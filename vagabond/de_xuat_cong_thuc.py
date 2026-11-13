# -*- coding: utf-8 -*-
"""Phiếu Đề xuất công thức: bếp gửi, Khải lên mã (v656, anh Việt 13/11/2026).

Vì sao có tệp này
-----------------
Khải nhắn 13/11: công thức bánh mới (ví dụ 73 Pinkpom bưởi) đi qua file Excel
"VGB recipe": Lab đưa nháp, Hân hoặc Linh ghi thành phần, Khải hỏi lại Linh cái
nào cấp 1, cấp 2 hay vào thẳng thành phẩm, rồi Khải tự tạo mã BTP và gõ tay công
thức lên ERP. Màn Danh mục công thức chỉ chọn được mã đã có, không có chỗ bếp
xác nhận cấp, không ghi gram theo size, không báo Khải.

Anh Việt duyệt ảnh 13/11 (hướng A, phương án A cả ba ý):
1. Một phiếu nhiều cột size. Bếp chọn cho từng thành phần nó VÀO ĐÂU: ruột bánh
   (cấp 1), khuôn bánh (cấp 2) hay thành phẩm (trang trí); Khải chỉ kiểm.
2. Khải bấm Tạo mã và công thức: máy tạo mã BTP mới, mã cấp 1, cấp 2 từng size,
   công thức nháp từng cấp; Khải xem lại rồi Ghi sổ.
3. Bốn ý thêm (tham khảo SAP, FlexiBake, meez, Apicbase): gõ tên mới thì báo mã
   gần giống; giá vốn dự kiến và % giá bán ngay trên phiếu, cho cả bếp, Lab, Khải,
   anh; nhập một size, máy gợi ý size khác theo diện tích khuôn; sửa công thức
   đang dùng cũng đi qua phiếu, có bảng trước và sau kèm chênh giá vốn.

Phần THUẦN đứng trước vạch, phần chạm hệ đứng sau.
"""

import json
import re
import unicodedata

# ------------------------------------------------------------ phần thuần

DT = "Vagabond De Xuat Cong Thuc"

LOAI_MOI = "Mới"
LOAI_DIEU_CHINH = "Điều chỉnh"

TT_NHAP = "Nháp"
TT_CHO = "Chờ Khải"
TT_TRA = "Trả lại bếp"
TT_DA_TAO = "Đã tạo nháp"
TT_XONG = "Đã ghi sổ"
TT_HUY = "Đã huỷ"
# Trạng thái người đề xuất còn sửa được phiếu.
TT_SUA_DUOC = (TT_NHAP, TT_TRA)

# Thành phần đi vào đâu. Đúng câu Khải phải hỏi lại bếp: "cấp 1, cấp 2, hay ra
# thẳng Thành phẩm".
CAP1, CAP2, THANH_PHAM = "cap1", "cap2", "thanh_pham"
DICH = (CAP1, CAP2, THANH_PHAM)
TEN_DICH = {
	CAP1: "Ruột bánh (cấp 1)",
	CAP2: "Khuôn bánh (cấp 2)",
	THANH_PHAM: "Thành phẩm, trang trí",
}

# Nhãn chặng trên công thức (ô custom_chang) và trên mã (custom_chang_btp), đúng
# chữ đang có trên site (ton_chang.NHAN_CU, kho_san_xuat.TEN_CHANG).
CHANG_BOM = {"thanh_phan": "BTP thành phần", CAP1: "Ruột bánh (C1)", CAP2: "Bánh khuôn (C2)", "tp": "Thành phẩm"}
CHANG_MA = {"thanh_phan": "BTP thành phần", CAP1: "BTP sơ cấp", CAP2: "BTP sẵn sàng"}

# Chữ đứng một mình không nói lên món nào, bỏ khi so tên.
CHU_BO = {"btp", "banh", "cua", "va", "voi", "size", "cm", "gr", "gram", "kg", "hu", "thung", "hop", "goi"}


def chuan_hoa(s):
	"""Thường hoá, bỏ dấu, đ thành d, bỏ ký tự lạ. THUẦN."""
	s = (s or "").replace("Đ", "d").replace("đ", "d").lower()
	s = unicodedata.normalize("NFD", s)
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	return re.sub(r"[^a-z0-9]+", " ", s).strip()


def tach_chu(s):
	"""Các chữ có nghĩa của một tên, đã bỏ dấu. Bỏ chữ chung chung và mã số. THUẦN."""
	ra = []
	for t in chuan_hoa(s).split():
		if len(t) < 2 or t in CHU_BO or t.isdigit():
			continue
		if re.fullmatch(r"[a-z]{3,4}\d{3,}", t):  # mã kiểu BTPB00215 nằm trong tên
			continue
		if t not in ra:
			ra.append(t)
	return ra


def diem_khop(chu_tim, ten):
	"""Số chữ của câu tìm có mặt trong tên. THUẦN."""
	co = set(tach_chu(ten))
	return sum(1 for t in chu_tim if t in co)


def xep_goi_y(ten, ung_vien, toi_da=8):
	"""Xếp mã gần giống theo số chữ trùng, nhiều chữ trùng đứng trước. THUẦN.

	ung_vien: [{"ma", "ten", ...}]. Bỏ mã không trùng chữ nào. Hoà điểm thì tên
	ngắn đứng trước (ít chữ thừa hơn), rồi theo mã cho ổn định."""
	chu = tach_chu(ten)
	if not chu:
		return []
	ra = []
	for u in ung_vien or ():
		d = diem_khop(chu, u.get("ten"))
		if d > 0:
			ra.append(dict(u, diem=d))
	ra.sort(key=lambda x: (-x["diem"], len(x.get("ten") or ""), x.get("ma") or ""))
	return ra[:toi_da]


def so_size(s):
	"""Đường kính (cm) đọc từ chữ size: "16", "16cm", "size 18 cm". Không phải
	bánh tròn đo bằng cm (Slice, khuôn vuông) thì None. THUẦN."""
	m = re.fullmatch(r"\s*(?:size\s*)?(\d{1,2}(?:[.,]\d)?)\s*(?:cm)?\s*", (s or "").lower())
	if not m:
		return None
	d = float(m.group(1).replace(",", "."))
	return d if d > 0 else None


def goi_y_size(gram, size_goc, size_dich):
	"""Gram gợi ý cho size_dich, nhân theo diện tích khuôn tròn so với size_goc.
	Không tính được (size không phải số, gram trống) thì None. THUẦN."""
	a, b = so_size(size_goc), so_size(size_dich)
	try:
		g = float(gram)
	except (TypeError, ValueError):
		return None
	if not a or not b or g <= 0:
		return None
	v = g * (b / a) ** 2
	return round(v) if v >= 10 else round(v, 3)


def goi_y_dong(dong, sizes, size_goc):
	"""Điền gợi ý cho các size còn trống của MỘT dòng, từ gram ở size_goc. Dòng
	trang trí (thành phẩm) không nhân theo diện tích: giữ nguyên số ở size_goc.
	Không ghi đè ô bếp đã nhập. Trả gram mới (dict). THUẦN."""
	gram = dict((dong or {}).get("gram") or {})
	goc = gram.get(size_goc)
	if goc in (None, "") or _so(goc) <= 0:
		return gram
	for s in sizes or ():
		if s == size_goc or _so(gram.get(s)) > 0:
			continue
		if not so_size(s):
			# Slice, khuôn vuông: không gợi ý gì, kể cả dòng trang trí (bếp tự ghi).
			continue
		if (dong or {}).get("dich") == THANH_PHAM:
			gram[s] = _so(goc)
			continue
		v = goi_y_size(goc, size_goc, s)
		if v is not None:
			gram[s] = v
	return gram


def goi_y_cac_size(dong, sizes):
	"""Nút Gợi ý các size còn trống: lấy size tròn ĐẦU TIÊN đã có gram làm gốc
	rồi điền các size còn trống (goi_y_dong). Một nguồn cho màn app. Trả
	{"goc": size gốc hoặc None, "gram": gram mới}. THUẦN."""
	gram = (dong or {}).get("gram") or {}
	goc = next((s for s in sizes or () if so_size(s) and _so(gram.get(s)) > 0), None)
	if not goc:
		return {"goc": None, "gram": dict(gram)}
	return {"goc": goc, "gram": goi_y_dong(dong, sizes, goc)}


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def doc_du_lieu(s):
	"""Đọc ô du_lieu (JSON) thành {"sizes": [...], "dong": [...]}. Hỏng thì rỗng. THUẦN."""
	if isinstance(s, dict):
		d = s
	else:
		try:
			d = json.loads(s or "{}")
		except (TypeError, ValueError):
			d = {}
	if not isinstance(d, dict):
		d = {}
	sizes = [str(x).strip() for x in (d.get("sizes") or []) if str(x).strip()]
	dong = [x for x in (d.get("dong") or []) if isinstance(x, dict)]
	return {"sizes": sizes, "dong": dong}


def kiem_phieu(loai, ten_banh, du_lieu, bom_goc=None):
	"""Các lỗi phải sửa trước khi Gửi Khải, câu nói việc cần làm. THUẦN."""
	d = doc_du_lieu(du_lieu)
	loi = []
	if loai == LOAI_DIEU_CHINH:
		if not bom_goc:
			loi.append("Phiếu điều chỉnh phải gắn với một công thức đang dùng.")
		if not d["dong"]:
			loi.append("Công thức phải còn ít nhất một dòng.")
		for i, x in enumerate(d["dong"], 1):
			if not x.get("ma"):
				loi.append("Dòng %d: chọn mã có sẵn. Thành phần mới thì lập phiếu Đề xuất công thức mới." % i)
			if _so((x.get("gram") or {}).get("")) <= 0:
				loi.append("Dòng %d (%s): chưa nhập số lượng." % (i, x.get("ten") or x.get("ma") or ""))
		return loi
	if not (ten_banh or "").strip():
		loi.append("Chưa ghi tên bánh.")
	if not d["sizes"]:
		loi.append("Chọn ít nhất một size.")
	if not d["dong"]:
		loi.append("Chưa có thành phần nào.")
	moi = {x.get("id") for x in d["dong"] if not x.get("ma")}
	for i, x in enumerate(d["dong"], 1):
		ten = (x.get("ten") or "").strip() or ("dòng %d" % i)
		if not x.get("ma") and not (x.get("ten") or "").strip():
			loi.append("Dòng %d: chọn mã có sẵn hoặc gõ tên thành phần mới." % i)
		if x.get("dich") not in DICH:
			loi.append("%s: chọn thành phần này vào ruột (cấp 1), khuôn (cấp 2) hay thành phẩm." % ten)
		if not x.get("ma"):
			con = x.get("con") or {}
			if _so(con.get("me")) <= 0:
				loi.append("%s là thành phần mới: ghi một mẻ ra được bao nhiêu gram." % ten)
			dc = [y for y in (con.get("dong") or []) if isinstance(y, dict)]
			if not dc:
				loi.append("%s là thành phần mới: ghi công thức con (nguyên liệu làm ra nó)." % ten)
			for y in dc:
				if not y.get("ma") and y.get("dong_id") not in moi:
					loi.append("%s: dòng con phải là mã có sẵn hoặc một thành phần mới trong phiếu." % ten)
				elif y.get("dong_id") == x.get("id"):
					loi.append("%s: công thức con không được dùng lại chính nó." % ten)
				if _so(y.get("sl")) <= 0:
					loi.append("%s: dòng con %s chưa có số lượng." % (ten, y.get("ten") or y.get("ma") or ""))
	if not loi and _co_vong(d["dong"]):
		loi.append("Các thành phần mới đang dùng lẫn nhau thành vòng, kiểm lại công thức con.")
	for s in d["sizes"]:
		if not any(_so((x.get("gram") or {}).get(s)) > 0 for x in d["dong"]):
			loi.append("Size %s chưa có thành phần nào có gram." % s)
	return loi


def _co_vong(dong):
	try:
		thu_tu_tao(dong)
		return False
	except ValueError:
		return True


def thu_tu_tao(dong):
	"""Thứ tự tạo thành phần mới: thành phần được dùng trong công thức con của
	thành phần khác phải tạo trước. Có vòng thì ValueError. THUẦN."""
	moi = {x.get("id"): x for x in dong or () if not x.get("ma")}
	ra, dang, xong = [], set(), set()

	def tham(i):
		if i in xong:
			return
		if i in dang:
			raise ValueError("vong")
		dang.add(i)
		for y in ((moi[i].get("con") or {}).get("dong") or []):
			j = isinstance(y, dict) and y.get("dong_id")
			if j and j in moi:
				tham(j)
		dang.discard(i)
		xong.add(i)
		ra.append(i)

	for i in moi:
		tham(i)
	return ra


def ke_hoach(du_lieu):
	"""Dựng kế hoạch máy sẽ tạo cho phiếu Mới. THUẦN.

	Trả {"moi": [id thành phần mới theo thứ tự tạo], "size": {s: {"cap1": [...],
	"cap2": [...], "tp": [...]}}}. Mỗi phần tử danh sách là ("dong", id, gram)
	cho thành phần, hoặc ("cap", "cap1"|"cap2", 1) cho một cái cấp dưới.
	Luật: size có dòng cấp 1 thì có mã cấp 1; có dòng cấp 2 thì có mã cấp 2, mã
	cấp 2 gồm một cái cấp 1 (nếu có). Thành phẩm gồm một cái cấp cao nhất đang
	có, cộng các dòng thành phẩm (trang trí). Không dòng nào vào cấp 1, cấp 2 thì
	thành phẩm gồm thẳng các thành phần, như Very Berry đang làm."""
	d = doc_du_lieu(du_lieu)
	ra = {"moi": thu_tu_tao(d["dong"]), "size": {}}
	for s in d["sizes"]:
		nhom = {CAP1: [], CAP2: [], THANH_PHAM: []}
		for x in d["dong"]:
			g = _so((x.get("gram") or {}).get(s))
			if g > 0 and x.get("dich") in nhom:
				nhom[x["dich"]].append(("dong", x.get("id"), g))
		c1, c2 = list(nhom[CAP1]), list(nhom[CAP2])
		if c2 and c1:
			c2 = [("cap", CAP1, 1)] + c2
		tp = list(nhom[THANH_PHAM])
		if c2:
			tp = [("cap", CAP2, 1)] + tp
		elif c1:
			tp = [("cap", CAP1, 1)] + tp
		ra["size"][s] = {CAP1: c1, CAP2: c2, "tp": tp}
	return ra


def don_gia_dong(x, gia, don_gia_moi):
	"""Đơn giá một đơn vị của một dòng: mã có sẵn lấy từ bảng giá (gia[ma]),
	thành phần mới lấy từ công thức con đã tính (don_gia_moi[id]). THUẦN."""
	if x.get("ma"):
		return _so((gia or {}).get(x["ma"]))
	return _so((don_gia_moi or {}).get(x.get("id")))


def gia_von(du_lieu, gia):
	"""Giá vốn dự kiến từng size và các thành phần chưa có giá. THUẦN.

	gia: {mã: đơn giá theo đơn vị của dòng}. Thành phần mới: đơn giá = tổng
	(số lượng dòng con x đơn giá) / mẻ ra. Trả {"size": {s: tiền}, "thieu":
	[tên], "don_gia_moi": {id: đơn giá}}."""
	d = doc_du_lieu(du_lieu)
	by_id = {x.get("id"): x for x in d["dong"]}
	thieu, dg = [], {}
	try:
		thu_tu = thu_tu_tao(d["dong"])
	except ValueError:
		thu_tu = []
	for i in thu_tu:
		x = by_id[i]
		con = x.get("con") or {}
		tong = 0.0
		for y in (con.get("dong") or []):
			if not isinstance(y, dict):
				continue
			if y.get("ma"):
				p = _so((gia or {}).get(y["ma"]))
				if p <= 0:
					_them(thieu, y.get("ten") or y["ma"])
			else:
				p = _so(dg.get(y.get("dong_id")))
			tong += _so(y.get("sl")) * p
		me = _so(con.get("me"))
		dg[i] = tong / me if me > 0 else 0.0
	ra = {}
	for s in d["sizes"]:
		t = 0.0
		for x in d["dong"]:
			g = _so((x.get("gram") or {}).get(s))
			if g <= 0:
				continue
			p = don_gia_dong(x, gia, dg)
			if p <= 0 and x.get("ma"):
				_them(thieu, x.get("ten") or x.get("ma"))
			t += g * p
		ra[s] = round(t)
	return {"size": ra, "thieu": thieu, "don_gia_moi": dg}


def thieu_gia_dong(dong, gia):
	"""Tên các dòng có số lượng mà chưa có đơn giá (giá vốn đang thiếu phần
	này). Dùng cho phiếu điều chỉnh. dong: [{"ma","ten","sl"}]. THUẦN."""
	ra = []
	for r in dong or ():
		if _so(r.get("sl")) > 0 and _so((gia or {}).get(r.get("ma"))) <= 0:
			_them(ra, r.get("ten") or r.get("ma"))
	return ra


def _them(ds, x):
	if x and x not in ds:
		ds.append(x)


def ty_le(von, ban):
	"""Giá vốn chiếm bao nhiêu phần trăm giá bán, làm tròn. Không có giá bán thì None. THUẦN."""
	b = _so(ban)
	if b <= 0:
		return None
	return round(_so(von) * 100.0 / b)


def doi_chieu(cu, moi):
	"""Bảng trước và sau của một phiếu điều chỉnh. THUẦN.

	cu, moi: [{"ma", "ten", "sl"}]. Trả các dòng {"ma", "ten", "cu", "moi",
	"kieu": them | bot | doi | giu}, theo thứ tự công thức mới rồi dòng bị bỏ."""
	a = {x.get("ma"): x for x in cu or ()}
	b = {x.get("ma"): x for x in moi or ()}
	ra = []
	for x in moi or ():
		m = x.get("ma")
		if m in a:
			c, n = _so(a[m].get("sl")), _so(x.get("sl"))
			kieu = "giu" if abs(c - n) < 1e-9 else "doi"
			ra.append({"ma": m, "ten": x.get("ten") or a[m].get("ten"), "cu": c, "moi": n, "kieu": kieu})
		else:
			ra.append({"ma": m, "ten": x.get("ten"), "cu": None, "moi": _so(x.get("sl")), "kieu": "them"})
	for x in cu or ():
		if x.get("ma") not in b:
			ra.append({"ma": x.get("ma"), "ten": x.get("ten"), "cu": _so(x.get("sl")), "moi": None, "kieu": "bot"})
	return ra


def co_thay_doi(bang):
	"""Phiếu điều chỉnh có đổi gì không. THUẦN."""
	return any(r["kieu"] != "giu" for r in bang or ())


def ten_cap(cap, ten_banh, size):
	"""Tên mã cấp 1, cấp 2 theo nếp đang có trên site ("BTP Cấp 2 Bánh Ổ Very
	Berry size 16cm"). Trả (tên mặt hàng, quy cách). THUẦN."""
	so = "1" if cap == CAP1 else "2"
	qc = ""
	if size:
		d = so_size(size)
		qc = ("size %scm" % (int(d) if d == int(d) else d)) if d else str(size)
	return ("BTP Cấp %s %s" % (so, (ten_banh or "").strip())).strip(), qc


def ma_tiep(tien_to, ma_lon_nhat):
	"""Mã kế tiếp theo nếp Client Script "Item - Tự ghép tên & sinh mã": tiền tố
	cộng 5 chữ số. THUẦN."""
	n = 0
	if ma_lon_nhat and ma_lon_nhat.startswith(tien_to):
		try:
			n = int(ma_lon_nhat[len(tien_to):])
		except ValueError:
			n = 0
	return "%s%05d" % (tien_to, n + 1)


def ghep_ten(*phan):
	"""Ghép tên mặt hàng như Client Script trên Desk (bỏ phần trống, nối dấu phẩy). THUẦN."""
	return ", ".join(p.strip() for p in phan if p and str(p).strip())


def co_dong(quan_ton, bom_con):
	"""Cờ nổ cho một dòng công thức, đúng hợp đồng phantom của xưởng
	(patches/no_phantom_chuan.py, phantom.py). THUẦN.

	- Mã KHÔNG quản tồn có công thức (BTP thành phần): dòng phantom, trỏ
	  bom_no vào công thức con, không chặn nổ. Lệnh nổ một cấp vẫn trừ
	  nguyên liệu bên trong.
	- Mã quản tồn có công thức (ruột cấp 1, bánh khuôn cấp 2): chặn nổ, bỏ
	  bom_no, lệnh đòi đúng mã giữ tồn.
	- Nguyên liệu mua vào (không công thức): để mặc định.
	quan_ton: mã có quản tồn; bom_con: công thức đang dùng của mã (hoặc rỗng)."""
	if not quan_ton:
		if bom_con:
			return {"is_phantom_item": 1, "bom_no": bom_con, "do_not_explode": 0}
		return {}
	if bom_con:
		return {"is_phantom_item": 0, "bom_no": "", "do_not_explode": 1}
	return {}


def ma_viec(trang_thai, la_duyet, la_nguoi_lap):
	"""Phiếu này có phải việc của người xem không. THUẦN.

	Khải (vai ghi sổ công thức): phiếu Chờ Khải và Đã tạo nháp. Người đề xuất:
	phiếu của mình bị Trả lại bếp."""
	if la_duyet and trang_thai in (TT_CHO, TT_DA_TAO):
		return True
	return bool(la_nguoi_lap and trang_thai == TT_TRA)


# ------------------------------------------------------------ phần chạm hệ

import frappe  # noqa: E402
from frappe.utils import cint, flt  # noqa: E402

NHOM_THANH_PHAN = "Bán thành phẩm Bánh"
NHOM_CAP = "Nhân bán thành phẩm"
# Tiền tố mã khi nhóm hàng chưa khai ô Mã master (bench kiểm thử, site mới).
TIEN_TO_MAC_DINH = {NHOM_THANH_PHAN: "BTPB", NHOM_CAP: "NBTP"}


def _ct():
	from vagabond import cong_thuc
	return cong_thuc


def _vai():
	return set(frappe.get_roles(frappe.session.user))


def _la_lap():
	return bool(_ct()._vai_xem() & _vai())


def _la_duyet():
	return bool(_ct()._vai_ghi_so() & _vai())


def _kiem_lap():
	if not _la_lap():
		frappe.throw("Phiếu đề xuất công thức dành cho bếp, Lab, quầy bar và quản lý sản xuất.", frappe.PermissionError)


def _kiem_duyet():
	if not _la_duyet():
		frappe.throw("Chỉ Khải (quản lý công thức), bếp trưởng hoặc giám đốc làm bước này.", frappe.PermissionError)


def _doc_khoa(name):
	"""Đọc phiếu SAU khi khoá dòng, để hai người bấm cùng lúc không cùng đi qua."""
	if not frappe.db.sql("select name from `tab%s` where name=%%s for update" % DT, (name,)):
		frappe.throw("Không thấy phiếu %s." % name)
	return frappe.get_doc(DT, name)


def _luu_doc(doc):
	doc.flags.vgb_de_xuat_ct = True
	doc.save(ignore_permissions=True)


def _gia_ban(ma):
	if not ma:
		return 0.0
	return flt(frappe.db.get_value("Item Price", {"item_code": ma, "selling": 1, "price_list": "Standard Selling"}, "price_list_rate"))


def _he_so(ma, dvt, dvt_kho):
	"""Một đơn vị dvt bằng bao nhiêu đơn vị kho của mã (UOM Conversion Detail)."""
	if not dvt or dvt == dvt_kho:
		return 1.0
	cf = frappe.db.get_value("UOM Conversion Detail", {"parent": ma, "uom": dvt}, "conversion_factor")
	return flt(cf) or 1.0


def don_gia_ma(ma, dvt=None):
	"""Đơn giá một đơn vị dvt của mã: có công thức đang dùng thì lấy giá công
	thức (tổng chi phí / mẻ, cùng cách ERPNext tính), không thì giá vốn tồn kho,
	không nữa thì giá mua gần nhất. Không có gì thì 0 (báo thiếu giá)."""
	it = frappe.db.get_value("Item", ma, ["stock_uom", "valuation_rate", "last_purchase_rate"], as_dict=True)
	if not it:
		return 0.0
	p = 0.0
	b = frappe.db.get_value("BOM", {"item": ma, "is_default": 1, "docstatus": 1}, ["total_cost", "quantity", "uom"], as_dict=True)
	if b and flt(b.quantity) > 0 and flt(b.total_cost) > 0:
		p = flt(b.total_cost) / flt(b.quantity) / _he_so(ma, b.uom, it.stock_uom)
	if p <= 0:
		p = flt(it.valuation_rate) or flt(it.last_purchase_rate)
	return p * _he_so(ma, dvt, it.stock_uom)


def _bang_gia(du_lieu):
	d = doc_du_lieu(du_lieu)
	ra = {}
	for x in d["dong"]:
		if x.get("ma"):
			ra.setdefault(x["ma"], don_gia_ma(x["ma"], x.get("dvt")))
		for y in ((x.get("con") or {}).get("dong") or []):
			if isinstance(y, dict) and y.get("ma"):
				ra.setdefault(y["ma"], don_gia_ma(y["ma"], y.get("dvt")))
	return ra


def _cho_man(doc):
	d = doc_du_lieu(doc.du_lieu)
	gv = gia_von(d, _bang_gia(d))
	ma_tp = _doc_json(doc.ma_thanh_pham)
	gia = {}
	for s in d["sizes"]:
		ban = _gia_ban(ma_tp.get(s))
		gia[s] = {"von": gv["size"].get(s, 0), "ban": ban, "ty_le": ty_le(gv["size"].get(s, 0), ban),
			"ma_tp": ma_tp.get(s) or "", "ten_tp": frappe.db.get_value("Item", ma_tp.get(s), "item_name") if ma_tp.get(s) else ""}
	ra = {
		"name": doc.name, "loai": doc.loai, "ten_banh": doc.ten_banh or "", "trang_thai": doc.trang_thai,
		"du_lieu": d, "bom_goc": doc.bom_goc or "", "ly_do": doc.ly_do or "", "ghi_chu_khai": doc.ghi_chu_khai or "",
		"nguoi_de_xuat": doc.nguoi_de_xuat or "", "ten_nguoi_de_xuat": _ten(doc.nguoi_de_xuat),
		"ket_qua": _doc_json(doc.ket_qua), "gia": gia, "thieu_gia": gv["thieu"],
		"quyen": {"sua": 1 if _sua_duoc(doc) else 0, "duyet": 1 if _la_duyet() else 0},
	}
	if doc.loai == LOAI_DIEU_CHINH and doc.bom_goc:
		ra["doi_chieu"] = _doi_chieu_dc(doc, d)
		# Phiếu điều chỉnh không có size: dòng thiếu giá lấy theo bảng trước sau.
		ra["thieu_gia"] = ra["doi_chieu"]["thieu"]
	return ra


def _doi_chieu_dc(doc, d):
	b = frappe.get_doc("BOM", doc.bom_goc)
	cu = [{"ma": i.item_code, "ten": i.item_name, "sl": i.qty} for i in b.items]
	moi = [{"ma": x.get("ma"), "ten": x.get("ten"), "sl": _so((x.get("gram") or {}).get(""))} for x in d["dong"]]
	gia = _bang_gia(d)
	von_moi = sum(_so(r["sl"]) * _so(gia.get(r["ma"])) for r in moi)
	q = flt(b.quantity) or 1
	return {"bang": doi_chieu(cu, moi), "von_cu": round(flt(b.total_cost)), "von_moi": round(von_moi),
		"thieu": thieu_gia_dong(moi, gia),
		"me": q, "dvt": b.uom, "ma": b.item, "ten": frappe.db.get_value("Item", b.item, "item_name") or b.item,
		"gia_ban": _gia_ban(b.item)}


def _ten(user):
	if not user:
		return ""
	return frappe.db.get_value("User", user, "full_name") or user


def _doc_json(s):
	try:
		v = json.loads(s or "{}")
	except (TypeError, ValueError):
		v = {}
	return v if isinstance(v, dict) else {}


def _sua_duoc(doc):
	if doc.trang_thai in TT_SUA_DUOC and (doc.nguoi_de_xuat == frappe.session.user or _la_duyet()):
		return True
	return doc.trang_thai == TT_CHO and _la_duyet()


MOI_TRANG = 50


@frappe.whitelist()
def danh_sach(trang_thai=None, tim=None, trang=0):
	"""Các phiếu đề xuất, mới nhất trước, MOI_TRANG phiếu một trang. Người lập
	thấy phiếu của mình; Khải thấy hết. tim: mã phiếu hoặc tên bánh (lọc ở
	máy chủ, nên phiếu cũ ngoài trang đầu vẫn tìm ra). Trả {ds, dem, con_nua}."""
	_kiem_lap()
	f = {}
	if not _la_duyet():
		f["nguoi_de_xuat"] = frappe.session.user
	hoac = None
	tim = (tim or "").strip()
	if tim:
		# v583: tìm theo từng chữ, bỏ dấu (tim_kiem.py), một điều kiện "name in".
		from vagabond import tim_kiem

		hoac = [tim_kiem.loc_ten(DT, tim, ["name", "ten_banh"])]
	dem = {}
	# Đếm từng trạng thái cho hàng chip (đọc đủ, không giới hạn dòng).
	for t in frappe.get_all(DT, filters=f, or_filters=hoac, pluck="trang_thai", limit_page_length=0):
		dem[t] = dem.get(t, 0) + 1
	dem["tat_ca"] = sum(dem.values())
	if trang_thai:
		f["trang_thai"] = trang_thai
	trang = max(0, cint(trang))
	ra = frappe.get_all(DT, filters=f, or_filters=hoac, fields=["name", "loai", "ten_banh", "trang_thai", "nguoi_de_xuat", "modified"],
		order_by="modified desc", start=trang * MOI_TRANG, page_length=MOI_TRANG + 1)
	con_nua = len(ra) > MOI_TRANG
	ra = ra[:MOI_TRANG]
	for r in ra:
		r["ten_nguoi_de_xuat"] = _ten(r.nguoi_de_xuat)
		r["modified"] = str(r.modified)[:16]
	return {"ds": ra, "dem": dem, "con_nua": 1 if con_nua else 0, "trang": trang}


@frappe.whitelist()
def chi_tiet(name):
	_kiem_lap()
	doc = frappe.get_doc(DT, name)
	if not _la_duyet() and doc.nguoi_de_xuat != frappe.session.user:
		frappe.throw("Phiếu này của người khác.", frappe.PermissionError)
	return _cho_man(doc)


@frappe.whitelist()
def luu(name=None, ten_banh=None, du_lieu=None, loai=None, bom_goc=None, ly_do=None, ma_thanh_pham=None):
	"""Lưu nháp (tạo mới nếu chưa có). Bếp sửa được lúc Nháp và Trả lại bếp; Khải
	sửa được cả lúc Chờ Khải."""
	_kiem_lap()
	d = doc_du_lieu(du_lieu)
	if name:
		doc = _doc_khoa(name)
		if not _sua_duoc(doc):
			frappe.throw("Phiếu %s đang %s, không sửa được nữa." % (doc.name, doc.trang_thai.lower()))
	else:
		doc = frappe.new_doc(DT)
		doc.loai = LOAI_DIEU_CHINH if loai == LOAI_DIEU_CHINH else LOAI_MOI
		doc.trang_thai = TT_NHAP
		doc.nguoi_de_xuat = frappe.session.user
		if doc.loai == LOAI_DIEU_CHINH:
			if not bom_goc or cint(frappe.db.get_value("BOM", bom_goc, "docstatus")) != 1:
				frappe.throw("Chỉ đề xuất điều chỉnh được công thức đã ghi sổ.")
			doc.bom_goc = bom_goc
			ten_banh = ten_banh or frappe.db.get_value("Item", frappe.db.get_value("BOM", bom_goc, "item"), "item_name")
	if ten_banh is not None:
		doc.ten_banh = (ten_banh or "").strip()[:140]
	if ly_do is not None:
		doc.ly_do = ly_do
	doc.du_lieu = json.dumps(d, ensure_ascii=False)
	if ma_thanh_pham is not None:
		mtp = _doc_json(ma_thanh_pham) if isinstance(ma_thanh_pham, str) else (ma_thanh_pham or {})
		doc.ma_thanh_pham = json.dumps({k: v for k, v in mtp.items() if v}, ensure_ascii=False)
	if doc.is_new():
		doc.flags.vgb_de_xuat_ct = True
		doc.insert(ignore_permissions=True)
	else:
		_luu_doc(doc)
	return _cho_man(doc)


@frappe.whitelist()
def tu_cong_thuc(bom):
	"""Dòng sẵn cho phiếu điều chỉnh, chép từ công thức đang dùng."""
	_kiem_lap()
	b = frappe.get_doc("BOM", bom)
	dong = [{"id": "d%d" % i, "ma": r.item_code, "ten": r.item_name, "dvt": r.uom, "gram": {"": flt(r.qty)}}
		for i, r in enumerate(b.items, 1)]
	return {"ten_banh": frappe.db.get_value("Item", b.item, "item_name") or b.item,
		"du_lieu": {"sizes": [], "dong": dong}, "me": flt(b.quantity), "dvt": b.uom}


@frappe.whitelist()
def gui(name):
	"""Bếp gửi phiếu cho Khải. Kiểm đủ thông tin trước, báo Zalo cho Khải."""
	_kiem_lap()
	doc = _doc_khoa(name)
	if doc.trang_thai not in TT_SUA_DUOC:
		frappe.throw("Phiếu %s đang %s, không gửi lại được." % (doc.name, doc.trang_thai.lower()))
	if doc.nguoi_de_xuat != frappe.session.user and not _la_duyet():
		frappe.throw("Phiếu này của người khác.", frappe.PermissionError)
	loi = kiem_phieu(doc.loai, doc.ten_banh, doc.du_lieu, doc.bom_goc)
	if loi:
		frappe.throw("Phiếu còn thiếu:<br>" + "<br>".join(loi[:8]))
	doc.trang_thai = TT_CHO
	_luu_doc(doc)
	_bao_khai(doc)
	return _cho_man(doc)


def _url(duong):
	from vagabond import viec_tu_dong as vtd
	return vtd._url(duong)


def _bao_khai(doc):
	from vagabond import kenh_zalo
	d = doc_du_lieu(doc.du_lieu)
	so_moi = sum(1 for x in d["dong"] if not x.get("ma"))
	dong = ["%s: %s" % (doc.loai, doc.ten_banh), "Người đề xuất: %s" % _ten(doc.nguoi_de_xuat)]
	if doc.loai == LOAI_MOI:
		dong.append("Size: %s · %d thành phần, %d thành phần mới" % (", ".join(d["sizes"]), len(d["dong"]), so_moi))
	elif doc.ly_do:
		dong.append("Lý do: %s" % doc.ly_do)
	kenh_zalo.bao_hoac_ghi_loi("viec", "san_xuat", "Phiếu đề xuất công thức chờ lên mã", dong,
		link=_url("/cong-thuc"), khoa="dxct_cho:%s:%s" % (doc.name, doc.modified), nguon=doc.name, ma_tin="kt_cong_thuc_cho")


@frappe.whitelist()
def tra_lai(name, ghi_chu=None):
	"""Khải trả phiếu về bếp kèm câu hỏi, thay cho nhắn Zalo riêng."""
	_kiem_duyet()
	doc = _doc_khoa(name)
	if doc.trang_thai != TT_CHO:
		frappe.throw("Chỉ trả lại được phiếu đang Chờ Khải.")
	if not (ghi_chu or "").strip():
		frappe.throw("Ghi rõ cần bếp sửa hay trả lời gì.")
	doc.trang_thai = TT_TRA
	doc.ghi_chu_khai = (ghi_chu or "").strip()
	_luu_doc(doc)
	from vagabond import kenh_zalo
	kenh_zalo.bao_hoac_ghi_loi("viec", "san_xuat", "Khải hỏi lại phiếu công thức %s" % doc.ten_banh,
		[doc.ghi_chu_khai, "Người đề xuất: %s" % _ten(doc.nguoi_de_xuat)], link=_url("/cong-thuc"),
		khoa="dxct_tra:%s:%s" % (doc.name, doc.modified), nguon=doc.name, ma_tin="bep_cong_thuc_tra_lai")
	return _cho_man(doc)


@frappe.whitelist()
def huy(name):
	_kiem_lap()
	doc = _doc_khoa(name)
	if doc.trang_thai not in (TT_NHAP, TT_TRA, TT_CHO):
		frappe.throw("Phiếu đã tạo công thức thì không huỷ được; bỏ các bản nháp công thức trên màn Danh mục công thức.")
	if doc.nguoi_de_xuat != frappe.session.user and not _la_duyet():
		frappe.throw("Phiếu này của người khác.", frappe.PermissionError)
	doc.trang_thai = TT_HUY
	_luu_doc(doc)
	return _cho_man(doc)


@frappe.whitelist()
def goi_y_ma(ten):
	"""Mã có sẵn gần giống một tên thành phần: tìm theo TỪNG chữ (không cần đúng
	thứ tự), bỏ dấu, rồi xếp theo số chữ trùng."""
	_kiem_lap()
	chu = tach_chu(ten)
	if not chu:
		return []
	# Ứng viên: khớp BẤT KỲ chữ nào (gần giống, không cần đủ chữ); mẫu like lấy
	# của tim_kiem.cac_mau để "duong" vẫn ra "Đường" (CSDL coi d, đ khác nhau).
	from vagabond import tim_kiem

	tham, hoac = {}, []
	for i, t in enumerate(chu):
		for j, m in enumerate(tim_kiem.cac_mau(t)):
			k = "gy%d_%d" % (i, j)
			tham[k] = m
			hoac.append("item_name like %%(%s)s or name like %%(%s)s" % (k, k))
	rows = frappe.db.sql(
		"select name, item_name, stock_uom from `tabItem` where disabled=0 and (%s) order by modified desc limit 400" % " or ".join(hoac),
		tham, as_dict=True)
	# CSDL so có dấu theo bảng mã của nó; xếp lại bằng tên đã bỏ dấu cho chắc.
	uv = [{"ma": r.name, "ten": r.item_name, "dvt": r.stock_uom} for r in rows]
	return xep_goi_y(ten, uv)


@frappe.whitelist()
def goi_y_size_dong(dong, sizes):
	"""Gram gợi ý cho các size còn trống của một dòng (theo diện tích khuôn)."""
	_kiem_lap()
	if isinstance(dong, str):
		dong = json.loads(dong or "{}")
	if isinstance(sizes, str):
		sizes = json.loads(sizes or "[]")
	return goi_y_cac_size(dong if isinstance(dong, dict) else {}, [str(x) for x in sizes or ()])


@frappe.whitelist()
def gia_ma(ma, dvt=None):
	"""Đơn giá một mã để phiếu tính giá vốn dự kiến ngay lúc chọn."""
	_kiem_lap()
	return {"ma": ma, "don_gia": don_gia_ma(ma, dvt), "dvt_kho": frappe.db.get_value("Item", ma, "stock_uom")}


# --------------------------------------------- Khải tạo mã và công thức nháp

def _tao_ma(nhom, ten_mat_hang, quy_cach, dvt, ton_kho, chang_ma):
	tien_to = ""
	if frappe.get_meta("Item Group").has_field("custom_ma_master"):
		tien_to = (frappe.db.get_value("Item Group", nhom, "custom_ma_master") or "").strip().upper()
	tien_to = tien_to or TIEN_TO_MAC_DINH.get(nhom, "")
	if not frappe.db.exists("Item Group", nhom):
		frappe.throw("Chưa có nhóm hàng %s trên hệ. Tạo nhóm này trên Desk rồi bấm lại." % nhom)
	if not tien_to:
		frappe.throw("Nhóm %s chưa khai tiền tố mã (Mã master). Khai trên Desk rồi bấm lại." % nhom)
	if not frappe.db.sql("select get_lock(%s, 20)", ("vgb_ma_" + tien_to,))[0][0]:
		frappe.throw("Đang có người tạo mã cùng nhóm, bấm lại sau ít giây.")
	try:
		lon = frappe.db.sql("select max(name) from `tabItem` where name like %s", (tien_to + "%",))[0][0]
		ma = ma_tiep(tien_to, lon)
		it = frappe.new_doc("Item")
		it.item_code = ma
		it.item_name = ghep_ten(ten_mat_hang, quy_cach)[:140]
		it.item_group = nhom
		it.stock_uom = dvt
		it.is_stock_item = 1 if ton_kho else 0
		it.include_item_in_manufacturing = 1
		meta = frappe.get_meta("Item")
		for f, v in (("custom_ten_mat_hang", ten_mat_hang), ("custom_quy_cach", quy_cach),
				("custom_loai_hang", "Bán thành phẩm"), ("custom_chang_btp", chang_ma)):
			if v and meta.has_field(f):
				it.set(f, v)
		it.insert(ignore_permissions=True)
		return it.name
	finally:
		frappe.db.sql("select release_lock(%s)", ("vgb_ma_" + tien_to,))


def _tao_bom(ma, so_luong, dvt, dong, chang):
	"""Công thức NHÁP cho một mã. Mã đã có bản đang dùng thì bản nháp trỏ ngược
	về nó (custom_ban_truoc) để lúc ghi sổ bản cũ tự lui về, như nút Điều chỉnh."""
	nhap = frappe.get_all("BOM", filters={"item": ma, "docstatus": 0}, pluck="name", limit_page_length=1)
	if nhap:
		frappe.throw("Mã %s đang có bản nháp công thức %s. Bỏ hoặc ghi sổ bản đó trên màn Danh mục công thức rồi bấm lại." % (ma, nhap[0]))
	cu = frappe.db.get_value("BOM", {"item": ma, "is_default": 1, "docstatus": 1}, "name")
	b = frappe.new_doc("BOM")
	b.item = ma
	b.company = frappe.db.get_single_value("Global Defaults", "default_company")
	b.quantity = flt(so_luong) or 1
	b.uom = dvt or frappe.db.get_value("Item", ma, "stock_uom")
	b.currency = frappe.get_cached_value("Company", b.company, "default_currency") or "VND"
	b.rm_cost_as_per = "Valuation Rate"
	b.with_operations = 0
	if cu and b.meta.has_field("custom_ban_truoc"):
		b.custom_ban_truoc = cu
	if chang and b.meta.has_field("custom_chang"):
		b.custom_chang = chang
	if not cint(frappe.db.get_value("Item", ma, "is_stock_item")) and b.meta.has_field("is_phantom_bom"):
		# BTP thành phần không quản tồn: công thức phantom (no_phantom_chuan.py).
		b.is_phantom_bom = 1
	for m, sl, u in dong:
		r = {"item_code": m, "qty": flt(sl), "uom": u or None}
		r.update(_co_dong_ma(m))
		b.append("items", r)
	b.insert(ignore_permissions=True)
	return b.name


def _co_dong_ma(ma):
	"""Cờ nổ cho dòng mã này, đọc mã và công thức đang dùng của nó (co_dong)."""
	bom = frappe.db.get_value("BOM", {"item": ma, "is_default": 1, "is_active": 1, "docstatus": 1}, "name") or ""
	return co_dong(cint(frappe.db.get_value("Item", ma, "is_stock_item")), bom)


def _dat_co_dong(ten_bom):
	"""Trước khi ghi sổ một bản nháp của phiếu: công thức con vừa ghi sổ xong
	(thành phần mới) giờ mới có để trỏ bom_no, nên đặt lại cờ nổ từng dòng.
	ERPNext không cho bản nháp trỏ vào công thức con chưa ghi sổ."""
	b = frappe.get_doc("BOM", ten_bom)
	doi = False
	for r in b.items:
		for k, v in _co_dong_ma(r.item_code).items():
			if r.meta.has_field(k) and (r.get(k) or (0 if k != "bom_no" else "")) != v:
				r.set(k, v)
				doi = True
	if doi:
		b.save(ignore_permissions=True)


@frappe.whitelist()
def tao_nhap(name, ma_thanh_pham=None):
	"""Khải bấm Tạo mã và công thức: máy tạo mã thành phần mới, mã cấp 1, cấp 2
	từng size, rồi công thức NHÁP cho từng cấp và thành phẩm từng size. Chưa ghi
	sổ: Khải xem lại rồi bấm Ghi sổ."""
	_kiem_duyet()
	doc = _doc_khoa(name)
	if doc.loai != LOAI_MOI:
		frappe.throw("Phiếu điều chỉnh thì bấm Duyệt, không tạo mã.")
	if doc.trang_thai != TT_CHO:
		frappe.throw("Phiếu %s đang %s, không tạo lại được." % (doc.name, doc.trang_thai.lower()))
	if ma_thanh_pham is not None:
		mtp = _doc_json(ma_thanh_pham) if isinstance(ma_thanh_pham, str) else (ma_thanh_pham or {})
		doc.ma_thanh_pham = json.dumps({k: v for k, v in mtp.items() if v}, ensure_ascii=False)
	d = doc_du_lieu(doc.du_lieu)
	loi = kiem_phieu(doc.loai, doc.ten_banh, d)
	mtp = _doc_json(doc.ma_thanh_pham)
	for s in d["sizes"]:
		if not mtp.get(s) or not frappe.db.exists("Item", mtp.get(s)):
			loi.append("Size %s: chọn mã thành phẩm (mã bán ra) cho size này." % s)
	if loi:
		frappe.throw("Chưa tạo được:<br>" + "<br>".join(loi[:8]))
	kh = ke_hoach(d)
	by_id = {x.get("id"): x for x in d["dong"]}
	kq = {"ma_moi": {}, "bom": [], "cap": {}}
	# 1. Thành phần mới (theo thứ tự: cái được dùng trong công thức con tạo trước).
	for i in kh["moi"]:
		x = by_id[i]
		ma = _tao_ma(NHOM_THANH_PHAN, "BTP " + (x.get("ten") or "").strip(), "", "Gram", False, CHANG_MA["thanh_phan"])
		kq["ma_moi"][i] = ma
		con = x.get("con") or {}
		dong = []
		for y in con.get("dong") or []:
			m = y.get("ma") or kq["ma_moi"].get(y.get("dong_id"))
			dong.append((m, _so(y.get("sl")), y.get("dvt") or (None if y.get("ma") else "Gram")))
		kq["bom"].append({"bom": _tao_bom(ma, _so(con.get("me")), "Gram", dong, CHANG_BOM["thanh_phan"]), "ma": ma, "bac": 0})

	def ma_dong(i):
		x = by_id[i]
		return x.get("ma") or kq["ma_moi"][i], x.get("dvt") if x.get("ma") else "Gram"

	# 2. Cấp 1, cấp 2 từng size, rồi thành phẩm.
	for s, n in kh["size"].items():
		kq["cap"][s] = {}
		for cap, bac in ((CAP1, 1), (CAP2, 2)):
			if not n[cap]:
				continue
			ten, qc = ten_cap(cap, doc.ten_banh, s)
			ma = _tao_ma(NHOM_CAP, ten, qc, "Cái", True, CHANG_MA[cap])
			kq["cap"][s][cap] = ma
			dong = []
			for k in n[cap]:
				if k[0] == "cap":
					dong.append((kq["cap"][s][k[1]], 1, "Cái"))
				else:
					m, u = ma_dong(k[1])
					dong.append((m, k[2], u))
			kq["bom"].append({"bom": _tao_bom(ma, 1, "Cái", dong, CHANG_BOM[cap]), "ma": ma, "bac": bac})
		dong = []
		for k in n["tp"]:
			if k[0] == "cap":
				dong.append((kq["cap"][s][k[1]], 1, "Cái"))
			else:
				m, u = ma_dong(k[1])
				dong.append((m, k[2], u))
		tp = mtp[s]
		kq["bom"].append({"bom": _tao_bom(tp, 1, frappe.db.get_value("Item", tp, "stock_uom"), dong, CHANG_BOM["tp"]), "ma": tp, "bac": 3})
	doc.ket_qua = json.dumps(kq, ensure_ascii=False)
	doc.trang_thai = TT_DA_TAO
	doc.nguoi_duyet = frappe.session.user
	_luu_doc(doc)
	return _cho_man(doc)


@frappe.whitelist()
def ghi_so_tat_ca(name):
	"""Ghi sổ mọi bản nháp phiếu đã tạo, từ dưới lên (thành phần, cấp 1, cấp 2,
	thành phẩm) để giá vốn cấp trên tính từ cấp dưới đã chốt. Bấm lại sau một
	lần hỏng thì bỏ qua bản đã ghi sổ, chỉ ghi tiếp phần còn lại."""
	_kiem_duyet()
	doc = _doc_khoa(name)
	if doc.trang_thai != TT_DA_TAO:
		frappe.throw("Phiếu %s đang %s." % (doc.name, doc.trang_thai.lower()))
	kq = _doc_json(doc.ket_qua)
	ct = _ct()
	for b in sorted(kq.get("bom") or [], key=lambda x: cint(x.get("bac"))):
		# ghi_so của cong_thuc tự commit, nhả khoá phiếu: khoá từng bản công
		# thức rồi mới đọc trạng thái, để lượt bấm thứ hai chờ rồi bỏ qua bản đã ghi.
		ds = cint((frappe.db.sql("select docstatus from `tabBOM` where name=%s for update", b["bom"]) or [[2]])[0][0])
		if ds == 1:
			continue
		if ds != 0:
			frappe.throw("Bản %s không còn là nháp (đã bỏ hoặc huỷ). Tạo lại phiếu mới." % b["bom"])
		_dat_co_dong(b["bom"])
		ct.ghi_so(b["bom"])
		frappe.get_doc("BOM", b["bom"]).add_comment("Comment", "Từ phiếu đề xuất %s của %s, %s duyệt." % (
			doc.name, _ten(doc.nguoi_de_xuat), _ten(frappe.session.user)))
	doc = _doc_khoa(name)
	doc.trang_thai = TT_XONG
	_luu_doc(doc)
	frappe.db.commit()
	return _cho_man(doc)


@frappe.whitelist()
def duyet_dieu_chinh(name):
	"""Khải duyệt phiếu điều chỉnh: ra phiên bản mới từ công thức gốc với các dòng
	bếp đề xuất, ghi sổ ngay; lịch sử ghi người đề xuất, người duyệt, lý do."""
	_kiem_duyet()
	doc = _doc_khoa(name)
	if doc.loai != LOAI_DIEU_CHINH:
		frappe.throw("Phiếu công thức mới thì bấm Tạo mã và công thức.")
	if doc.trang_thai != TT_CHO:
		frappe.throw("Phiếu %s đang %s, không duyệt được." % (doc.name, doc.trang_thai.lower()))
	d = doc_du_lieu(doc.du_lieu)
	loi = kiem_phieu(doc.loai, doc.ten_banh, d, doc.bom_goc)
	frappe.db.sql("select name from `tabBOM` where name=%s for update", doc.bom_goc)
	cu = frappe.get_doc("BOM", doc.bom_goc)
	if cint(cu.docstatus) != 1 or not cint(cu.is_default):
		loi.append("Công thức %s không còn là bản đang dùng. Lập phiếu mới từ bản đang dùng." % cu.name)
	bang = doi_chieu([{"ma": i.item_code, "sl": i.qty} for i in cu.items],
		[{"ma": x.get("ma"), "sl": _so((x.get("gram") or {}).get(""))} for x in d["dong"]])
	if not co_thay_doi(bang):
		loi.append("Phiếu không đổi dòng nào so với công thức đang dùng.")
	if loi:
		frappe.throw("Chưa duyệt được:<br>" + "<br>".join(loi[:8]))
	dvt_cu = {i.item_code: i.uom for i in cu.items}
	dong = [(x["ma"], _so((x.get("gram") or {}).get("")), x.get("dvt") or dvt_cu.get(x["ma"])) for x in d["dong"]]
	ten_bom = _tao_bom(cu.item, cu.quantity, cu.uom, dong, cu.get("custom_chang"))
	_ct().ghi_so(ten_bom)
	frappe.get_doc("BOM", ten_bom).add_comment("Comment", "Điều chỉnh theo phiếu %s. Đề xuất: %s. Duyệt: %s. Lý do: %s" % (
		doc.name, _ten(doc.nguoi_de_xuat), _ten(frappe.session.user), doc.ly_do or "không ghi"))
	doc = _doc_khoa(name)
	doc.ket_qua = json.dumps({"bom": [{"bom": ten_bom, "ma": cu.item, "bac": 3}]}, ensure_ascii=False)
	doc.trang_thai = TT_XONG
	doc.nguoi_duyet = frappe.session.user
	_luu_doc(doc)
	frappe.db.commit()
	return _cho_man(doc)


def viec(vai):
	"""Dòng Việc cần làm: Khải thấy phiếu Chờ Khải và Đã tạo nháp (chưa ghi sổ);
	người đề xuất thấy phiếu của mình bị Trả lại bếp."""
	la_duyet = bool(_ct()._vai_ghi_so() & set(vai or ()))
	from vagabond import viec_tu_dong as vtd
	# Lọc ngay trong câu đọc (không lọc sau LIMIT): phiếu bị trả của chính người
	# xem, cộng phiếu chờ Khải nếu người xem là Khải.
	loc = [{"trang_thai": TT_TRA, "nguoi_de_xuat": frappe.session.user}]
	if la_duyet:
		loc.append({"trang_thai": ["in", [TT_CHO, TT_DA_TAO]]})
	dong = []
	for f in loc:
		dong += frappe.get_all(DT, filters=f, fields=["name", "loai", "ten_banh", "trang_thai", "nguoi_de_xuat", "modified"],
			order_by="modified asc", limit_page_length=0)
	ra = []
	for r in sorted(dong, key=lambda r: str(r.modified)):
		if not ma_viec(r.trang_thai, la_duyet, r.nguoi_de_xuat == frappe.session.user):
			continue
		ra.append(vtd.dong_viec("de_xuat_ct", r.name, r.trang_thai,
			"%s: %s · %s" % (r.loai, r.ten_banh or "", _ten(r.nguoi_de_xuat)), str(r.modified)[:10], False))
	return ra


def gia_von_bom(b):
	"""Giá vốn một công thức cho màn Danh mục công thức: tổng chi phí ERPNext đã
	tính trên công thức (một nguồn), giá bán của mã, và dòng chưa có giá."""
	ban = _gia_ban(b.item)
	von = flt(b.total_cost)
	q = flt(b.quantity) or 1
	mot = von / q if q else von
	thieu = [i.item_name or i.item_code for i in (b.items or []) if flt(i.rate) <= 0]
	return {"tong": round(von), "mot": round(mot), "ban": ban, "ty_le": ty_le(mot, ban), "thieu": thieu, "dvt": b.uom}

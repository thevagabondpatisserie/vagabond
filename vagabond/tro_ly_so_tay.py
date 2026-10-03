# -*- coding: utf-8 -*-
"""Sổ tay tri thức cho trợ lý trong app: MÁY SINH, không gõ tay.

Anh Việt giao 26/08/2026: dựng một trợ lý trong app để nhân viên hỏi cách
dùng bất kỳ màn hình nào.


VÌ SAO SỔ TAY PHẢI DO MÁY SINH
==============================

Một tệp hướng dẫn gõ tay thì đúng đúng một tuần. App này mỗi ngày lên một
bản, màn hình đổi, luật đổi, câu chặn đổi. Sổ tay gõ tay sẽ lệch với phần
mềm, và trợ lý dạy nhân viên làm theo cái không còn tồn tại - tệ hơn hẳn
việc không có trợ lý.

Nên sổ tay ở đây dựng lại từ CHÍNH MÃ NGUỒN mỗi lần gọi, lấy từ ba nguồn đã
có sẵn và đã được cổng kiểm canh:

1. Bảng `MAN` trong `duong_app.py`. Một nguồn duy nhất cho 90 màn hình, có
   cổng kiểm đối chiếu từng byte với bảng bên JavaScript. Cho ra TÊN màn và
   ĐỊA CHỈ mở màn đó.

2. Các thẻ trên trang chủ trong `02-trang-chu.js`. Mỗi thẻ đã sẵn một dòng
   mô tả viết cho người dùng đọc, ví dụ "Còn nợ nhà cung cấp nào, khoản nào
   quá hạn". Đây là câu chữ đã được duyệt qua mắt người thật.

3. Đoạn mô tả đầu mỗi tệp Python nghiệp vụ. Đây là nguồn quý nhất: mỗi tệp
   đều có một đoạn dài kể việc gì, vì sao làm vậy, ca hỏng thật nào sinh ra
   nó. Chính những đoạn đó trả lời được câu khó nhất mà nhân viên hay hỏi:
   "vì sao máy chặn tôi".

Sổ tay tự đúng theo mã nguồn. Không có bước "nhớ cập nhật tài liệu".


CHỖ CẦN CẨN THẬN
================

Đoạn mô tả đầu tệp chép NGUYÊN VĂN lời anh Việt, trong đó có xưng hô đời
thường. Trợ lý phải nói giọng "Hệ thống", nên phần gọi mô hình ngôn ngữ chỉ
dùng sổ tay làm TƯ LIỆU chứ không chép lại giọng văn. Luật đó nằm ở
`tro_ly.py`, không nằm ở đây.
"""

import re

# Bao nhiêu ký tự đầu của đoạn mô tả một tệp thì đủ. Cắt để một câu hỏi
# không kéo theo mười nghìn chữ.
DAI_DOAN = 1800

# Từ quá phổ biến, có mặt ở mọi câu nên không giúp phân biệt mục nào.
TU_BO = frozenset("""
la va cua o cho khi thi ma nhu de duoc co khong con nao day kia
mot hai ba bon nam sau bay tam chin muoi
lam sao the nay do gi ai dau bao nhieu vi cai cach
toi minh anh chi ban ho ta
tren duoi trong ngoai truoc sau
""".split())


def bo_dau(t):
	"""Bỏ dấu tiếng Việt và hạ thường. THUẦN."""
	import unicodedata

	t = unicodedata.normalize("NFD", str(t or ""))
	t = "".join(c for c in t if unicodedata.category(c) != "Mn")
	return t.replace("\u0111", "d").replace("\u0110", "d").lower()


def tu_khoa(t):
	"""Bộ từ khoá của một câu, đã bỏ dấu và bỏ từ quá phổ biến. THUẦN."""
	tu = re.findall(r"[a-z0-9]+", bo_dau(t))
	return {x for x in tu if len(x) > 1 and x not in TU_BO}


def doc_the_trang_chu(nguon_js):
	"""Rút các thẻ chức năng trên trang chủ. THUẦN.

	Mỗi thẻ khai `card(biểu tượng, tên, mô tả, số đếm, khoá màn)`. Trả về
	{khoá màn: mô tả}.

	Chỉ bắt các thẻ khai chuỗi thẳng. Vài thẻ lấy tên từ biến (`TYPES.X.title`)
	thì bỏ qua: đoán mò giá trị của biến trong một tệp JavaScript bằng biểu
	thức chính quy là cách chắc chắn sinh ra mô tả sai.
	"""
	mau = re.compile(
		r"card\(\s*'([^'\\]*)'\s*,\s*'([^'\\]*)'\s*,\s*'([^'\\]*)'\s*,"
		r"\s*[^,]+?,\s*'([^'\\]*)'",
		re.S,
	)
	ra = {}
	for _bt, _ten, mo_ta, khoa in mau.findall(str(nguon_js or "")):
		khoa = khoa.strip()
		mo_ta = re.sub(r"\s+", " ", mo_ta).strip()
		if khoa and mo_ta and khoa not in ra:
			ra[khoa] = mo_ta
	return ra


def doan_dau_tep(nguon_py, dai=DAI_DOAN):
	"""Đoạn mô tả đầu một tệp Python, đã gọn lại. THUẦN.

	Trả về chuỗi rỗng nếu tệp không mở đầu bằng đoạn mô tả.
	"""
	s = str(nguon_py or "").lstrip()
	if s.startswith("# -*-"):
		s = s.split("\n", 1)[-1].lstrip()
	for dau in ('"""', "'''"):
		if s.startswith(dau):
			het = s.find(dau, len(dau))
			if het < 0:
				return ""
			than = s[len(dau):het]
			than = re.sub(r"\n{3,}", "\n\n", than).strip()
			return than[:dai]
	return ""


DAU_CHUA_XAC_MINH = "CHƯA XÁC MINH"
DONG_DAN_CHUA_XAC_MINH = ("Lưu ý cho trợ lý: mục này có điểm đánh dấu [CHƯA XÁC MINH]. "
	"Phần đó không được hướng dẫn như điều chắc chắn.")


def doc_chuong(nguon_md):
	"""Tách một chương sổ tay viết tay thành các mục. THUẦN.

	v554, anh Việt giao 02/10/2026. Ba câu hỏi thật đầu tiên trong nhật ký
	(cấn trừ công nợ, tạo phiếu nhập kho, đặt lại mật khẩu) đều nhận câu
	"chưa có tài liệu": đoạn mô tả đầu tệp mã nguồn kể VÌ SAO làm, không kể
	BẤM NÚT NÀO. Nên thêm một nguồn thứ tư là sổ tay viết cho nhân viên đọc,
	nằm trong `vagabond/so_tay/`, quy ước ở `_quy-uoc.md` cùng thư mục.

	Mỗi mục mở bằng `## `. Dòng `Từ khoá:` đi vào ô mô tả (chấm điểm nặng
	hơn thân mục) vì đó là chỗ khai các cách gọi khác của cùng một việc.
	Chú thích HTML thường là ghi chú cho người rà soát, không gửi mô hình.

	RIÊNG chú thích `<!-- kiểm: ... -->` (điểm người soạn CHƯA XÁC MINH)
	thì KHÔNG được xoá im lặng. Review #412 F1: bản đầu xoá hết, nên mô hình
	nhận câu khẳng định mà không biết đó là điều chưa ai thử, và luật "chỉ
	dựa vào tư liệu" trong `tro_ly.py` lại bảo nó tin tư liệu. Hướng dẫn sai
	về tiền, kho, quyền hay phiên đăng nhập mà nói giọng chắc chắn thì tệ
	hơn không nói. Nên chú thích đó đổi thành dấu `[CHƯA XÁC MINH: ...]`
	nằm đúng chỗ trong thân mục, mục được gắn cờ `chua_xac_minh`, và đầu
	thân mục có một dòng dặn mô hình. `tro_ly.py` có luật đi kèm.
	"""
	def _doi(m):
		than_cmt = m.group(1).strip()
		if bo_dau(than_cmt).startswith("kiem"):
			y = than_cmt.split(":", 1)[1].strip() if ":" in than_cmt else than_cmt
			return "[%s: %s]" % (DAU_CHUA_XAC_MINH, y)
		return ""

	s = re.sub(r"<!--(.*?)-->", _doi, str(nguon_md or ""), flags=re.S)
	chuong = ""
	m = re.search(r"^# +(.+)$", s, re.M)
	if m:
		chuong = m.group(1).strip()
	ra = []
	for khoi in re.split(r"^## +", s, flags=re.M)[1:]:
		dong = khoi.split("\n")
		ten = dong[0].strip()
		if not ten:
			continue
		than, tu = [], ""
		for d in dong[1:]:
			if not tu and bo_dau(d).startswith("tu khoa:"):
				tu = d.split(":", 1)[1].strip()
				continue
			than.append(d)
		than = re.sub(r"\n{3,}", "\n\n", "\n".join(than)).strip()
		chua = ("[" + DAU_CHUA_XAC_MINH + ":") in than
		dau = ("Chương: %s\n" % chuong) if chuong else ""
		if chua:
			dau += DONG_DAN_CHUA_XAC_MINH + "\n"
		# Dia chi man (review #412, bo sung 1). Vong 3 doi khuon: man hinh
		# nam trong BANG tom tat, khong con dong "Man hinh:" rieng. Lay dia chi
		# DAU TIEN dang "(/chu-thuong)" trong than muc, la o cot Man hinh cua
		# bang tom tat theo quy uoc.
		duong = ""
		md = re.search(r"\((/[a-z0-9][a-z0-9-]*)\)", than)
		if md:
			duong = md.group(1)
		ra.append({
			"loai": "so_tay",
			"ten": ten,
			"duong": duong,
			"mo_ta": ("Từ khoá: " + tu) if tu else "",
			"chi_tiet": dau + than,
			"chua_xac_minh": 1 if chua else 0,
		})
	return ra


def chuong_cho_man(nguon_md, ma=""):
	"""Một chương dạng dành cho màn Sổ tay trong app. THUẦN.

	Khác tư liệu gửi mô hình ở hai chỗ: bỏ dòng "Chương:" và dòng dặn trợ lý
	(người đọc không cần), còn dấu [CHƯA XÁC MINH: ...] thì GIỮ để màn vẽ
	thành ô cảnh báo màu, người đọc biết chỗ nào chưa ai thử.
	"""
	s = str(nguon_md or "")
	m = re.search(r"^# +(.+)$", s, re.M)
	ten = m.group(1).strip() if m else ma
	muc = []
	for x in doc_chuong(s):
		than = x["chi_tiet"]
		than = re.sub(r"^Chương: .*\n", "", than, count=1)
		than = than.replace(DONG_DAN_CHUA_XAC_MINH + "\n", "")
		muc.append({
			"ten": x["ten"],
			"tu_khoa": (x["mo_ta"] or "").replace("Từ khoá: ", "", 1),
			"than": than.strip(),
			"duong": x["duong"],
			"chua_xac_minh": x["chua_xac_minh"],
		})
	return {"ma": ma, "ten": ten, "muc": muc}


def duoc_xem_so_tay(nguoi, loai_tk, vai, la_noi_bo):
	"""Người này có được mở màn Sổ tay không. THUẦN.

	Codex #412 F3: bản đầu chỉ chặn Guest, nên tài khoản khách hàng hay nhà
	cung cấp đăng nhập cổng web vẫn đọc đủ sáu chương. Sổ tay cho MỌI NHÂN
	VIÊN, không phải mọi tài khoản đăng nhập. `la_noi_bo` là phép phân biệt
	người của tiệm đang dùng ở màn Quản lý người dùng
	(`nguoi_dung.trong_pham_vi_quan_ly`): tài khoản nội bộ luôn qua, tài
	khoản web chỉ qua khi giữ vai trong gói chức vụ, nên bạn bếp Lab dạng
	Website User vẫn vào được, còn khách và nhà cung cấp thì không.
	"""
	if str(nguoi or "") in ("", "Guest"):
		return False
	return bool(la_noi_bo(loai_tk, vai))


def dong_goi_tu_lieu(cac_muc, tran=9000):
	"""Như `gon_tu_lieu` nhưng trả thêm các mục THẬT SỰ được đóng gói. THUẦN.

	Codex #412: câu cấn trừ chọn 6 mục nhưng trần 9000 ký tự chỉ chứa 5, mà
	nhật ký vẫn ghi đủ 6 nguồn. Nguồn ghi vào nhật ký phải là mục mô hình
	đã đọc, không phải mục đã chọn.
	"""
	phan, dai, da = [], 0, []
	for m in cac_muc or []:
		khoi = "## %s\n" % (m.get("ten") or "")
		if m.get("duong"):
			khoi += "Địa chỉ mở màn: %s\n" % m["duong"]
		if m.get("mo_ta"):
			khoi += "%s\n" % m["mo_ta"]
		if m.get("chi_tiet"):
			khoi += "%s\n" % m["chi_tiet"]
		if dai + len(khoi) > tran:
			break
		phan.append(khoi)
		da.append(m)
		dai += len(khoi)
	return "\n".join(phan).strip(), da


def diem_khop(tu_hoi, muc):
	"""Mục này khớp câu hỏi tới đâu. THUẦN.

	Tên màn nặng hơn mô tả, mô tả nặng hơn phần chi tiết dài. Lý do: người
	ta hỏi "màn doanh số ở đâu" thì cái đáng trả về là màn tên Doanh số, chứ
	không phải một tệp nào đó có chữ "doanh số" nằm giữa nghìn chữ.
	"""
	if not tu_hoi:
		return 0
	d = 0
	d += 6 * len(tu_hoi & tu_khoa(muc.get("ten")))
	d += 3 * len(tu_hoi & tu_khoa(muc.get("mo_ta")))
	d += 1 * len(tu_hoi & tu_khoa(muc.get("chi_tiet")))
	return d


# Muc sat nhat phai phu duoc bao nhieu PHAN cua cau hoi thi moi coi la so
# tay co tai lieu. Do tren so tay that ngay 26/08/2026, 177 muc.
#
# VI SAO PHAI CO NGUONG NAY, va vi sao "co chu nao trung la duoc" KHONG DU.
#
# Ban dau phep chon chi doi diem lon hon 0, tuc chi can mot chu trung la
# nhan. Do tren so tay that thi luat do gan nhu khong bao gio tu choi: hoi
# "hom nay troi dep khong" van ra sau muc, vi trong hon mot tram doan mo ta
# cua mot tiem banh thi chu nao cung tung xuat hien o dau do. Rieng chu
# "banh" thi co mat khap noi.
#
# Nhu vay cai chan quan trong nhat, khong co tu lieu thi khong goi mo hinh,
# xem nhu khong ton tai: cau nao cung duoc dua sang mo hinh kem mot mo tu
# lieu khong lien quan. Vua ton tien vua moi mo hinh bia.
#
# Do tren mot bo cau that: tam cau hoi ve app deu phu tu 0,75 tro len, con
# nam cau ngoai le nhu "cach nuong banh mi sourdough tai nha", "gia vang hom
# nay bao nhieu", "thu do nuoc Phap la gi" thi phu quanh 0,57 den 0,67. Dat
# nguong 0,75 thi tam cau that van qua het, con bon trong nam cau ngoai le
# bi chan.
#
# Cau ngoai le con lot duoc thi con hai lop chan phia sau: luat cam bia
# trong `tro_ly.py` va nhiet do 0. Nguong nay khong phai lop duy nhat, no
# chi khong duoc phep vo dung nhu truoc.
TI_LE_PHU = 0.75

# Muc phu phai dat it nhat ty le nay cua diem muc dau. Xem chon_muc.
TI_LE_DIEM_PHU = 0.4


def phu_tu_khoa(tu_hoi, muc):
	"""Mục này phủ được bao nhiêu từ khoá của câu hỏi. THUẦN."""
	if not tu_hoi:
		return 0
	co = tu_khoa(muc.get("ten")) | tu_khoa(muc.get("mo_ta")) | tu_khoa(muc.get("chi_tiet"))
	return len(tu_hoi & co)


def du_lien_quan(tu_hoi, muc, ti_le=TI_LE_PHU):
	"""Mục này có đủ liên quan tới câu hỏi không. THUẦN."""
	if not tu_hoi:
		return False
	can = int(len(tu_hoi) * float(ti_le))
	if can < len(tu_hoi) * float(ti_le):
		can += 1
	return phu_tu_khoa(tu_hoi, muc) >= max(1, can)


def chon_muc(cau_hoi, so_tay, so_muc=6, ti_le=TI_LE_PHU):
	"""Vài mục sổ tay sát câu hỏi nhất. THUẦN.

	Trả về danh sách đã xếp theo điểm giảm dần. Không mục nào ĐỦ liên quan
	thì trả về danh sách RỖNG, và nơi gọi phải hiểu đó là "chưa biết" chứ
	không được lấy bừa mấy mục đầu bảng.

	Ngưỡng liên quan xem `TI_LE_PHU`. Mục sát nhất phải qua ngưỡng thì cả
	danh sách mới được nhận: qua rồi thì các mục sau xếp theo điểm để mô
	hình có thêm ngữ cảnh, nhưng chính mục sát nhất mới quyết định sổ tay có
	tài liệu hay không.
	"""
	tu = tu_khoa(cau_hoi)
	if not tu:
		return []
	cham = []
	for m in so_tay or []:
		d = diem_khop(tu, m)
		if d > 0:
			cham.append((phu_tu_khoa(tu, m), d, m))
	if not cham:
		return []
	# Xep theo DO PHU truoc, roi moi toi diem. Do phu tra loi cau "muc nay
	# co dinh toi cau hoi khong", con diem tra loi cau "dinh toi muc nao
	# manh hon". Xep nham thu tu thi muc phu tron ven cau hoi co the bi mot
	# muc dai lem nhem day xuong duoi, va cai chan ben duoi soi nham nguoi.
	# v554: cung do phu thi muc so tay viet tay dung truoc doan mo ta dau
	# tep. So tay noi bam nut nao, doan mo ta noi vi sao lam; nguoi hoi
	# "cach lam X" can cai truoc.
	cham.sort(key=lambda x: (-x[0], 0 if x[2].get("loai") == "so_tay" else 1,
		-x[1], str(x[2].get("ten") or "")))
	if not du_lien_quan(tu, cham[0][2], ti_le):
		return []
	# Review #412 bo sung 2: muc PHU chi giu khi diem du gan muc dau. Do
	# phu thi gan nhu muc dai nao cung du (than muc dai chua du chu), nen hoi
	# "dat lai mat khau" van keo theo "Lam bao gia" (diem 0,16 muc dau) vao
	# tu lieu: ton token va tron huong dan. Do tren 6 cau that 02/10/2026:
	# muc phu dung viec deu tu 0,41 tro len, muc lac de deu duoi 0,33.
	d0 = cham[0][1] or 1
	ra = [cham[0][2]]
	for _p, d, m in cham[1:]:
		if len(ra) >= max(1, int(so_muc or 6)):
			break
		if d >= d0 * TI_LE_DIEM_PHU:
			ra.append(m)
	return ra


def gon_tu_lieu(cac_muc, tran=9000):
	"""Ghép các mục đã chọn thành tư liệu gửi kèm câu hỏi. THUẦN.

	Có trần ký tự: một câu hỏi kéo theo cả mã nguồn là vừa chậm vừa tốn
	tiền, mà mô hình cũng đọc kém đi khi tư liệu quá dài. Phần ghép nằm ở
	`dong_goi_tu_lieu`, hàm này giữ cho nơi gọi cũ.
	"""
	return dong_goi_tu_lieu(cac_muc, tran)[0]


# ------------------------------------------------------- phan can Frappe

import os

import frappe

# Tệp nghiệp vụ KHÔNG đưa vào sổ tay: hạ tầng, tiện ích, hoặc chính trợ lý.
BO_TEP = frozenset("""
__init__.py hooks.py lib.py dich.py mau_chuan.py
tro_ly.py tro_ly_so_tay.py
""".split())

KHOA_NHO = "vgb_tro_ly_so_tay_v564"


def _goc():
	return frappe.get_app_path("vagabond")


def _doc(duong):
	try:
		with open(duong, encoding="utf-8") as f:
			return f.read()
	except Exception:
		return ""


def dung_so_tay():
	"""Dựng lại sổ tay từ mã nguồn. Trả về danh sách mục."""
	from vagabond import duong_app

	goc = _goc()
	the = doc_the_trang_chu(
		_doc(os.path.join(goc, "public", "js", "bep", "02-trang-chu.js")))

	# Bang_duong() la {slug: khoa}, can chieu nguoc lai de biet mo mot man
	# thi go dia chi nao. Mot khoa chi co dung mot slug nen lat khong mat gi.
	dia_chi = {}
	for slug, khoa in duong_app.bang_duong().items():
		dia_chi.setdefault(khoa, "/" + slug)

	ra = []
	# So tay viet tay (v554) nap TRUOC. Tep bat dau bang "_" la quy uoc,
	# khong nap.
	thu_muc = os.path.join(goc, "so_tay")
	if os.path.isdir(thu_muc):
		for ten_tep in sorted(os.listdir(thu_muc)):
			if ten_tep.endswith(".md") and not ten_tep.startswith("_"):
				ra.extend(doc_chuong(_doc(os.path.join(thu_muc, ten_tep))))

	for hang in getattr(duong_app, "MAN", ()):
		ma, ten = hang[0], hang[1]
		ra.append({
			"loai": "man",
			"ten": ten,
			"duong": dia_chi.get(ma, ""),
			"mo_ta": the.get(ma, ""),
			"chi_tiet": "",
		})

	for ten_tep in sorted(os.listdir(goc)):
		if not ten_tep.endswith(".py") or ten_tep in BO_TEP:
			continue
		doan = doan_dau_tep(_doc(os.path.join(goc, ten_tep)))
		if not doan:
			continue
		dong_dau = doan.split("\n", 1)[0].strip().rstrip(".")
		ra.append({
			"loai": "nghiep_vu",
			"ten": dong_dau or ten_tep,
			"duong": "",
			"mo_ta": "",
			"chi_tiet": doan,
		})
	return ra


def so_tay(dung_lai=0):
	"""Sổ tay, có nhớ lại. Dựng lại mỗi lần deploy vì bộ nhớ đệm trống."""
	if not frappe.utils.cint(dung_lai):
		co = frappe.cache().get_value(KHOA_NHO)
		if co:
			return co
	ra = dung_so_tay()
	frappe.cache().set_value(KHOA_NHO, ra, expires_in_sec=3600)
	return ra


@frappe.whitelist()
def doc_so_tay():
	"""Toàn bộ sổ tay viết tay cho màn Sổ tay (v554). CHỈ ĐỌC.

	Mọi NHÂN VIÊN xem được, kể cả tài khoản bếp Lab dạng Website User;
	khách hàng và nhà cung cấp thì không (Codex #412 F3, xem
	`duoc_xem_so_tay`). Khác trợ lý (chỉ cấp quản lý) vì trợ lý tốn tiền gọi
	mô hình, sổ tay thì không.
	"""
	from vagabond.nguoi_dung import trong_pham_vi_quan_ly

	nguoi = frappe.session.user
	loai = frappe.db.get_value("User", nguoi, "user_type") if nguoi not in (None, "", "Guest") else ""
	if not duoc_xem_so_tay(nguoi, loai, frappe.get_roles(nguoi), trong_pham_vi_quan_ly):
		frappe.throw("Sổ tay chỉ mở cho nhân viên của tiệm.", frappe.PermissionError)
	thu_muc = os.path.join(_goc(), "so_tay")
	ra = []
	if os.path.isdir(thu_muc):
		for ten_tep in sorted(os.listdir(thu_muc)):
			if ten_tep.endswith(".md") and not ten_tep.startswith("_"):
				ra.append(chuong_cho_man(_doc(os.path.join(thu_muc, ten_tep)), ten_tep[:-3]))
	return {"chuong": ra}

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
		# Chỉ chặn chữ số ở phía mã cũng là CHỮ SỐ. Mã mở đầu bằng chữ
		# ("APP", "HDB") thì chữ số đứng trước không làm nó thành khúc của
		# một số dài hơn. Ca thật 21/09/2026: "TT HD 1840 APP 26 09 799"
		# gọt thành "...1840APP2609799", bản cũ thấy chữ 0 trước chữ A nên
		# bỏ qua, phiếu APP-26-09-799 báo "ngân hàng chưa chi" dù tiền đã đi.
		chan_truoc = g_ma[0].isdigit() and truoc.isdigit()
		chan_sau = g_ma[-1].isdigit() and sau.isdigit()
		if not chan_truoc and not chan_sau:
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


def xep_ung_vien(dong, ma_phieu, tien_phieu, thu_tu="goi_y"):
	"""Xếp thứ tự ứng viên cho NGƯỜI nhìn. THUẦN.

	Khớp mã lên trước, rồi đúng số tiền, trong nhóm ngày mới nhất trước. Số tiền chỉ dùng
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
		x["khop_ma"] = 1 if (ma_phieu and co_ma("%s %s" % (d.get("mo_ta") or "", d.get("reference_number") or ""), ma_phieu)) else 0
		x["dung_tien"] = 1 if lech <= DUNG_SAI else 0
		x["lech"] = lech
		ra.append(x)
	# Sắp ổn định: ngày là ưu tiên trong nhóm, mã bản ghi phá hoà.
	ra.sort(key=lambda r: (str(r.get("date") or ""), str(r.get("creation") or ""), str(r.get("name") or "")), reverse=True)
	if thu_tu != "moi_nhat":
		ra.sort(key=lambda r: (-r.get("dung_duoc", 1), -r["khop_ma"], -r["dung_tien"]))
	return ra




# ------------------------------------------------- lớp 3: thanh toán tiện ích
#
# v528, anh Việt 25/09/2026: tiền điện, nước, internet trả bằng tính năng
# "thanh toán hoá đơn" trong app ngân hàng thì KHÔNG gõ được nội dung, nên
# sao kê không bao giờ mang mã APP. Dòng thật của hồ sơ APP.26.09.100:
#     "WATER BT WATER 1032865688 e0Vh5pp20ek.BP1"
# và của APP.26.09.101 cùng ngày: "WATER TH WATER 1032865615 faILoefoMwM.BP1".
# Dãy số dài ĐỔI mỗi lần trả (là số lệnh của ngân hàng, không phải mã khách
# hàng), phần đuôi là chuỗi ngẫu nhiên. Phần ỔN ĐỊNH chỉ là mấy chữ đầu:
# "WATER BT WATER" (Bến Thành), "WATER TH WATER" (Tân Hoà), "EVN-HCM
# ELECTRIC", "PAYOO WATER". Vì vậy máy nhớ MẪU ĐẦU DÒNG theo nhà cung cấp,
# không nhớ dãy số.

# Chữ đầu dòng do người gõ khi chuyển khoản thường, không phải tên dịch vụ
# của ngân hàng. Mẫu bắt đầu bằng các chữ này thì không nhớ, vì nó khớp với
# mọi lệnh chuyển tay.
CHU_CHUNG = frozenset((
	"THANH", "TOAN", "TT", "CK", "CHUYEN", "TIEN", "MBCT", "VAGABOND", "VGB",
	"KH", "IBFT", "TRA", "NOP", "RUT", "PHI", "HOAN", "NHAN", "GD", "QR",
))
_CHU_MAU = re.compile(r"^[A-Z][A-Z&\-]*$")


def _chu(mo_ta):
	return str(mo_ta or "").split()


def mau_sao_ke(mo_ta):
	"""Mẫu đầu dòng của một lệnh thanh toán tiện ích. THUẦN.

	Lấy các chữ IN HOA liên tiếp ở đầu nội dung, dừng ở chữ đầu tiên có số,
	có chữ thường hoặc dài quá 10 ký tự (chuỗi ngẫu nhiên của ngân hàng).
	Tối đa 4 chữ. Trả "" khi không ra mẫu dùng được: quá ngắn, hoặc bắt đầu
	bằng chữ chung của lệnh chuyển tay.
	"""
	ra = []
	for t in _chu(mo_ta):
		if len(ra) >= 4 or len(t) > 10 or not _CHU_MAU.match(t):
			break
		ra.append(t)
	mau = " ".join(ra)
	if not ra or ra[0] in CHU_CHUNG or len(mau.replace(" ", "")) < 5:
		return ""
	return mau


def doc_ds_mau(chu):
	"""Ô nhớ mẫu trên nhà cung cấp, mỗi dòng một mẫu. THUẦN."""
	ra = []
	for d in str(chu or "").splitlines():
		m = " ".join(d.split()).upper()
		if m and m not in ra:
			ra.append(m)
	return ra


def khop_mau(mo_ta, ds_mau):
	"""Mẫu dài nhất mà nội dung sao kê BẮT ĐẦU bằng nó, trọn chữ. THUẦN.

	So trọn chữ: mẫu "WATER BT" không khớp "WATER BTX ...". Không có thì "".
	"""
	dong = " ".join(_chu(mo_ta)).upper()
	for m in sorted(ds_mau or [], key=len, reverse=True):
		if m and (dong == m or dong.startswith(m + " ")):
			return m
	return ""


def mau_chong_nhau(a, b):
	"""Hai mẫu có cùng khớp một dòng sao kê không, theo đúng luật của
	khop_mau: trùng hẳn, hoặc mẫu này là tiền tố TRỌN CHỮ của mẫu kia. THUẦN.

	Codex #371 M2: "WATER BT" và "WATER BT WATER" cùng khớp dòng "WATER BT
	WATER ...", nên hai NCC giữ hai mẫu đó là máy lấy nhầm tiền của nhau."""
	a = " ".join(str(a or "").split()).upper()
	b = " ".join(str(b or "").split()).upper()
	if not a or not b:
		return False
	return a == b or a.startswith(b + " ") or b.startswith(a + " ")


def khop_tu_khoa(tu_khoa, dong):
	"""Ô tìm của màn chọn sao kê: tìm chữ, hoặc tìm ĐÚNG số tiền. THUẦN.

	Người đi tìm một khoản trả tiện ích thường gõ số tiền trên hoá đơn
	("1.144.382", "1144382 đ"). Trước v528 ô tìm chỉ so chữ trong nội dung
	nên số tiền không bao giờ ra. `dong` cần `name`, `mo_ta`, `tien`.
	"""
	tk = str(tu_khoa or "").strip().lower()
	if not tk:
		return True
	if tk in ("%s %s" % (dong.get("name") or "", dong.get("mo_ta") or "")).lower():
		return True
	so = re.sub(r"[\s.,đd]", "", tk)
	return len(so) >= 4 and so.isdigit() and int(so) == int(round(_so(dong.get("tien"))))


_MA_APP = re.compile(r"APP[.\-]?\d{2}[.\-]?\d{2}[.\-]?\d{3,}", re.I)


def co_ma_app_khac(mo_ta, ma_minh):
	"""Dòng sao kê mang mã hồ sơ APP của NGƯỜI KHÁC. THUẦN.

	Codex #370 vòng 1: dòng "WATER BT WATER APP.26.09.999 ..." đúng mẫu, đúng
	tiền nhưng đã ghi rõ là của hồ sơ khác; lấy nó theo mẫu là giành tiền của
	hồ sơ kia. Dòng có mã khác thì không khớp theo mẫu, không gợi ý."""
	minh = got(ma_minh)
	return any(got(m) != minh for m in _MA_APP.findall(str(mo_ta or "")))


def xep_goi_y(ds, ngay_lap):
	"""Xếp gợi ý giao dịch không mang mã. THUẦN.

	Dòng khớp mẫu đã nhớ lên trước, rồi ngày gần ngày lập hồ sơ nhất, mã bản
	ghi phá hoà. `ds` là dict có `date`, `name`, `da_nho`.
	"""
	import datetime

	def ngay(v):
		try:
			return datetime.date.fromisoformat(str(v or "")[:10])
		except ValueError:
			return None
	goc = ngay(ngay_lap)

	def xa(r):
		d = ngay(r.get("date"))
		return abs((d - goc).days) if (d and goc) else 10 ** 6
	return sorted(ds, key=lambda r: (-int(r.get("da_nho") or 0), xa(r), str(r.get("name") or "")))

# -*- coding: utf-8 -*-
"""Mã phiếu kế hoạch sản xuất, lệnh sản xuất và lô hàng.

Anh Việt 30/08/2026: "đổi tiền tố mã của phiếu kế hoạch sản xuất thay vì là
MFG- thì đổi thành KHSX-26-08-0001 để thấy rõ tháng năm. Cả lệnh sản xuất
cũng nên là LSX-26-08-0001, rồi đánh số lại theo từng tháng."

Anh Việt 06/09/2026 (#206, theo ý kiến Khải) đổi lại phần đuôi số:

    Mã lệnh sản xuất và mã lô của thành phẩm, bán thành phẩm dùng đuôi SÁU
    chữ số, và số đó tăng LIÊN TỤC. Sang ngày, sang tháng, sang năm đều
    KHÔNG đánh lại từ đầu.

Phần ngày trong mã vẫn là NGÀY TẠO chứng từ theo múi giờ site. Ngày và bộ
đếm là hai việc độc lập: ngày đổi nhưng đuôi số cứ nối tiếp.

    LSX-060926-000010  ->  lệnh kế tiếp tạo ngày 07/09 là LSX-070926-000011
    LO-260906-000751   ->  lô kế tiếp ngày 07/09 là LO-260907-000752

Vì sao KHÔNG dùng được chuỗi đặt tên của Frappe
-----------------------------------------------
`make_autoname` đếm theo TIỀN TỐ ĐÃ ĐIỀN: bảng `tabSeries` giữ một dòng
riêng cho mỗi tiền tố, tức mỗi ngày một dòng `LSX-060926-`, `LSX-070926-`.
Sang ngày là dòng đếm khác, số về 1. Không có cách nào vừa giữ ngày trong
mã vừa đếm liên tục bằng chuỗi đặt tên. Nên phải tự đặt tên, tách hẳn phần
ngày khỏi phần đếm. Thiết kế vòng 3 (`LSX-.DD.MM.YY.-.######`) chính là cái
đánh lại theo ngày, nên đã bỏ.

Cấp số bằng gì
--------------
`frappe.model.naming.getseries(khoá, 6)`, đúng hàm Frappe dùng cho mọi
naming_series. Đọc mã frappe 16.27.1: nó `SELECT current ... FOR UPDATE`
(khoá dòng) rồi `UPDATE current = current + 1`, nên hai người tạo cùng lúc
không thể nhận cùng một số; lượt sau chờ lượt trước cởi khoá. Mã khách hàng
KL/SI/DN (`vagabond/ma_khach.py`) đã cấp số bằng đúng hàm này từ 12/08/2026,
tức đường này có vết chạy thật chứ không phải mới thử.

KHÔNG dùng MAX+1, không đếm bản ghi, không nhớ số ở trình duyệt.

Đuôi số dài ra chứ không quay vòng
----------------------------------
Sáu chữ số là số chữ số TỐI THIỂU. Qua 999999 thì in ra bảy chữ số
(1000000), không quay về 000001, không cắt bớt. Trong tệp này không có phép
chia dư ở đâu cả, xem `duoi_so`.

Mã mới không thể trùng mã cũ
----------------------------
Mã lệnh cũ `LSX-26-09-0010`, `MFG-WO-2026-00048` khác hẳn hình dạng. Lô cũ
`LO-260906-0002` có đuôi bốn chữ số, mã mới luôn từ sáu chữ số trở lên.
Khác độ dài thì không có cách nào ra cùng một chuỗi.

Cấp số hỏng thì CHẶN, không lùi về quy tắc khác
-----------------------------------------------
Bản đầu để hook nuốt lỗi rồi cho Frappe đặt tên theo naming_series. Codex
bác trên #215 (06/09/2026): làm vậy là một mã kiểu cũ chen vào giữa dãy
mới, trái yêu cầu tăng liên tục, mà người tạo phiếu không hề biết. Nay cấp
số hỏng là `frappe.throw` với câu nói rõ; phiếu chưa lưu nên dữ liệu vừa
nhập vẫn còn trên màn hình để bấm lại. Dòng đếm chưa được dựng cũng chặn,
không để `getseries` tự tạo dòng ở 1.

Chuỗi naming_series theo tháng vẫn được đặt cho Production Plan (KHSX đi
bằng chuỗi đó) và vẫn nằm trong danh sách chọn của Work Order để phiếu cũ
mở được, nhưng KHÔNG còn là đường lùi của lệnh nữa.

Mốc bắt đầu của dòng đếm
------------------------
Lấy theo ĐUÔI LỚN NHẤT đã từng cấp trong cùng họ mã (LSX-*, MFG-WO-* cho
lệnh; LO-* cho lô) cộng với mọi dòng đếm cùng họ đang có trong tabSeries.
Không lấy số chứng từ: 56 lệnh nhưng có lệnh mang đuôi 113, dựng ở 56 là
lệnh mới mang số nhỏ hơn lệnh cũ. Đọc mốc hỏng thì không dựng, ghi nhật
ký, và hook chặn cho tới khi migrate lại thành công. Xem `moc_bao_toan`.

Phiếu CŨ giữ nguyên mã cũ
-------------------------
Toàn bộ lệnh đang mang mã `MFG-WO-2026-00xxx` và lô đang mang số nhà cung
cấp vẫn giữ tên cũ. Đổi tên một chứng từ đã ghi sổ là sửa dữ liệu quá khứ:
bút toán kho, mẻ hàng, phiếu yêu cầu đều trỏ về tên đó. Luật của tiệm là
không tự sửa dữ liệu cũ, nên máy KHÔNG đổi tên phiếu cũ, chỉ đếm và kể ra.

Vì sao chuỗi cũ vẫn nằm trong danh sách chọn
--------------------------------------------
Ô `naming_series` là ô Select. Phiếu cũ đang giữ giá trị `MFG-WO-.YYYY.-`.
Bỏ giá trị đó khỏi danh sách thì mở phiếu cũ trên Desk là Frappe báo giá
trị không hợp lệ, sửa một ô bất kỳ cũng không lưu được. Nên chuỗi mới được
đặt lên ĐẦU và làm mặc định, chuỗi cũ vẫn còn ở dưới.
"""

# ------------------------------------------------------------ phần thuần

import re

# Doctype -> tien to moi. Chi hai cai nay, dung them cho vui.
TIEN_TO = {
	"Production Plan": "KHSX",
	"Work Order": "LSX",
}

# So chu so TOI THIEU cua duoi. Qua 999999 thi dai ra, xem `duoi_so`.
SO_CHU_SO = 6

# Khoa dong dem trong bang `tabSeries`. HAI day RIENG, khong gop lam mot:
# gop thi so doc ra khong con noi duoc la lenh thu may hay lo thu may, va
# mot day chung tieu so nhanh gap doi.
KHOA_LENH = "LSX"
KHOA_LO = "LO"

# Toi nguong nay thi ghi mot dong nhat ky de con kip ban truoc khi duoi so
# dai ra bay chu so. Voi nhip hien tai (chuc lo moi ngay) con rat xa.
NGUONG_CANH_BAO = 900000

# Tien to ma lo. Giu dung tien to tem dang in.
TIEN_TO_LO = "LO"


class LoiCapSo(ValueError):
	"""Cấp số hỏng. Ném ra để người tạo phiếu THẤY, không âm thầm lùi về
	quy tắc khác. Codex chốt trên #215: mã mới phải luôn tăng liên tục, nên
	khi không cấp được số thì phải chặn và giữ dữ liệu nhập cho người ta thử
	lại, chứ không được lặng lẽ đẻ ra một mã kiểu cũ."""


def duoi_so(so, so_chu_so=SO_CHU_SO):
	"""Đuôi số của mã, tối thiểu `so_chu_so` chữ số. THUẦN.

	Qua 999999 thì chuỗi DÀI RA (1000000) chứ không quay về 000001 và cũng
	không bị cắt. Đây là chỗ duy nhất quyết định hình dạng đuôi số, mọi nơi
	khác gọi vào đây (điều 18: một nguồn, không rải công thức).

	Số rác (None, chữ, âm) thì NÉM LỖI. Bản trước trả về "000000" cho rác,
	tức biến một lần cấp số hỏng thành một mã trông như thật, và hai lần
	hỏng là hai chứng từ cùng mang 000000. Codex bắt trên #215.
	"""
	try:
		so = int(so)
	except (TypeError, ValueError):
		raise LoiCapSo("Số cấp ra không phải số: %r" % (so,))
	if so < 1:
		raise LoiCapSo("Số cấp ra phải từ 1 trở lên, nhận được %r" % (so,))
	try:
		so_chu_so = int(so_chu_so)
	except (TypeError, ValueError):
		so_chu_so = SO_CHU_SO
	if so_chu_so < 1:
		so_chu_so = 1
	return ("%0" + str(so_chu_so) + "d") % so


def duoi_so_cua(ten):
	"""Đuôi số đã cấp của một mã: phần số sau dấu gạch cuối. THUẦN.

	LSX-060926-000057 -> 57, MFG-WO-2026-00048 -> 48, LSX-26-09-0010 -> 10,
	LO-260906-0028 -> 28. Không có phần số thì None. Dùng để chọn mốc bắt đầu
	không lùi so với mọi số đã từng cấp.
	"""
	m = re.search(r"-(\d+)$", (ten or "").strip())
	return int(m.group(1)) if m else None


def moc_bao_toan(cac_ten, cac_dong_dem):
	"""Mốc bắt đầu cho dòng đếm: lớn nhất trong mọi đuôi đã cấp và mọi dòng
	đếm đã có cùng họ. THUẦN.

	Codex chốt trên #215: số lượng chứng từ KHÔNG phải đuôi lớn nhất. Đếm
	bản ghi ra 56 trong khi có lệnh mang đuôi 113, dựng dòng đếm ở 56 là
	lệnh mới mang số nhỏ hơn lệnh cũ. Nên soi thẳng đuôi của từng mã.
	"""
	lon = 0
	for t in cac_ten or []:
		d = duoi_so_cua(t)
		if d is not None and d > lon:
			lon = d
	for c in cac_dong_dem or []:
		try:
			c = int(c or 0)
		except (TypeError, ValueError):
			continue
		if c > lon:
			lon = c
	return lon


def _ngay(x):
	"""Đưa về đối tượng ngày. Nhận date, datetime hoặc chuỗi YYYY-MM-DD."""
	import datetime

	if isinstance(x, datetime.datetime):
		return x.date()
	if isinstance(x, datetime.date):
		return x
	s = str(x or "")[:10]
	return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def ddmmyy(x):
	"""Ngày viết kiểu ddmmyy cho mã lệnh: 06/09/2026 -> "060926". THUẦN."""
	d = _ngay(x)
	return "%02d%02d%02d" % (d.day, d.month, d.year % 100)


def yymmdd(x):
	"""Ngày viết kiểu yymmdd cho mã lô: 06/09/2026 -> "260906". THUẦN.

	Lô đảo thứ tự so với lệnh vì tem đang in như vậy từ trước, đổi lại là
	đổi hình dạng tem của những lô đã in.
	"""
	d = _ngay(x)
	return "%02d%02d%02d" % (d.year % 100, d.month, d.day)


def ma_lenh(ngay, so):
	"""Mã lệnh sản xuất: LSX-060926-000057. THUẦN."""
	return "%s-%s-%s" % (TIEN_TO["Work Order"], ddmmyy(ngay), duoi_so(so))


def ma_lo(ngay, so):
	"""Mã lô: LO-260906-000751. THUẦN."""
	return "%s-%s-%s" % (TIEN_TO_LO, yymmdd(ngay), duoi_so(so))


def la_ma_lo_may_dat(ten):
	"""Mã lô này do MÁY đặt theo khuôn LO-yymmdd-số chưa. THUẦN.

	Dùng làm đường lùi khi không biết người có gõ số lô hay không, xem
	`_may_duoc_dat_lo`. Mã lô nhà cung cấp kiểu KKK2600007-NVLT00026 không
	khớp khuôn này nên máy không đụng vào.
	"""
	ten = (ten or "").strip().upper()
	return bool(re.match(r"^%s-\d{6}-\d+$" % re.escape(TIEN_TO_LO), ten))


def chuoi_cua(doctype):
	"""Chuỗi đặt tên naming_series cho MỘT doctype. Nguồn duy nhất.

	Từ 06/09/2026 chuỗi này chỉ còn là ĐƯỜNG LÙI cho lệnh sản xuất: tên
	thật do hook `dat_ten_lenh` đặt. Kế hoạch sản xuất thì vẫn đi bằng
	chuỗi này, vì KHSX không nằm trong yêu cầu đổi.
	"""
	tt = TIEN_TO.get(doctype)
	if not tt:
		return ""
	return chuoi_ma(tt)


def chuoi_ma(tien_to):
	"""Chuỗi đặt tên theo tháng cho một tiền tố: KHSX -> KHSX-.YY.-.MM.-.####

	Viết thành hàm riêng chứ không rải chuỗi khắp nơi, vì sai một dấu chấm
	là Frappe hiểu thành chữ thường: `.YY-` (thiếu dấu chấm đóng) cho ra mã
	có đúng chữ "YY" nằm trong tên phiếu, mà tên phiếu thì không sửa lại
	được.
	"""
	tien_to = (tien_to or "").strip().upper()
	if not tien_to:
		return ""
	return "%s-.YY.-.MM.-.####" % tien_to


def gop_chuoi(moi, cu):
	"""Danh sách chuỗi đặt tên: chuỗi mới lên đầu, chuỗi cũ giữ nguyên ở dưới.

	Giữ chuỗi cũ vì phiếu cũ đang mang giá trị đó trong ô Select; xem phần
	đầu tệp. Không nhân bản nếu chuỗi mới đã có sẵn trong danh sách.
	"""
	cu_dong = [d.strip() for d in (cu or "").replace("\r", "").split("\n")]
	cu_dong = [d for d in cu_dong if d]
	ra = [moi] if moi else []
	for d in cu_dong:
		if d not in ra:
			ra.append(d)
	return "\n".join(ra)


def la_ma_theo_ngay(ten, tien_to):
	"""Mã này theo kiểu ngày chưa: LSX-060926-000057 đúng, LSX-26-09-0001 chưa.

	Sáu chữ số ngày tháng năm liền nhau, gạch, rồi đuôi số. Chỉ so tiền tố
	là không đủ, cùng lý do với `la_ma_kieu_moi`.
	"""
	ten = (ten or "").strip().upper()
	tien_to = (tien_to or "").strip().upper()
	if not ten or not tien_to:
		return False
	return bool(re.match(r"^%s-\d{6}-\d+$" % re.escape(tien_to), ten))


def ngay_tao_trong_ma(ten, tien_to):
	"""Đọc ngày tạo từ mã kiểu ngày: LSX-060926-000057 -> "2026-09-06". THUẦN.

	Mã không theo kiểu ngày, hoặc sáu số không phải một ngày có thật
	(LSX-320926-...), trả về "" chứ không đoán. Dùng để màn hình hiện
	"tạo ngày 06/09" mà không phải hỏi máy chủ thêm một lượt.
	"""
	if not la_ma_theo_ngay(ten, tien_to):
		return ""
	so = ten.strip().upper().split("-")[1]
	dd, mm, yy = int(so[0:2]), int(so[2:4]), int(so[4:6])
	import datetime
	try:
		return datetime.date(2000 + yy, mm, dd).isoformat()
	except ValueError:
		return ""


def la_ma_kieu_moi(ten, tien_to):
	"""Mã này đã theo kiểu mới chưa. Kiểu mới có HAI dạng, cả hai đều tính:
	theo tháng `LSX-26-08-0001` (30/08 tới 06/09/2026) và theo ngày
	`LSX-060926-000057` (từ 06/09/2026). `LSX-2026-00113` là kiểu cũ.

	Chỉ so tiền tố là KHÔNG đủ. Lệnh sản xuất trước đây đã mang chuỗi
	`LSX-.YYYY.-`, tức mã cũ `LSX-2026-00113` cũng bắt đầu bằng "LSX-" y
	như mã mới. Đếm kiểu đó thì `soat_ma_cu` báo không còn mã cũ nào trong
	khi thực tế còn 48 lệnh. Nên soi đúng hình dạng.
	"""
	ten = (ten or "").strip().upper()
	tien_to = (tien_to or "").strip().upper()
	if not ten or not tien_to:
		return False
	if la_ma_theo_ngay(ten, tien_to):
		return True
	return bool(re.match(r"^%s-\d{2}-\d{2}-\d+$" % re.escape(tien_to), ten))


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, nowdate


def dung():
	"""Đặt chuỗi đặt tên và dựng sẵn dòng đếm. Gọi từ after_migrate.

	Lặp lại được không giới hạn lần: `make_property_setter` ghi đè đúng một
	bản ghi, còn dòng đếm chỉ dựng khi CHƯA có.
	"""
	ra = {}
	for dt, tt in TIEN_TO.items():
		try:
			ra[dt] = _dat_mot(dt, tt)
		except Exception:
			# Hong o day KHONG duoc chan ca lan migrate: site khong len duoc
			# phien ban moi thi ca tiem dung, ma loi that chi la ma phieu
			# van mang tien to cu.
			frappe.log_error(frappe.get_traceback(), "ma_phieu_sx: %s" % dt)
			ra[dt] = "loi"
	try:
		ra["bo_dem"] = dat_moc_bo_dem()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ma_phieu_sx: moc bo dem")
		ra["bo_dem"] = "loi"
	return ra


def _dat_mot(dt, tien_to):
	"""Đặt chuỗi mới cho MỘT doctype. Trả về chữ mô tả việc đã làm."""
	from frappe.custom.doctype.property_setter.property_setter import (
		make_property_setter,
	)

	if not frappe.db.exists("DocType", dt):
		return "khong co doctype"

	meta = frappe.get_meta(dt)
	o = meta.get_field("naming_series")
	if not o:
		# Doctype nay khong dat ten bang naming_series thi doi chuoi la vo
		# nghia. Bao ra chu khong am tham lam gi ca.
		return "khong co o naming_series"

	dat_ten = (meta.autoname or "").strip().lower()
	if not dat_ten.startswith("naming_series"):
		# ERPNext co the doi cach dat ten giua cac ban. Ghi chuoi vao mot o
		# khong ai doc toi thi ma van ra kieu cu ma minh lai tuong da xong.
		return "autoname khong theo naming_series (%s)" % (meta.autoname or "")

	moi = chuoi_cua(dt)
	cu = o.options or ""
	gop = gop_chuoi(moi, cu)
	if gop != cu:
		make_property_setter(dt, "naming_series", "options", gop, "Text",
			validate_fields_for_doctype=False)
	if (o.default or "") != moi:
		make_property_setter(dt, "naming_series", "default", moi, "Text",
			validate_fields_for_doctype=False)
	frappe.clear_cache(doctype=dt)
	return "da dat %s" % moi


# ------------------------------------------------------------ dong dem
#
# Moc bat dau lay theo DUOI LON NHAT da tung cap trong cung ho ma, cong voi
# moi dong dem cung ho dang co trong tabSeries. Khong lay so chung tu: Codex
# chi ra so luong ban ghi khong phai duoi lon nhat (56 lenh nhung co lenh
# mang duoi 113).
#
# Dung san dong dem con bit mot khe nua: getseries chi khoa dong khi dong
# DA ton tai. Dong chua co thi hai luot cung luc cung chay INSERT va mot
# luot hong. Tao truoc la het khe do.
#
# DOC MOC HONG THI KHONG DUNG. Dung bua o 0 la lenh moi mang so nho hon
# lenh cu. Ghi nhat ky, de dong dem trong, va hook cap so se CHAN cho toi
# khi migrate lai thanh cong (xem _so_moi).

MOC_THEO_KHOA = {
	KHOA_LENH: "Work Order",
	KHOA_LO: "Batch",
}

# Nhung tien to cua ma CU cung ho, de soi duoi da cap.
HO_TIEN_TO = {
	KHOA_LENH: ("LSX-", "MFG-WO-"),
	KHOA_LO: ("LO-",),
}


def _cac_ten_cung_ho(khoa):
	"""Mọi mã đang có trong cùng họ. Ném lỗi nếu không đọc được."""
	dt = MOC_THEO_KHOA[khoa]
	ra = []
	for tt in HO_TIEN_TO[khoa]:
		ra += frappe.get_all(dt, filters={"name": ["like", tt + "%"]},
			pluck="name", limit_page_length=0)
	return ra


def _cac_dong_dem_cung_ho(khoa):
	"""Giá trị `current` của mọi dòng tabSeries cùng họ. Ném lỗi nếu không đọc được."""
	ra = []
	for tt in HO_TIEN_TO[khoa]:
		for (c,) in frappe.db.sql(
				"select `current` from `tabSeries` where `name` like %s", (tt + "%",)):
			ra.append(c)
	# Va chinh dong cua khoa, neu da co.
	for (c,) in frappe.db.sql("select `current` from `tabSeries` where `name`=%s", (khoa,)):
		ra.append(c)
	return ra


def _dong_dem_dang_co(khoa):
	d = frappe.db.sql("select `current` from `tabSeries` where `name`=%s", (khoa,))
	return cint(d[0][0]) if d else None


def dat_moc_bo_dem():
	"""Dựng dòng đếm ở mốc bảo toàn. Chỉ tăng, không bao giờ hạ.

	Chạy lại nhiều lần không đổi gì: dòng đã ở mốc rồi là đi ra. Dòng đã có
	mà thấp hơn mốc thì NÂNG lên mốc (nâng là an toàn, hạ mới nguy hiểm).
	Đọc mốc hỏng thì không đụng gì và ghi nhật ký.
	"""
	ra = {}
	for khoa in MOC_THEO_KHOA:
		try:
			moc = moc_bao_toan(_cac_ten_cung_ho(khoa), _cac_dong_dem_cung_ho(khoa))
			dang = _dong_dem_dang_co(khoa)
			if dang is None:
				frappe.db.sql(
					"insert into `tabSeries` (`name`, `current`) values (%s, %s)",
					(khoa, moc))
				ra[khoa] = "dung moi o %s" % moc
			elif dang < moc:
				frappe.db.sql(
					"update `tabSeries` set `current`=%s where `name`=%s and `current`<%s",
					(moc, khoa, moc))
				ra[khoa] = "nang tu %s len %s" % (dang, moc)
			else:
				ra[khoa] = "da o %s, giu nguyen" % dang
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ma_phieu_sx: dong dem %s" % khoa)
			ra[khoa] = "loi, khong dung"
	return ra


def _so_moi(khoa):
	"""Một số chưa ai dùng, lấy nguyên tử từ bảng `tabSeries`.

	Trả về CHUỖI đã zero-pad qua `duoi_so`, để hình dạng đuôi số chỉ do một
	hàm quyết định. `getseries` cũng tự pad, nhưng đi vòng qua `duoi_so` thì
	đổi luật pad về sau chỉ phải sửa một chỗ.
	"""
	if _dong_dem_dang_co(khoa) is None:
		# Khong de getseries tu tao dong o 1: dong o 1 la ma moi nho hon ma
		# cu. Migrate se dung dong nay o moc bao toan; chua co thi chan.
		raise LoiCapSo(
			"Bộ đếm %s chưa được dựng trên hệ. Chạy lại migrate (after_migrate "
			"dựng dòng đếm) rồi tạo lại. Dữ liệu vừa nhập chưa mất." % khoa)
	from frappe.model.naming import getseries

	so = cint(getseries(khoa, SO_CHU_SO))
	if so > NGUONG_CANH_BAO:
		try:
			frappe.log_error(
				"Bộ đếm %s đã tới %s. Qua 999999 thì đuôi số dài thành bảy "
				"chữ số, mã vẫn đúng và vẫn tăng, nhưng nên bàn trước." % (khoa, so),
				"ma_phieu_sx: bo dem sap day")
		except Exception:
			pass
	return duoi_so(so)


def _chua_ai_mang(dt, ten):
	try:
		return not frappe.db.exists(dt, ten)
	except Exception:
		return True


# ------------------------------------------------------------ hai hook dat ten


def dat_ten_lenh(doc, method=None):
	"""Hook autoname của Work Order: LSX-ddmmyy-nnnnnn.

	Chạy sau autoname của lớp. Đặt được `doc.name` ở đây thì Frappe bỏ qua
	đường naming_series (frappe/model/naming.py, `set_new_name`).

	Hỏng thì để Frappe đặt theo naming_series, tức chuỗi theo THÁNG, khác
	hình dạng nên không thể trùng dãy mới.
	"""
	try:
		if getattr(doc, "doctype", None) != "Work Order":
			return
		if (getattr(doc, "name", None) or "").strip():
			# Ai do da dat ten roi (luat dat ten cua Frappe, ban SUA phieu,
			# hay import). May khong cai.
			return
		ngay = _hom_nay()
		for _ in range(5):
			ten = ma_lenh(ngay, _so_moi(KHOA_LENH))
			if _chua_ai_mang("Work Order", ten):
				doc.name = ten
				return
		raise LoiCapSo("Năm số liên tiếp đều đã có người mang, bộ đếm đang lệch với dữ liệu.")
	except Exception as e:
		# KHONG nuot. Nuot la Frappe dat ten theo naming_series, tuc mot ma
		# kieu cu chen vao giua day moi, trai yeu cau tang lien tuc. Nem ra
		# de nguoi tao phieu thay va thu lai; phieu chua luu nen du lieu
		# nhap van con tren man hinh.
		frappe.log_error(frappe.get_traceback(), "ma_phieu_sx: dat ten lenh")
		frappe.throw("Không cấp được mã lệnh sản xuất: %s Dữ liệu vừa nhập chưa mất, "
			"bấm lưu lại; vẫn hỏng thì báo quản lý." % _cau(e), title="Cấp mã lệnh hỏng")


def nho_nguoi_go_lo(doc, method=None):
	"""Hook before_naming của Batch: ghi nhớ NGƯỜI có gõ số lô hay không.

	Phải ghi ở đây chứ không đọc lại ở `autoname`: tới lúc đó ERPNext đã
	tự điền `batch_id` từ chuỗi của mã hàng rồi, không phân biệt được nữa.
	"""
	try:
		if getattr(doc, "doctype", None) != "Batch":
			return
		doc.flags.vgb_nguoi_go_lo = 1 if (doc.get("batch_id") or "").strip() else 0
	except Exception:
		pass


def _may_duoc_dat_lo(doc):
	"""Máy có được đặt lại số cho lô này không.

	Người gõ số lô (mã lô nhà cung cấp trên phiếu nhập) thì KHÔNG. Đây là
	661 trên 750 lô đang có.

	Không thấy dấu vết của `before_naming` thì không đoán bừa: chỉ nhận
	những mã đúng khuôn máy đặt `LO-yymmdd-số`.
	"""
	co = None
	try:
		co = doc.flags.get("vgb_nguoi_go_lo")
	except Exception:
		co = None
	if co is not None:
		return not cint(co)
	return la_ma_lo_may_dat(getattr(doc, "name", None)
		or (doc.get("batch_id") if hasattr(doc, "get") else ""))


def dat_ten_lo(doc, method=None):
	"""Hook autoname của Batch: LO-yymmdd-nnnnnn cho lô MÁY đặt số.

	Đặt cả `batch_id` lẫn `name`, vì ERPNext hiện `batch_id` ra màn hình và
	tem in đọc ô đó. Để lệch hai ô là tem một đằng sổ một nẻo.
	"""
	try:
		if getattr(doc, "doctype", None) != "Batch":
			return
		if not _may_duoc_dat_lo(doc):
			return
		ngay = _hom_nay()
		for _ in range(5):
			ten = ma_lo(ngay, _so_moi(KHOA_LO))
			if _chua_ai_mang("Batch", ten):
				doc.batch_id = ten
				doc.name = ten
				return
		raise LoiCapSo("Năm số liên tiếp đều đã có người mang, bộ đếm đang lệch với dữ liệu.")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "ma_phieu_sx: dat ten lo")
		frappe.throw("Không cấp được mã lô: %s Phiếu chưa ghi sổ, dữ liệu vừa nhập chưa "
			"mất; bấm lại, vẫn hỏng thì báo quản lý." % _cau(e), title="Cấp mã lô hỏng")


def _cau(e):
	"""Câu lỗi ngắn để ghép vào thông báo, không kéo cả traceback lên màn."""
	t = " ".join(str(e or "").split())
	return (t[:160] + ("..." if len(t) > 160 else "")) if t else "lỗi không rõ."


def _hom_nay():
	"""Ngày của máy chủ theo múi giờ site. Không lấy đồng hồ trình duyệt."""
	return nowdate()


# ------------------------------------------------------------ chi doc


@frappe.whitelist()
def soat_ma_cu():
	"""Đếm xem còn bao nhiêu phiếu mang mã kiểu cũ, để anh Việt biết mà đọc.

	KHÔNG đổi tên phiếu nào. Đổi tên chứng từ đã ghi sổ là sửa dữ liệu quá
	khứ; việc của hàm này chỉ là đếm và kể ra vài mã đầu tiên.
	"""
	_kiem_quyen()
	ra = []
	for dt, tt in TIEN_TO.items():
		if not frappe.db.exists("DocType", dt):
			continue
		ds = frappe.get_all(dt, fields=["name"], limit_page_length=0)
		cu = [d["name"] for d in ds if not la_ma_kieu_moi(d["name"], tt)]
		ra.append({"doctype": dt, "tien_to": tt, "tong": len(ds),
			"con_ma_cu": len(cu), "vai_ma": sorted(cu)[:5]})
	return ra


@frappe.whitelist()
def soat_bo_dem():
	"""Hai dòng đếm đang ở số mấy. CHỈ ĐỌC, không cấp số, không sửa gì.

	Cấp một số để xem thì số đó mất luôn, nên hàm này đọc thẳng bảng.
	"""
	_kiem_quyen()
	ra = []
	for khoa, dt in MOC_THEO_KHOA.items():
		so = None
		try:
			d = frappe.db.sql(
				"select `current` from `tabSeries` where `name`=%s", (khoa,))
			so = cint(d[0][0]) if d else None
		except Exception:
			so = None
		ra.append({
			"khoa": khoa, "doctype": dt, "dang_o": so,
			"so_ke_tiep": duoi_so(cint(so) + 1) if so is not None else None,
			"chung_tu_dang_co": frappe.db.count(dt),
		})
	return ra


def _kiem_quyen():
	if not set(frappe.get_roles()) & {"System Manager", "Manufacturing Manager",
			"Giám đốc", "AP Giám đốc"}:
		frappe.throw("Bạn chưa được cấp quyền xem mục này.")

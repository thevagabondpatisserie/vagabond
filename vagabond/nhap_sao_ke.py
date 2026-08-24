# -*- coding: utf-8 -*-
"""Nhập tệp sao kê ngân hàng, bù những giao dịch SePay không đẩy về.

Anh Việt 20/08/2026: *"Sao kê OCB của Uyên vẫn bị thiếu những khoản dưới
100k, và kéo về bị không đầy đủ."* Và 21/08/2026: *"nhập tệp sao kê OCB ->
Chỗ nhập tệp em cho vào màn app luôn nhé để Uyên nhập."*

Vì sao phải có đường này
------------------------
Đã dò tới cùng ngày 20/08/2026: gọi thẳng API của SePay cho ba ngày 12, 13,
14/08 thì SePay trả về 12, 10 và 5 giao dịch, và ERPNext đang giữ đủ cả ba
con số đó. Gom theo tài khoản thì thấy rõ hơn: OCB KHÔNG có một khoản nào
dưới 100k, trong khi MB có sáu khoản. Nghĩa là chỗ mất nằm giữa NGÂN HÀNG và
SePay, không nằm ở đoạn SePay sang mình.

Đoạn đó ngoài tầm sửa của tiệm. Cái trong tầm là: lấy tệp sao kê ngân hàng
gửi, đối chiếu với những gì đang có, và bù đúng phần thiếu. Nên có tệp này.

Ba điều giữ cứng
----------------
1. KHÔNG BAO GIỜ ghi đè dòng đã có. Khử trùng theo số giao dịch của ngân
   hàng (FT...), và trước khi ghi còn dò thêm theo ngày cộng số tiền cộng
   nội dung - vì SePay lưu số tham chiếu theo cách riêng của họ và không
   phải lúc nào cũng trùng chuỗi với sao kê.
2. XEM TRƯỚC rồi mới ghi. Uyên nhìn thấy đúng bao nhiêu dòng sẽ thêm, bao
   nhiêu dòng bỏ qua và vì sao, rồi mới bấm ghi. Nhập tệp mà máy tự ghi
   luôn là cách nhân đôi cả sổ ngân hàng chỉ bằng một cú bấm nhầm.
3. Phần ĐỌC TỆP là hàm thuần, không đụng frappe. Nhờ vậy bộ kiểm thử chạy
   được trên mọi dạng tệp lệch chuẩn mà không cần dựng cả một site.
"""

import re

TIEN_TO = "OCBSK-"

# Tên cột trên sao kê, viết thường và đã bỏ dấu. Mỗi khoá là một danh sách
# vì mỗi ngân hàng gọi một kiểu, và cùng một ngân hàng đổi tên cột giữa các
# bản xuất.
COT = {
	"stt": ["stt", "so tt", "no."],
	"ngay": ["ngay thuc hien", "ngay giao dich", "ngay", "transaction date", "ngay hieu luc"],
	"ngay_ghi": ["ngay ghi nhan", "ngay hach toan", "posting date"],
	"so_gd": ["so giao dich", "so tham chieu", "ma giao dich", "reference", "so but toan", "ref no"],
	"noi_dung": ["noi dung", "dien giai", "mo ta", "description", "noi dung giao dich"],
	"no": ["ps giam", "ps giam (no)", "no", "ghi no", "debit", "phat sinh giam", "tien ra"],
	"co": ["ps tang", "ps tang (co)", "co", "ghi co", "credit", "phat sinh tang", "tien vao"],
	"so_du": ["so du", "so du cuoi", "balance", "so du cuoi ky"],
}

DAU = {
	"à": "a", "á": "a", "ạ": "a", "ả": "a", "ã": "a", "â": "a", "ầ": "a", "ấ": "a",
	"ậ": "a", "ẩ": "a", "ẫ": "a", "ă": "a", "ằ": "a", "ắ": "a", "ặ": "a", "ẳ": "a",
	"ẵ": "a", "è": "e", "é": "e", "ẹ": "e", "ẻ": "e", "ẽ": "e", "ê": "e", "ề": "e",
	"ế": "e", "ệ": "e", "ể": "e", "ễ": "e", "ì": "i", "í": "i", "ị": "i", "ỉ": "i",
	"ĩ": "i", "ò": "o", "ó": "o", "ọ": "o", "ỏ": "o", "õ": "o", "ô": "o", "ồ": "o",
	"ố": "o", "ộ": "o", "ổ": "o", "ỗ": "o", "ơ": "o", "ờ": "o", "ớ": "o", "ợ": "o",
	"ở": "o", "ỡ": "o", "ù": "u", "ú": "u", "ụ": "u", "ủ": "u", "ũ": "u", "ư": "u",
	"ừ": "u", "ứ": "u", "ự": "u", "ử": "u", "ữ": "u", "ỳ": "y", "ý": "y", "ỵ": "y",
	"ỷ": "y", "ỹ": "y", "đ": "d",
}


def bo_dau(s):
	"""Bỏ dấu tiếng Việt và hạ chữ thường. THUẦN.

	Cần vì tên cột trên sao kê lúc có dấu lúc không, lúc HOA lúc thường, và
	so chuỗi thô thì bản xuất tháng sau là hỏng.
	"""
	s = str(s or "").strip().lower()
	return "".join(DAU.get(c, c) for c in s)


def chuan_ten_cot(s):
	"""Tên cột đã chuẩn hoá: bỏ dấu, bỏ ký tự lạ, ép về một khoảng trắng."""
	s = bo_dau(s)
	s = re.sub(r"[^a-z0-9 ]+", " ", s)
	return re.sub(r"\s+", " ", s).strip()


def doc_so(v):
	"""Đọc một ô tiền. THUẦN. Trả về float, không đọc được thì 0.

	Sao kê Việt Nam viết 1.234.567,00 còn bản xuất tiếng Anh viết
	1,234,567.00. Đoán sai dấu nào là dấu thập phân thì 1.234.567 thành
	1,23 - sai một triệu lần, và sai êm ru vì con số vẫn "trông như tiền".

	Luật: dấu nào ĐỨNG SAU CÙNG và theo sau đúng 1 tới 2 chữ số thì đó là
	dấu thập phân. Không thoả thì mọi dấu đều là dấu ngăn nghìn.
	"""
	if v is None:
		return 0.0
	if isinstance(v, (int, float)):
		return float(v)
	s = str(v).strip()
	if not s:
		return 0.0
	am = s.startswith("(") and s.endswith(")")
	s = s.strip("()")
	s = re.sub(r"[^0-9.,\-]", "", s)
	if not s or s in ("-", ".", ","):
		return 0.0
	cuoi = max(s.rfind("."), s.rfind(","))
	if cuoi > -1 and 1 <= len(s) - cuoi - 1 <= 2 and s.count(s[cuoi]) == 1:
		nguyen = re.sub(r"[.,]", "", s[:cuoi])
		le = s[cuoi + 1:]
		s = (nguyen or "0") + "." + le
	else:
		s = re.sub(r"[.,]", "", s)
	try:
		n = float(s)
	except ValueError:
		return 0.0
	return -n if am else n


def doc_ngay(v):
	"""Đọc một ô ngày về dạng yyyy-mm-dd. THUẦN. Không đọc được thì "".

	Nhận dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd, và cả chuỗi có kèm giờ.
	KHÔNG nhận mm/dd/yyyy: sao kê ngân hàng Việt Nam không dùng dạng đó, mà
	đoán thêm một dạng nữa thì 03/04 với 04/03 lẫn nhau vĩnh viễn.
	"""
	if v is None:
		return ""
	if hasattr(v, "strftime"):
		return v.strftime("%Y-%m-%d")
	s = str(v).strip()
	if not s:
		return ""
	s = s.split(" ")[0].split("T")[0]
	m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", s)
	if m:
		nam, thang, ngay = m.group(1), m.group(2), m.group(3)
	else:
		m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$", s)
		if not m:
			return ""
		ngay, thang, nam = m.group(1), m.group(2), m.group(3)
		if len(nam) == 2:
			nam = "20" + nam
	try:
		t, n = int(thang), int(ngay)
	except ValueError:
		return ""
	if not (1 <= t <= 12 and 1 <= n <= 31):
		return ""
	return "%s-%02d-%02d" % (nam, t, n)


def tim_dong_dau(bang, quet=30):
	"""Dòng nào là dòng tiêu đề. THUẦN. Trả về (chỉ số dòng, bản đồ cột).

	Sao kê ngân hàng luôn có mấy dòng đầu là tên ngân hàng, số tài khoản, kỳ
	sao kê. Đọc cứng "dòng 1 là tiêu đề" là hỏng ngay tệp đầu tiên.

	Điều kiện nhận: dòng đó phải chỉ ra được ÍT NHẤT cột nội dung và một
	trong hai cột tiền. Thiếu thì chưa phải tiêu đề, đi tiếp.
	"""
	for i, dong in enumerate(bang[:quet]):
		bd = {}
		for j, o in enumerate(dong or []):
			ten = chuan_ten_cot(o)
			if not ten:
				continue
			for khoa, nhan in COT.items():
				if khoa in bd:
					continue
				if ten in nhan or any(ten.startswith(x) for x in nhan):
					bd[khoa] = j
					break
		if "noi_dung" in bd and ("no" in bd or "co" in bd):
			return i, bd
	return -1, {}


def doc_bang(bang):
	"""Đọc cả tệp sao kê thành danh sách giao dịch. THUẦN.

	Trả về (danh sách dòng, ghi chú lỗi). Dòng nào không có ngày hoặc không
	có tiền thì bỏ, vì đó là dòng tổng cộng hoặc dòng trống của bản xuất.
	"""
	if not bang:
		return [], "Tệp rỗng, không đọc được dòng nào."
	i, bd = tim_dong_dau(bang)
	if i < 0:
		return [], (
			"Không tìm ra dòng tiêu đề. Tệp sao kê phải có các cột Nội dung và "
			"PS giảm hoặc PS tăng. Kiểm lại xem có xuất đúng dạng Excel hay CSV "
			"của ngân hàng không."
		)

	def o(dong, khoa):
		j = bd.get(khoa)
		if j is None or j >= len(dong):
			return ""
		return dong[j]

	ra = []
	for dong in bang[i + 1:]:
		if not dong:
			continue
		ngay = doc_ngay(o(dong, "ngay")) or doc_ngay(o(dong, "ngay_ghi"))
		no = abs(doc_so(o(dong, "no")))
		co = abs(doc_so(o(dong, "co")))
		if not ngay or (not no and not co):
			continue
		ra.append({
			"ngay": ngay,
			"so_gd": str(o(dong, "so_gd") or "").strip(),
			"noi_dung": " ".join(str(o(dong, "noi_dung") or "").split()),
			"tien_ra": no,
			"tien_vao": co,
			"so_du": doc_so(o(dong, "so_du")),
		})
	if not ra:
		return [], (
			"Đọc được tiêu đề nhưng không có dòng giao dịch nào. Kiểm lại xem "
			"tệp có phải sao kê của kỳ đang cần không."
		)
	return ra, ""


def khoa_dong(d):
	"""Khoá khử trùng của một dòng. THUẦN.

	Ưu tiên số giao dịch của ngân hàng vì đó là mã duy nhất thật. Dòng nào
	ngân hàng để trống số giao dịch thì mới rơi xuống bộ ba ngày, tiền, nội
	dung - kém chắc hơn nhưng vẫn hơn là bỏ mất dòng.
	"""
	so = (d.get("so_gd") or "").strip()
	if so:
		return TIEN_TO + re.sub(r"\s+", "", so)
	tho = re.sub(r"[^a-z0-9]+", "", bo_dau(d.get("noi_dung") or ""))[:40]
	return "%s%s-%d-%d-%s" % (
		TIEN_TO, d.get("ngay") or "", int(d.get("tien_ra") or 0),
		int(d.get("tien_vao") or 0), tho,
	)


# ===================================================================
# PHẦN CHẠM CƠ SỞ DỮ LIỆU
# ===================================================================

import frappe
from frappe.utils import cint, flt

BT = "Bank Transaction"
# Trần dòng cho một lần nhập. Sao kê một tháng của tiệm khoảng 1.500 dòng,
# nên 5.000 là rộng rãi mà vẫn chặn được lần ai đó nhập nhầm tệp cả năm.
TRAN_DONG = 5000


def _doc_tep(file_url):
	"""Đọc tệp đính kèm thành bảng ô. Trả về (bảng, ghi chú lỗi)."""
	try:
		tep = frappe.get_doc("File", {"file_url": file_url})
		noi_dung = tep.get_content()
	except Exception:
		return [], (
			"Không mở được tệp vừa tải lên. Thử tải lại một lần nữa; vẫn lỗi "
			"thì báo anh Việt."
		)
	ten = (getattr(tep, "file_name", "") or file_url).lower()
	if ten.endswith((".xlsx", ".xlsm")):
		try:
			from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file

			return list(read_xlsx_file_from_attached_file(fcontent=noi_dung)), ""
		except Exception:
			frappe.log_error(frappe.get_traceback(), "nhap_sao_ke: doc xlsx loi")
			return [], (
				"Tệp Excel này máy chưa đọc được. Mở bằng Excel rồi lưu lại dạng CSV UTF-8, vui lòng tải lên lại."
			)
	if ten.endswith(".csv"):
		import csv
		import io as _io

		if isinstance(noi_dung, bytes):
			for ma in ("utf-8-sig", "utf-8", "cp1258", "latin-1"):
				try:
					noi_dung = noi_dung.decode(ma)
					break
				except UnicodeDecodeError:
					continue
		if isinstance(noi_dung, bytes):
			return [], "Tệp CSV dùng bảng mã máy không đọc được. Vui lòng lưu lại dạng CSV UTF-8."
		dau = noi_dung[:4000]
		nc = ";" if dau.count(";") > dau.count(",") else ","
		return [list(r) for r in csv.reader(_io.StringIO(noi_dung), delimiter=nc)], ""
	if ten.endswith(".xls"):
		return [], (
			"Tệp .xls đời cũ máy chưa đọc được. Mở bằng Excel, bấm Lưu thành "
			".xlsx hoặc CSV rồi tải lên lại."
		)
	return [], "Chỉ nhận tệp .xlsx hoặc .csv. Tệp vừa tải lên là %s." % (ten.rsplit(".", 1)[-1] or "không rõ")


def _da_co(tai_khoan, ds):
	"""Dòng nào trong sao kê ĐÃ có trong sổ. Trả về dict khoá -> mã Bank Transaction.

	Dò hai lượt vì hai lượt bắt hai kiểu trùng khác nhau:

	  1. Theo khoá của mình và theo `reference_number`. Bắt được dòng SePay
	     đã đẩy về kèm đúng số giao dịch của ngân hàng.
	  2. Theo bộ ba ngày, số tiền, tài khoản. Bắt được dòng SePay đẩy về mà
	     ghi số tham chiếu theo cách riêng của họ, không trùng chuỗi với sao
	     kê. Bỏ lượt này là mỗi lần nhập tệp lại nhân đôi sổ ngân hàng.
	"""
	ra = {}
	khoa = [khoa_dong(d) for d in ds]
	so_gd = [(d.get("so_gd") or "").strip() for d in ds if (d.get("so_gd") or "").strip()]
	for lo in (khoa, so_gd):
		for i in range(0, len(lo), 200):
			phan = lo[i:i + 200]
			if not phan:
				continue
			for t in ("transaction_id", "reference_number"):
				for r in frappe.get_all(
					BT, filters={t: ("in", phan)},
					fields=["name", "transaction_id", "reference_number"],
					limit_page_length=0,
				):
					for v in (r.get("transaction_id"), r.get("reference_number")):
						if v:
							ra[v] = r["name"]

	ngay = sorted({d["ngay"] for d in ds})
	if ngay:
		co = {}
		for r in frappe.get_all(
			BT,
			filters={
				"bank_account": tai_khoan,
				"date": ("between", [ngay[0], ngay[-1]]),
				"docstatus": ("<", 2),
			},
			fields=["name", "date", "deposit", "withdrawal"],
			limit_page_length=0,
		):
			k = "%s|%d|%d" % (str(r["date"])[:10], int(flt(r["deposit"])), int(flt(r["withdrawal"])))
			co.setdefault(k, []).append(r["name"])
		for d, k in zip(ds, khoa):
			if k in ra or (d.get("so_gd") or "").strip() in ra:
				continue
			bo = co.get("%s|%d|%d" % (d["ngay"], int(d["tien_vao"]), int(d["tien_ra"])))
			if bo:
				# Cùng ngày cùng số tiền: coi như đã có. Thà bỏ sót một dòng
				# thật hiếm hoi còn hơn nhân đôi một khoản tiền trong sổ.
				ra[k] = bo[0]
	return ra


def _phan_loai(tai_khoan, ds):
	"""Chia sao kê thành hai rổ: sẽ thêm và đã có."""
	co = _da_co(tai_khoan, ds)
	them, bo = [], []
	thay = set()
	for d in ds:
		k = khoa_dong(d)
		cu = co.get(k) or co.get((d.get("so_gd") or "").strip())
		if cu:
			bo.append(dict(d, khoa=k, vi_sao="Đã có trong sổ (%s)" % cu))
			continue
		if k in thay:
			bo.append(dict(d, khoa=k, vi_sao="Trùng với một dòng khác ngay trong tệp này"))
			continue
		thay.add(k)
		them.append(dict(d, khoa=k))
	return them, bo


def _tai_khoan_hop_le():
	return [
		r["name"]
		for r in frappe.get_all("Bank Account", fields=["name"], limit_page_length=0)
	]


@frappe.whitelist()
def danh_sach_tai_khoan():
	"""Tài khoản ngân hàng để Uyên chọn nhập vào đâu."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ra = []
	for r in frappe.get_all(
		"Bank Account",
		fields=["name", "account_name", "bank", "bank_account_no"],
		limit_page_length=0,
	):
		ra.append({
			"ma": r["name"],
			"ten": r.get("account_name") or r["name"],
			"ngan_hang": r.get("bank") or "",
			"so_tk": r.get("bank_account_no") or "",
		})
	ra.sort(key=lambda x: (x["ngan_hang"], x["ten"]))
	return {"ds": ra}


@frappe.whitelist()
def tai_len(ten=None, noi_dung=None):
	"""Nhận tệp sao kê từ màn hình, cất riêng tư, trả về đường dẫn.

	Tệp cất `is_private` và KHÔNG gắn vào chứng từ nào: sao kê ngân hàng có
	tên và nội dung chuyển khoản của khách, không được nằm ở đường công khai.
	"""
	_chan()
	ten = (ten or "").strip() or "sao-ke.xlsx"
	if not ten.lower().endswith((".xlsx", ".xlsm", ".csv")):
		frappe.throw(
			"Chỉ nhận tệp .xlsx hoặc .csv. Mở tệp ngân hàng gửi bằng Excel rồi bấm Lưu thành .xlsx hoặc CSV, vui lòng xong tải lên lại."
		)
	noi = (noi_dung or "").strip()
	if not noi:
		frappe.throw("Chưa chọn tệp sao kê. Vui lòng bấm Chọn tệp rồi thử lại.")
	if "," in noi and noi[:5].lower() == "data:":
		noi = noi.split(",", 1)[1]
	import base64

	try:
		so_byte = len(base64.b64decode(noi))
	except Exception:
		frappe.throw("Tệp gửi lên hỏng giữa đường nên máy không đọc được. Vui lòng chọn lại tệp.")
	if so_byte <= 0:
		frappe.throw("Tệp sao kê rỗng. Vui lòng kiểm lại tệp ngân hàng gửi.")
	if so_byte > 20 * 1024 * 1024:
		frappe.throw(
			"Tệp nặng %s MB, quá 20 MB. Cắt sao kê theo tháng rồi tải từng tệp."
			% ("{:.1f}".format(so_byte / 1024.0 / 1024.0))
		)
	f = frappe.get_doc({
		"doctype": "File", "file_name": ten, "content": noi,
		"decode": True, "is_private": 1,
	})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"file_url": f.file_url, "ten": ten}


@frappe.whitelist()
def xem_truoc(file_url, tai_khoan):
	"""Đọc tệp và nói TRƯỚC sẽ thêm gì, bỏ gì. KHÔNG ghi một dòng nào."""
	_chan()
	if tai_khoan not in _tai_khoan_hop_le():
		frappe.throw("Chưa chọn tài khoản ngân hàng, hoặc tài khoản không còn trên hệ.")
	bang, loi = _doc_tep(file_url)
	if loi:
		frappe.throw(loi)
	ds, loi = doc_bang(bang)
	if loi:
		frappe.throw(loi)
	if len(ds) > TRAN_DONG:
		frappe.throw(
			"Tệp có %d dòng, quá trần %d dòng một lần nhập. Cắt sao kê theo "
			"tháng rồi nhập từng tệp." % (len(ds), TRAN_DONG)
		)
	them, bo = _phan_loai(tai_khoan, ds)
	return {
		"tong": len(ds),
		"se_them": len(them),
		"bo_qua": len(bo),
		"tu_ngay": min(d["ngay"] for d in ds),
		"den_ngay": max(d["ngay"] for d in ds),
		"tien_vao": sum(d["tien_vao"] for d in them),
		"tien_ra": sum(d["tien_ra"] for d in them),
		# Chỉ gửi 60 dòng đầu mỗi rổ ra màn: điện thoại không vẽ nổi 1.500
		# dòng, và Uyên chỉ cần thấy mẫu để biết máy đọc có đúng không.
		"mau_them": them[:60],
		"mau_bo": bo[:60],
		"file_url": file_url,
		"tai_khoan": tai_khoan,
	}


@frappe.whitelist()
def nap(file_url, tai_khoan):
	"""Ghi thật những dòng còn thiếu vào sổ ngân hàng.

	Đọc lại tệp từ đầu chứ KHÔNG nhận danh sách dòng do màn hình gửi lên
	(QT-19). Màn hình gửi số nào lên thì ghi số đó là mở đúng cái cửa cho
	một dòng tiền bịa vào thẳng sổ ngân hàng.
	"""
	_chan()
	xt = xem_truoc(file_url, tai_khoan)
	bang, _ = _doc_tep(file_url)
	ds, _ = doc_bang(bang)
	them, bo = _phan_loai(tai_khoan, ds)

	da, hong = 0, []
	moi = []
	for d in them:
		try:
			bt = frappe.get_doc({
				"doctype": BT,
				"date": d["ngay"],
				"bank_account": tai_khoan,
				"deposit": flt(d["tien_vao"]),
				"withdrawal": flt(d["tien_ra"]),
				"currency": "VND",
				"description": d["noi_dung"],
				"reference_number": (d.get("so_gd") or "")[:140],
				"transaction_id": d["khoa"][:140],
			})
			bt.insert(ignore_permissions=True)
			bt.submit()
			# Ghi xuống NGAY từng dòng. Một dòng hỏng ở giữa không được kéo
			# theo mấy trăm dòng đã ghi đúng trước đó.
			frappe.db.commit()
			da += 1
			moi.append(bt.name)
		except Exception as e:
			frappe.db.rollback()
			hong.append({"ngay": d["ngay"], "so_gd": d.get("so_gd") or "", "loi": str(e)[:160]})
			frappe.log_error(frappe.get_traceback(), "nhap_sao_ke: ghi dong loi")

	# Đối soát ngay cho những dòng vừa thêm: khoản dưới 100k mà SePay bỏ sót
	# chính là khoản đang làm phiếu thanh toán nội bộ đứng ở "Chờ chi".
	khop = 0
	for ma in moi:
		try:
			from vagabond import de_nghi_chi

			de_nghi_chi.khi_co_giao_dich(ma)
			khop += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "nhap_sao_ke: doi soat sau khi nap loi")

	return {
		"da_them": da,
		"bo_qua": len(bo),
		"hong": hong,
		"tong": len(ds),
		"tu_ngay": xt["tu_ngay"],
		"den_ngay": xt["den_ngay"],
		"loi_nhan": (
			"Đã thêm %d dòng vào sổ, bỏ qua %d dòng đã có. Kỳ %s đến %s."
			% (da, len(bo), xt["tu_ngay"], xt["den_ngay"])
		) + (" Có %d dòng lỗi, xem danh sách bên dưới." % len(hong) if hong else ""),
	}


def _chan():
	"""Chỉ kế toán, thu mua và giám đốc được nhập sao kê.

	Sổ ngân hàng là căn cứ đối soát của cả hệ. Mở đường ghi vào đó cho mọi
	nhân viên là mở đường cho một dòng tiền không có thật.
	"""
	from vagabond.viec_can_lam import VAI_GIAM_DOC, VAI_KE_TOAN, VAI_THU_MUA

	if not (set(frappe.get_roles()) & (VAI_KE_TOAN | VAI_THU_MUA | VAI_GIAM_DOC)):
		frappe.throw(
			"Nhập sao kê ngân hàng chỉ mở cho Kế toán, Thu mua và Giám đốc. "
			"Cần dùng thì báo anh Việt cấp thêm chức vụ trong màn Quản lý người dùng."
		)

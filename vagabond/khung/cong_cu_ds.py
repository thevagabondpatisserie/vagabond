"""Bộ công cụ danh sách dùng chung: chip ngày, bảng Excel, sổ khai xuất.

Issue #380, anh Việt chốt 28/09/2026: *"Chip lọc, xuất excel, chip trạng thái
theo chặng,... là những cái tối cần thiết, áp dụng cho mọi màn."*

VÌ SAO GOM VỀ MỘT CHỖ
---------------------
Tới v533 có chín hàm xuất Excel viết riêng từng màn, mỗi hàm một kiểu cột,
một kiểu ngày, một trần dòng. Thêm màn thứ mười thì chép thêm bản thứ mười.
Quy tắc 18 của repo: cùng một việc tính ở nhiều nơi thì gom về một nguồn.

Tệp này có ba phần:

  * `khoang_ky`     THUẦN: chip ngày ra khoảng (từ, đến). Mọi màn dùng chung
                    một bộ chip ngày, nên "Tháng trước" ở màn nào cũng nghĩa
                    là cùng một khoảng.
  * `dung_bang`     THUẦN: cột khai báo cộng dòng dữ liệu ra bảng hai chiều
                    cho Excel. Tiền là SỐ (kế toán cộng được trong Excel),
                    ngày là dd/mm/yyyy.
  * `xuat_excel`    cửa mở ra ngoài DUY NHẤT. Nhận tên màn, tra sổ khai
                    `MAN_XUAT` ra adapter của màn đó rồi gọi. Tên màn lạ bị
                    từ chối, không nạp mô đun tuỳ ý theo chuỗi người gửi.

ADAPTER CỦA TỪNG MÀN (Codex #381 F5)
-----------------------------------
Không gọi thẳng hàm danh sách của màn với `day_du=1`: mỗi hàm nhận một bộ
tham số khác nhau, có hàm còn ép trần 500 dòng. Mỗi màn khai MỘT adapter
`xuat_*(**loc)` trong chính mô đun của nó. Adapter tự kiểm quyền bằng đúng
cổng quyền của màn, tự chọn những khoá lọc nó hiểu, bỏ qua khoá lạ, và lấy
ĐỦ dòng. Trả về (tên tệp, cột, dòng).
"""

import re
import datetime

# Một bộ chip ngày cho mọi màn. Khoá rỗng là "không lọc ngày".
KY_NGAY = (
	("", "Mọi ngày"),
	("hom_nay", "Hôm nay"),
	("7_ngay", "7 ngày"),
	("thang_nay", "Tháng này"),
	("thang_truoc", "Tháng trước"),
	("tuy_chon", "Tuỳ chọn"),
)
KHOA_KY = tuple(k for k, _ in KY_NGAY)

# Tên màn -> "mô đun.hàm adapter". Thêm màn thì thêm MỘT dòng ở đây và viết
# adapter trong mô đun của màn. Ca kiểm `thu_cong_cu_ds_534` chốt mọi dòng
# trỏ tới hàm có thật.
MAN_XUAT = {
	"hang_tang": "vagabond.hang_tang.xuat_ds",
	"cong_no": "vagabond.cong_no.xuat_no",
	"tien_da_ve": "vagabond.cong_no.xuat_tien_da_ve",
}

KIEU_COT = ("chu", "tien", "so", "ngay")


def _ngay(v):
	"""Chuỗi hoặc date ra date; không đọc được thì None. THUẦN."""
	if v is None or v == "":
		return None
	if isinstance(v, datetime.datetime):
		return v.date()
	if isinstance(v, datetime.date):
		return v
	try:
		n = [int(x) for x in str(v).strip()[:10].split("-")]
		return datetime.date(n[0], n[1], n[2])
	except (ValueError, IndexError):
		return None


def khoang_ky(ky, hom_nay, tu=None, den=None):
	"""Chip ngày ra khoảng (từ, đến), hai đầu đều TÍNH. THUẦN.

	Trả (None, None) khi không lọc ngày. Khoá lạ cũng coi như không lọc,
	chứ không ném lỗi: một chip gửi sai tên không đáng làm trắng màn.

	"Tuỳ chọn" nhận hai ô ngày người dùng gõ. Gõ ngược thứ tự thì đảo lại,
	thiếu một đầu thì đầu đó để trống.
	"""
	ky = (ky or "").strip()
	hn = _ngay(hom_nay)
	if ky not in KHOA_KY or not ky or hn is None:
		return (None, None)
	if ky == "hom_nay":
		return (hn.isoformat(), hn.isoformat())
	if ky == "7_ngay":
		return ((hn - datetime.timedelta(days=6)).isoformat(), hn.isoformat())
	if ky == "thang_nay":
		return (hn.replace(day=1).isoformat(), hn.isoformat())
	if ky == "thang_truoc":
		dau_thang_nay = hn.replace(day=1)
		cuoi = dau_thang_nay - datetime.timedelta(days=1)
		return (cuoi.replace(day=1).isoformat(), cuoi.isoformat())
	# tuy_chon
	a, b = _ngay(tu), _ngay(den)
	if a and b and a > b:
		a, b = b, a
	return (a.isoformat() if a else None, b.isoformat() if b else None)


def trong_khoang(ngay, tu, den):
	"""Ngày này có nằm trong khoảng không, hai đầu tính. THUẦN."""
	if not tu and not den:
		return True
	n = _ngay(ngay)
	if n is None:
		return False
	if tu and n < _ngay(tu):
		return False
	if den and n > _ngay(den):
		return False
	return True


_SO_HOAC_DIEN_THOAI = re.compile(r"^[+-]?[0-9][0-9 .,()/-]*$")


def chu_an_toan(v):
	"""Ô chữ đưa vào Excel không được thành công thức. THUẦN.

	Codex #382 vòng 7: tên khách, lý do tặng, mã đơn đến từ dữ liệu khách.
	Bộ ghi xlsxwriter của Frappe (v16.27.1, xlsxwriter 3.2.9) ghi chuỗi bắt
	đầu bằng "=" và chuỗi dạng "{=...}" thành CÔNG THỨC, kế toán mở tệp là
	Excel chạy. Thêm dấu nháy đơn phía trước cho mọi chuỗi mở đầu bằng ký tự
	công thức (=, +, -, @, tab, xuống dòng) hoặc có dạng {...}; riêng số và
	số điện thoại như "+84 90 123 4567", "-150000" giữ nguyên cho dễ đọc.
	"""
	s = "" if v is None else str(v)
	if not s:
		return s
	if s[0] in "\t\r\n":
		return "'" + s
	if s[0] == "{" and s.endswith("}"):
		return "'" + s
	if s[0] in "=@":
		return "'" + s
	if s[0] in "+-" and not _SO_HOAC_DIEN_THOAI.match(s):
		return "'" + s
	return s


def _o(kieu, v):
	if kieu in ("tien", "so"):
		try:
			x = float(v or 0)
		except (TypeError, ValueError):
			return 0
		return int(x) if x == int(x) else x
	if kieu == "ngay":
		n = _ngay(v)
		return n.strftime("%d/%m/%Y") if n else ""
	if v is None:
		return ""
	return chu_an_toan(v)


def dung_bang(cot, dong):
	"""Cột khai báo + dòng dữ liệu ra bảng hai chiều, hàng đầu là tiêu đề. THUẦN.

	`cot` là list dict {k, nhan, kieu}; kiểu lạ coi là chữ. Dòng thiếu khoá
	thì ô trống chứ không nổ: một dòng thiếu dữ liệu không đáng làm hỏng cả
	tệp của kế toán.
	"""
	cot = [c for c in (cot or []) if isinstance(c, dict) and c.get("k")]
	bang = [[c.get("nhan") or c["k"] for c in cot]]
	for d in dong or []:
		d = d or {}
		bang.append([_o(c.get("kieu") if c.get("kieu") in KIEU_COT else "chu", d.get(c["k"])) for c in cot])
	return bang


def ten_tep(goc, hom_nay):
	"""Tên tệp Excel an toàn cho điện thoại. THUẦN."""
	sach = "".join(ch if (ch.isalnum() or ch in "-_") else "-" for ch in str(goc or "danh-sach"))
	while "--" in sach:
		sach = sach.replace("--", "-")
	n = _ngay(hom_nay)
	return "%s-%s.xlsx" % (sach.strip("-") or "danh-sach", n.isoformat() if n else "")


# ------------------------------------------------------- phần cần Frappe

import frappe  # noqa: E402


@frappe.whitelist(methods=["POST"])
def xuat_excel(man=None, loc=None):
	"""Xuất đúng tập đang lọc trên màn ra .xlsx, ĐỦ dòng (không cắt 200/500).

	Quyền: do adapter của từng màn tự kiểm, bằng chính cổng quyền của màn.
	Cửa này không tự cấp quyền đọc nào thêm.
	"""
	man = (man or "").strip()
	duong = MAN_XUAT.get(man)
	if not duong:
		frappe.throw("Màn này chưa khai xuất Excel.")
	if isinstance(loc, str):
		loc = frappe.parse_json(loc or "{}")
	loc = loc if isinstance(loc, dict) else {}
	mo_dun, ham = duong.rsplit(".", 1)
	adapter = getattr(frappe.get_module(mo_dun), ham)
	ten, cot, dong = adapter(**loc)
	from frappe.utils import nowdate
	from frappe.utils.xlsxutils import make_xlsx
	import base64

	tep = make_xlsx(dung_bang(cot, dong), (ten or "Danh sach")[:30])
	return {
		"ten_file": ten_tep(ten, nowdate()),
		"b64": base64.b64encode(tep.getvalue()).decode(),
		"so_dong": len(dong or []),
	}

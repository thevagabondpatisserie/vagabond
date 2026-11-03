# -*- coding: utf-8 -*-
"""Thanh toán thẻ qua cổng OnePay cho phiếu đề nghị thanh toán (v633).

Anh Việt 03/11/2026: phiếu đề nghị thanh toán (công nợ khách sỉ) in thêm cách
trả bằng THẺ qua OnePay, khách tự chọn chuyển khoản hay thẻ. OnePay báo thành
công là GHI SỔ NGAY phiếu thu (không chờ đính bảng kê); tiền thẻ vào cùng tài
khoản phương thức "OnePay" đang dùng (11211 MB Bank), phí thẻ ghi khi đối soát
bảng kê OnePay như bill thẻ hiện nay.

Tài khoản tích hợp do OnePay cấp (merchant VAGABONDWEB, thư 04/08/2026): địa
chỉ cổng, Merchant ID, Access Code, Hash code (SECURE_SECRET); mật khẩu tra cứu
gửi thư sau. Anh dán ở Cài đặt lõi và API, mục "Thanh toán thẻ OnePay". Mã
nguồn KHÔNG chứa khoá nào.

VÌ SAO MÃ QR TRÊN PHIẾU KHÔNG PHẢI LINK ONEPAY
=============================================
Mỗi link OnePay mang một mã giao dịch (vpc_MerchTxnRef), trả một lần là xong,
còn tờ phiếu khách giữ nhiều ngày và có thể trả một phần. Nên QR trỏ về trang
của tiệm `/tra-the/<mã phiếu>?k=<khoá>`: trang đọc SỐ CÒN PHẢI TRẢ lúc mở, khách
bấm "Thanh toán bằng thẻ" thì máy mới tạo một giao dịch OnePay mới. Khoá `k`
là HMAC của mã phiếu bằng khoá mã hoá của site: không lưu, không đoán được.

CHỮ KÝ (tài liệu tích hợp OnePay)
=================================
HMAC-SHA256 trên chuỗi "k=v&k=v" các tham số bắt đầu bằng `vpc_` hoặc `user_`,
xếp theo tên, bỏ ô rỗng và bỏ chính vpc_SecureHash, vpc_SecureHashType. Khoá
là Hash code dạng chuỗi hex, giải hex ra byte trước khi ký. Kết quả hex IN HOA.
Số tiền vpc_Amount nhân 100. Giao dịch thành công khi vpc_TxnResponseCode = "0"
VÀ chữ ký đúng. IPN trả "responsecode=1&desc=confirm-success".
"""

import hashlib
import hmac
import json
import re
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

PT = "OnePay"
DUONG_TRANG = "/tra-the"
DAP_IPN_OK = "responsecode=1&desc=confirm-success"
DAP_IPN_SAI = "responsecode=0&desc=confirm-fail"
DAP_IPN_CHUA_KHOA = "responsecode=0&desc=chua-khai-khoa"
TIEN_TOI_THIEU = 10000
SO_LAN_TOI_DA = 30
TRANG_QUET = 200
RE_MA_GD = re.compile(r"^(DNTT[0-9]{9}|CN[A-Z0-9]{6})-([0-9]{1,3})$")

# Mã kết quả hay gặp của OnePay -> câu cho khách. Mã lạ thì câu chung.
CAU_MA = {
	"0": "Giao dịch thành công.",
	"1": "Ngân hàng từ chối giao dịch.",
	"3": "Thẻ không được chấp nhận.",
	"4": "Thẻ hết hạn.",
	"5": "Thẻ không đủ số dư hoặc hạn mức.",
	"6": "Ngân hàng chưa trả lời, giao dịch chưa thực hiện.",
	"7": "Thông tin thẻ chưa đúng.",
	"8": "Thẻ chưa đăng ký thanh toán trực tuyến.",
	"9": "Thẻ không đủ số dư hoặc hạn mức.",
	"10": "Thẻ đã hết hạn hoặc bị khoá.",
	"11": "Thẻ chưa đăng ký thanh toán trực tuyến.",
	"12": "Thẻ hết hạn hoặc bị khoá.",
	"13": "Số tiền vượt hạn mức thanh toán của thẻ.",
	"21": "Tài khoản không đủ số dư.",
	"22": "Thông tin tài khoản chưa đúng.",
	"23": "Tài khoản bị khoá.",
	"24": "Thông tin thẻ chưa đúng.",
	"25": "Mã OTP chưa đúng.",
	"253": "Hết thời gian thanh toán.",
	"99": "Quý khách đã huỷ giao dịch.",
	"B": "Ngân hàng chưa xác thực được thẻ.",
	"F": "Xác thực 3D Secure không thành công.",
}


def cau_ma(ma):
	"""Câu cho khách theo mã kết quả OnePay. THUẦN."""
	ma = str(ma if ma is not None else "").strip()
	return CAU_MA.get(ma) or "Giao dịch chưa thành công (mã %s). Quý khách thử lại hoặc chọn chuyển khoản." % (ma or "?")


def chuan_cong(url):
	"""Ô cài đặt người dán tay: chịu khoảng trắng, thiếu https, có sẵn dấu ? hay
	tham số thừa. Trả địa chỉ cổng sạch (không tham số), rỗng nếu không dùng
	được. THUẦN."""
	s = str(url or "").strip().strip("'\"").strip()
	if not s:
		return ""
	if "://" not in s:
		s = "https://" + s
	p = urlsplit(s)
	if not p.netloc or p.scheme not in ("https", "http"):
		return ""
	duong = p.path or "/"
	return urlunsplit(("https", p.netloc.lower(), duong, "", ""))


DUONG_TRA_CUU = "/msp/api/v1/vpc/invoices/queries"


def cong_tra_cuu(cong):
	"""Địa chỉ QueryDR: cùng máy chủ với cổng thanh toán, đường
	/msp/api/v1/vpc/invoices/queries (OnePay cấp cho VAGABONDWEB, anh Việt
	03/11/2026). Cổng thử mtf.onepay.vn thì tra cứu ở mtf.onepay.vn. THUẦN.
	v633 đoán .../Vpcdps.op theo tài liệu nội địa cũ: sai với cổng paygate."""
	c = chuan_cong(cong)
	if not c:
		return ""
	p = urlsplit(c)
	return urlunsplit((p.scheme, p.netloc, DUONG_TRA_CUU, "", ""))


def khoa_byte(hash_code):
	"""Hash code OnePay là chuỗi hex; giải hex. Chuỗi không phải hex thì dùng
	nguyên văn (một số tài khoản cũ). THUẦN."""
	s = str(hash_code or "").strip()
	if not s:
		raise ValueError("Chưa khai Hash code (SECURE_SECRET) của OnePay.")
	if len(s) % 2 == 0 and re.fullmatch(r"[0-9A-Fa-f]+", s):
		return bytes.fromhex(s)
	return s.encode("utf-8")


def chuoi_ky(tham_so):
	"""Chuỗi đem ký: vpc_ và user_, xếp theo tên, bỏ ô rỗng và ô chữ ký. THUẦN."""
	cap = []
	for k in sorted(tham_so or {}):
		if not (k.startswith("vpc_") or k.startswith("user_")):
			continue
		if k in ("vpc_SecureHash", "vpc_SecureHashType"):
			continue
		v = tham_so[k]
		if v is None or str(v) == "":
			continue
		cap.append("%s=%s" % (k, v))
	return "&".join(cap)


def ky(tham_so, hash_code):
	"""Chữ ký HMAC-SHA256 hex IN HOA. THUẦN."""
	return hmac.new(khoa_byte(hash_code), chuoi_ky(tham_so).encode("utf-8"), hashlib.sha256).hexdigest().upper()


def dung_chu_ky(tham_so, hash_code):
	"""Chữ ký OnePay gửi về có khớp không. So bằng phép so thời gian hằng. THUẦN."""
	gui = str((tham_so or {}).get("vpc_SecureHash") or "").strip().upper()
	if not gui:
		return False
	try:
		return hmac.compare_digest(gui, ky(tham_so, hash_code))
	except ValueError:
		return False


def so_tien_vpc(so_tien):
	"""Đồng -> vpc_Amount (nhân 100, số nguyên). Tiền Việt không có số lẻ. THUẦN."""
	return str(int(round(float(so_tien or 0))) * 100)


def tien_tu_vpc(v):
	"""vpc_Amount -> đồng. THUẦN."""
	try:
		return float(int(str(v or "0").strip())) / 100.0
	except (TypeError, ValueError):
		return 0.0


def ma_gd(ma_phieu, lan):
	"""Mã giao dịch gửi OnePay: mã phiếu bỏ gạch, nối số lần. Ví dụ
	DNTT2611000002-3. Khớp RE_MA_GD. THUẦN."""
	return "%s-%d" % (re.sub(r"[^A-Z0-9]", "", str(ma_phieu or "").upper()), int(lan))


def ma_phieu_cua_gd(ma):
	"""Tách mã phiếu (không gạch) từ mã giao dịch. Sai dạng thì rỗng. THUẦN."""
	m = RE_MA_GD.match(str(ma or "").strip())
	return m.group(1) if m else ""


def tham_so_tra(c, ma, so_tien, thong_tin, url_ve, ip, link_lai, tieu_de="The Vagabond Patisserie"):
	"""Bộ tham số một lần trả, đã ký. `c` là dict cấu hình đã đọc
	(cong, merchant, access_code, hash_code). THUẦN."""
	if not (c.get("cong") and c.get("merchant") and c.get("access_code") and c.get("hash_code")):
		raise ValueError("Chưa khai đủ cổng, Merchant ID, Access Code, Hash code của OnePay.")
	ts = {
		"vpc_Version": "2",
		"vpc_Currency": "VND",
		"vpc_Command": "pay",
		"vpc_AccessCode": c["access_code"],
		"vpc_Merchant": c["merchant"],
		"vpc_Locale": "vn",
		"vpc_ReturnURL": url_ve,
		"vpc_MerchTxnRef": ma,
		"vpc_OrderInfo": str(thong_tin or ma)[:32],
		"vpc_Amount": so_tien_vpc(so_tien),
		"vpc_TicketNo": str(ip or "127.0.0.1")[:45],
		"AgainLink": link_lai,
		"Title": tieu_de,
	}
	ts["vpc_SecureHash"] = ky(ts, c["hash_code"])
	return ts


def url_tra(c, ts):
	"""Địa chỉ chuyển khách sang OnePay. THUẦN."""
	return chuan_cong(c.get("cong")) + "?" + urlencode(ts)


def doc_ket_qua(tham_so, hash_code, tin_cay=False):
	"""Đọc kết quả OnePay gửi về (trang về hay IPN). THUẦN.

	Trả dict: hop_le (chữ ký đúng), thanh_cong (hợp lệ VÀ mã 0), ma (mã giao
	dịch của tiệm), so_tien (đồng), ma_onepay, the, ma_kq, cau.

	tin_cay=True chỉ dành cho phản hồi tra cứu do CHÍNH máy chủ tiệm gọi tới
	OnePay qua HTTPS: tài liệu QueryDR không hứa phản hồi có chữ ký, nên không
	có chữ ký thì tin kênh; CÓ chữ ký thì vẫn phải đúng."""
	ts = dict(tham_so or {})
	if tin_cay and not str(ts.get("vpc_SecureHash") or "").strip():
		hop_le = True
	else:
		hop_le = dung_chu_ky(ts, hash_code)
	ma_kq = str(ts.get("vpc_TxnResponseCode", "")).strip()
	return {
		"hop_le": hop_le,
		"thanh_cong": bool(hop_le and ma_kq == "0"),
		"ma": str(ts.get("vpc_MerchTxnRef") or "").strip(),
		"so_tien": tien_tu_vpc(ts.get("vpc_Amount")),
		"ma_onepay": str(ts.get("vpc_TransactionNo") or "").strip(),
		"the": str(ts.get("vpc_Card") or "").strip(),
		"so_the": str(ts.get("vpc_CardNum") or "").strip(),
		"ma_kq": ma_kq,
		"cau": cau_ma(ma_kq),
	}


def doc_tra_cuu(chuoi):
	"""Phản hồi QueryDR -> dict. Chịu cả chuỗi k=v&k=v lẫn JSON (phẳng hoặc bọc
	trong một khoá). Không đọc được thì dict rỗng. THUẦN."""
	s = str(chuoi or "").strip()
	if s.startswith("{"):
		try:
			d = json.loads(s)
		except ValueError:
			return {}
		if isinstance(d, dict) and not any(str(k).startswith("vpc_") for k in d):
			for v in d.values():
				if isinstance(v, dict) and any(str(k).startswith("vpc_") for k in v):
					d = v
					break
		return {str(k): "" if v is None else str(v) for k, v in d.items()} if isinstance(d, dict) else {}
	if "=" not in s or s.startswith("<"):
		return {}
	return dict(parse_qsl(s, keep_blank_values=True))


def tom_tat_phan_hoi(chuoi, toi_da=300):
	"""Cắt ngắn phản hồi lạ để ghi Error Log, che mọi ô mật khẩu, người dùng,
	chữ ký. THUẦN."""
	s = re.sub(r"(?i)(vpc_(?:password|user|securehash|accesscode)\W{0,3}[=:]\W{0,2})[^&\s\"',}]*", r"\1***", str(chuoi or ""))
	return s[:toi_da]


def tham_so_tra_cuu(c, ma):
	"""Tham số QueryDR, đã ký. THUẦN."""
	if not (c.get("merchant") and c.get("access_code") and c.get("hash_code") and c.get("query_user") and c.get("query_password")):
		raise ValueError("Chưa khai đủ tài khoản tra cứu giao dịch OnePay.")
	ts = {
		"vpc_Command": "queryDR",
		"vpc_Version": "2",
		"vpc_MerchTxnRef": ma,
		"vpc_Merchant": c["merchant"],
		"vpc_AccessCode": c["access_code"],
		"vpc_User": c["query_user"],
		"vpc_Password": c["query_password"],
	}
	ts["vpc_SecureHash"] = ky(ts, c["hash_code"])
	return ts


def khoa_trang(bi_mat, ma_phieu):
	"""Khoá riêng của trang trả thẻ một phiếu: HMAC mã phiếu bằng bí mật của
	site, 16 ký tự. Không lưu ở đâu, tính lại được, không đoán được. THUẦN."""
	if not bi_mat:
		raise ValueError("Site chưa có khoá mã hoá.")
	return hmac.new(str(bi_mat).encode("utf-8"), ("tra-the:" + str(ma_phieu or "")).encode("utf-8"),
		hashlib.sha256).hexdigest()[:16]


def duong_trang(ma_phieu, khoa):
	"""Đường tương đối của trang trả thẻ, in trên phiếu. THUẦN."""
	return "%s/%s?k=%s" % (DUONG_TRANG, re.sub(r"[^A-Z0-9]", "", str(ma_phieu or "").upper()), khoa)


def doc_nhat_ky(chuoi):
	"""Nhật ký giao dịch thẻ cất trên phiếu (JSON list). Hỏng thì rỗng. THUẦN."""
	try:
		v = json.loads(chuoi or "[]")
		return v if isinstance(v, list) else []
	except (TypeError, ValueError):
		return []


def lan_tiep(nhat_ky):
	"""Số lần tiếp theo cho mã giao dịch mới. THUẦN."""
	so = 0
	for g in nhat_ky or []:
		m = RE_MA_GD.match(str(g.get("ma") or ""))
		if m:
			so = max(so, int(m.group(2)))
	return so + 1


def tim_gd(nhat_ky, ma):
	for g in nhat_ky or []:
		if g.get("ma") == ma:
			return g
	return None


def xet_ghi_nhan(gd, kq, con_phai_thu):
	"""Kết quả OnePay (đã đọc bằng doc_ket_qua) có được ghi tiền không. THUẦN.

	Trả (ghi, so_tien_ghi, ly_do). Không ghi khi: chữ ký sai, không thành công,
	giao dịch lạ (không có trong nhật ký phiếu), đã ghi rồi, số tiền khác số
	đã gửi OnePay. Khách trả trùng (hai lần thanh toán cùng lúc) thì chỉ ghi
	phần còn phải thu, phần dư báo kế toán hoàn."""
	if not kq.get("hop_le"):
		return (False, 0.0, "chu_ky_sai")
	if not kq.get("thanh_cong"):
		return (False, 0.0, "khong_thanh_cong")
	if not gd:
		return (False, 0.0, "gd_la")
	if gd.get("trang_thai") == "da_ghi":
		return (False, 0.0, "da_ghi_roi")
	if abs(float(gd.get("so_tien") or 0) - float(kq.get("so_tien") or 0)) > 0.5:
		return (False, 0.0, "lech_so_tien")
	ghi = min(float(kq.get("so_tien") or 0), max(0.0, float(con_phai_thu or 0)))
	return (True, ghi, "du" if ghi + 0.5 < float(kq.get("so_tien") or 0) else "")


def doi_chieu_ghi(so_onepay, so_du_kien, da_ghi_thuc):
	"""Số ghi nhận cuối cùng là số phiếu thu ĐÃ GHI SỔ thật (Codex #534): hoá
	đơn bị trả bớt ở chỗ khác sau khi tạo giao dịch thì phép lập phiếu thu chỉ
	lập tới dư nợ còn lại. Phần OnePay đã thu mà chưa ghi được là tiền dư phải
	báo kế toán. `lech` = ghi ít hơn dự kiến. THUẦN."""
	so_onepay = float(so_onepay or 0)
	ghi = max(0.0, float(da_ghi_thuc or 0))
	du = so_onepay - ghi
	return {"so_ghi": ghi, "du": du if du > 0.5 else 0.0, "lech": float(so_du_kien or 0) - ghi > 0.5}


def phan_loai_cho(nhat_ky, tu, den):
	"""Giao dịch "chờ" nào cần hỏi OnePay (tạo trong [tu, den]) và nào đã quá
	hạn (tạo trước tu) để cho hết hạn, khỏi chiếm lượt quét mãi. THUẦN."""
	hoi, het = [], []
	for g in nhat_ky or []:
		if g.get("trang_thai") != "cho":
			continue
		luc = str(g.get("tao_luc") or "")
		if luc < tu:
			het.append(g.get("ma"))
		elif luc <= den:
			hoi.append(g.get("ma"))
	return hoi, het


def cach_tra(phieu):
	"""Trang /tra-the hiện gì (Codex #534). Chỉ báo "đã thanh toán đủ" khi hết
	nợ thật; dưới mức tối thiểu của thẻ thì chỉ ẩn nút thẻ, vẫn hiện chuyển
	khoản. THUẦN."""
	con = float((phieu or {}).get("con") or 0)
	huy = bool((phieu or {}).get("huy"))
	da_du = not huy and con < 1
	return {"da_du": da_du, "tra_the": bool(not huy and not da_du and (phieu or {}).get("dung_duoc") and con >= TIEN_TOI_THIEU),
		"con_nho": not huy and not da_du and con < TIEN_TOI_THIEU}


# ------------------------------------------------------------- chạm Frappe

import frappe  # noqa: E402
from frappe.utils import flt  # noqa: E402

try:
	import requests  # noqa: E402
except ImportError:  # CI tay không
	requests = None

try:
	from frappe.rate_limiter import rate_limit  # noqa: E402
except ImportError:  # Frappe giả của bộ kiểm tầng khung
	def rate_limit(**_kw):
		return lambda f: f

CN = "Vagabond Cong No"


def cau_hinh():
	"""Đọc mục OnePay của Cài đặt. Khoá đọc bằng get_password, không ra màn."""
	from vagabond.lib import cfg, key

	c = cfg()
	return {
		"bat": int(c.get("onepay_bat") or 0),
		"cong": chuan_cong(c.get("onepay_cong")),
		"merchant": str(c.get("onepay_merchant") or "").strip(),
		"access_code": key(c, "onepay_access_code"),
		"hash_code": key(c, "onepay_hash_code"),
		"query_user": str(c.get("onepay_query_user") or "").strip(),
		"query_password": key(c, "onepay_query_password"),
	}


def dung_duoc(c=None):
	"""Bật và đủ bốn ô thì in mã trả thẻ lên phiếu."""
	try:
		c = c or cau_hinh()
	except Exception:
		# Đọc cài đặt hỏng (chưa migrate, khoá giải mã lỗi) thì phiếu vẫn in được,
		# chỉ không có ô trả thẻ.
		return False
	return bool(c["bat"] and c["cong"] and c["merchant"] and c["access_code"] and c["hash_code"])


def _bi_mat():
	from frappe.utils.password import get_encryption_key

	return get_encryption_key()


def khoa_phieu(ma_phieu):
	return khoa_trang(_bi_mat(), ma_phieu)


def link_phieu(ma_phieu):
	"""Địa chỉ tuyệt đối trên miền khách, in thành mã QR trên phiếu."""
	from vagabond.ten_mien import link_khach

	return link_khach(duong_trang(ma_phieu, khoa_phieu(ma_phieu)))


def _tim_phieu(ma, k):
	"""Mã trên đường dẫn (bỏ gạch) + khoá -> tên phiếu. Sai khoá thì như không có."""
	ma = re.sub(r"[^A-Z0-9]", "", str(ma or "").upper())
	if not ma or not isinstance(k, str) or not re.fullmatch(r"[0-9a-f]{16}", k):
		return None
	if m := re.fullmatch(r"DNTT(\d{2})(\d{2})(\d{5})", ma):
		ma_day = "DNTT-%s-%s-%s" % m.groups()
	else:
		ma_day = ma
	ten = frappe.db.get_value(CN, {"ma_phieu": ma_day}, "name") or frappe.db.get_value(CN, {"ma_phieu": ma}, "name")
	if not ten:
		return None
	ma_luu = frappe.db.get_value(CN, ten, "ma_phieu") or ""
	if not hmac.compare_digest(khoa_phieu(ma_luu), k):
		return None
	return ten


def thong_tin_trang(ma, k):
	"""Dữ liệu cho trang /tra-the. Không lộ gì khi khoá sai."""
	ten = _tim_phieu(ma, k)
	if not ten:
		return None
	from vagabond.cong_no import con_phai_thu_phieu

	d = frappe.db.get_value(CN, ten, ["name", "ma_phieu", "ten_khach", "khach", "trang_thai", "tong_tien"], as_dict=True)
	con = con_phai_thu_phieu(ten)
	return {"ten": d.name, "ma_phieu": d.ma_phieu, "khach": d.ten_khach or d.khach, "tong": flt(d.tong_tien),
		"con": con, "huy": d.trang_thai == "Huy", "dung_duoc": dung_duoc()}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=600)
def tao_gd(ma, k):
	"""Khách bấm "Thanh toán bằng thẻ": tạo một giao dịch mới cho SỐ CÒN PHẢI
	TRẢ đọc ở máy chủ, trả địa chỉ OnePay để trình duyệt chuyển sang."""
	ten = _tim_phieu(ma, k)
	if not ten:
		frappe.throw("Không tìm thấy phiếu thanh toán.")
	c = cau_hinh()
	if not dung_duoc(c):
		frappe.throw("Thanh toán thẻ đang tạm ngưng. Quý khách vui lòng chuyển khoản theo phiếu.")
	from vagabond.cong_no import con_phai_thu_phieu

	doc = frappe.get_doc(CN, ten, for_update=True)
	if doc.trang_thai == "Huy":
		frappe.throw("Phiếu này đã huỷ. Quý khách liên hệ The Vagabond để nhận phiếu mới.")
	con = con_phai_thu_phieu(ten)
	if con < 1:
		frappe.throw("Phiếu này đã được thanh toán đủ. Cảm ơn quý khách.")
	if con < TIEN_TOI_THIEU:
		frappe.throw("Số còn lại dưới 10.000 đ nên không trả bằng thẻ được. Quý khách vui lòng chuyển khoản theo phiếu.")
	nk = doc_nhat_ky(doc.get("onepay_gd"))
	lan = lan_tiep(nk)
	if lan > SO_LAN_TOI_DA:
		frappe.throw("Phiếu này đã thử thanh toán thẻ quá nhiều lần. Quý khách liên hệ The Vagabond.")
	ma_gd_moi = ma_gd(doc.ma_phieu, lan)
	duong = link_phieu(doc.ma_phieu)
	ts = tham_so_tra(c, ma_gd_moi, con, doc.ma_phieu, duong + "&ve=1", getattr(frappe.local, "request_ip", None), duong)
	nk.append({"ma": ma_gd_moi, "so_tien": con, "tao_luc": str(frappe.utils.now_datetime())[:19], "trang_thai": "cho"})
	frappe.db.set_value(CN, ten, "onepay_gd", json.dumps(nk, ensure_ascii=False), update_modified=False)
	frappe.db.commit()
	return {"url": url_tra(c, ts)}


def ghi_nhan(tham_so, nguon, tin_cay=False):
	"""Một kết quả OnePay (trang về, IPN, tra cứu). Lặp lại bao nhiêu lần cũng
	chỉ ghi tiền một lần. Trả dict kết quả cho người gọi. tin_cay: xem
	doc_ket_qua, CHỈ quet() được truyền True."""
	c = cau_hinh()
	if not c["hash_code"]:
		return {"ok": 0, "ly_do": "chua_khai_khoa"}
	kq = doc_ket_qua(tham_so, c["hash_code"], tin_cay=tin_cay)
	if not kq["hop_le"]:
		return {"ok": 0, "ly_do": "chu_ky_sai", "kq": kq}
	ma_ngan = ma_phieu_cua_gd(kq["ma"])
	if not ma_ngan:
		return {"ok": 1, "ly_do": "gd_la", "kq": kq}
	m = re.fullmatch(r"DNTT(\d{2})(\d{2})(\d{5})", ma_ngan)
	ma_day = "DNTT-%s-%s-%s" % m.groups() if m else ma_ngan
	ten = frappe.db.get_value(CN, {"ma_phieu": ma_day}, "name")
	if not ten:
		return {"ok": 1, "ly_do": "gd_la", "kq": kq}
	from vagabond.cong_no import ghi_nhan_the

	return ghi_nhan_the(ten, kq, nguon)


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def ipn(**tham_so):
	"""OnePay gọi về sau mỗi giao dịch. Trả chuỗi OnePay đòi, không bọc JSON."""
	from werkzeug.wrappers import Response

	ts = {k: v for k, v in (tham_so or {}).items() if k != "cmd"}
	try:
		r = ghi_nhan(ts, "ipn")
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "onepay: IPN lỗi")
		# Không trả xác nhận: OnePay gọi lại sau, lần sau ghi tiếp.
		return Response("responsecode=0&desc=loi-he-thong", mimetype="text/plain")
	if r.get("ly_do") == "chua_khai_khoa":
		# v634: chưa dán khoá thì KHÔNG xác nhận, OnePay gọi lại sau khi dán.
		return Response(DAP_IPN_CHUA_KHOA, mimetype="text/plain")
	return Response(DAP_IPN_OK if r.get("ly_do") != "chu_ky_sai" else DAP_IPN_SAI, mimetype="text/plain")


def tra_cuu(ma):
	"""Hỏi OnePay một giao dịch (QueryDR). Trả dict tham số OnePay trả về.

	Gửi POST (biểu mẫu); phản hồi không có vpc_DRExists thì thử lại bằng GET.
	Cả hai không đọc được thì NÉM kèm phản hồi đã che, để Error Log cho thấy
	ngay địa chỉ hay cách gọi sai, không im lặng coi như "không có giao dịch"."""
	c = cau_hinh()
	if requests is None:
		raise RuntimeError("Thiếu thư viện requests.")
	dia_chi = cong_tra_cuu(c["cong"])
	ts = tham_so_tra_cuu(c, ma)
	vet = []
	for cach in ("post", "get"):
		try:
			if cach == "post":
				r = requests.post(dia_chi, data=ts, timeout=20)
			else:
				r = requests.get(dia_chi, params=ts, timeout=20)
		except Exception as e:
			vet.append("%s: %s" % (cach, type(e).__name__))
			continue
		kq = doc_tra_cuu(r.text)
		if "vpc_DRExists" in kq:
			return kq
		vet.append("%s %s: %s" % (cach, r.status_code, tom_tat_phan_hoi(r.text)))
	raise ValueError("Phản hồi tra cứu OnePay không đọc được (%s). %s" % (dia_chi, " | ".join(vet)))


def quet():
	"""Mỗi 15 phút: giao dịch tạo quá 15 phút mà chưa có kết quả thì hỏi OnePay.
	OnePay chỉ cho tra sau 15 phút; quá 2 ngày thì cho hết hạn (Codex #534:
	trước đây chúng nằm "chờ" mãi, chiếm hết 200 lượt quét đầu nên giao dịch
	mới phía sau không bao giờ được hỏi). Đi hết các phiếu theo trang."""
	c = cau_hinh()
	if not (dung_duoc(c) and c["query_user"] and c["query_password"]):
		return
	from datetime import timedelta

	bay_gio = frappe.utils.now_datetime()
	tu = str(bay_gio - timedelta(days=2))[:19]
	den = str(bay_gio - timedelta(minutes=15))[:19]
	sau = ""
	while True:
		trang = frappe.get_all(CN, filters={"onepay_gd": ["like", "%\"cho\"%"], "trang_thai": ["!=", "Huy"],
			"name": [">", sau]}, pluck="name", order_by="name asc", limit_page_length=TRANG_QUET)
		for ten in trang:
			hoi, het = phan_loai_cho(doc_nhat_ky(frappe.db.get_value(CN, ten, "onepay_gd")), tu, den)
			if het:
				_het_han(ten, het)
			for ma in hoi:
				try:
					ts = tra_cuu(ma)
					if str(ts.get("vpc_DRExists") or "").upper() == "Y":
						# Phản hồi phải nói đúng giao dịch mình hỏi.
						if str(ts.get("vpc_MerchTxnRef") or ma).strip() != ma:
							raise ValueError("OnePay trả kết quả của giao dịch khác: hỏi %s, nhận %s."
								% (ma, ts.get("vpc_MerchTxnRef")))
						ghi_nhan(dict(ts, vpc_MerchTxnRef=ma), "tra_cuu", tin_cay=True)
					frappe.db.commit()
				except Exception:
					frappe.db.rollback()
					frappe.log_error(frappe.get_traceback(), "onepay: tra cứu %s" % ma)
		if len(trang) < TRANG_QUET:
			break
		sau = trang[-1]


def _het_han(ten, cac_ma):
	"""Đổi giao dịch "chờ" quá hạn sang "het_han", đọc lại nhật ký trong khoá
	hàng phiếu. Giao dịch hết hạn vẫn ghi được nếu OnePay báo thành công muộn
	(xet_ghi_nhan chỉ chặn "da_ghi")."""
	try:
		nk = doc_nhat_ky(frappe.db.get_value(CN, ten, "onepay_gd", for_update=True))
		doi = 0
		for g in nk:
			if g.get("ma") in cac_ma and g.get("trang_thai") == "cho":
				g["trang_thai"] = "het_han"
				doi += 1
		if doi:
			frappe.db.set_value(CN, ten, "onepay_gd", json.dumps(nk, ensure_ascii=False), update_modified=False)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "onepay: cho hết hạn %s" % ten)

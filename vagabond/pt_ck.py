# -*- coding: utf-8 -*-
"""Phương thức CHUYỂN KHOẢN và đường mở app ngân hàng (v678). THUẦN.

ANH VIỆT 20/11/2026
-------------------
*"Ở phần phương thức thanh toán này, ở tất cả các điểm bán em cho thêm một
phương thức chuyển khoản Shinhan nữa nhé, và dùng logo của ngân hàng Shinhan
vào đó vì có vài khách muốn chuyển vào đó, kết nối với luồng đối soát sepay
tự động."*

Trước bản này cả hệ so đúng chữ "Chuyển khoản" ở hơn chục chỗ (cửa ghi sổ,
màn bill, chốt ca, khớp theo số tiền...). Thêm một phương thức chuyển khoản
thứ hai mà để mỗi chỗ tự so là chỗ nào quên thì bill Shinhan ghi sổ không cần
tiền về, hoặc không bao giờ ghi sổ được. Nên gom về MỘT phép ở đây: `la_ck`.
Ca kiểm thu_shinhan_o2o_678 dò mã nguồn chốt không còn chỗ nào so chữ trần.

Tên hai phương thức bị khoá (pt_thanh_toan.TEN_KHOA): đổi tên là đối soát
SePay và tài khoản hạch toán mất dấu.

Hai tài khoản, hai tài khoản kế toán:
  - "Chuyển khoản": tài khoản ảo MB của từng điểm bán (tai_khoan.tk_cho),
    hạch toán 11211.
  - "Chuyển khoản - Shinhan": tài khoản Shinhan công ty, hạch toán theo dòng
    tài khoản của Hình thức thanh toán (11212). Mã QR lấy số tài khoản từ
    chính dòng đó, không chép số vào màn tính tiền.

Đường mở app ngân hàng (anh Việt 20/11/2026: *"khách nhấn vào nút chuyển khoản
thì sẽ cho chọn ngân hàng, rồi nó sẽ nhảy sang cái app ngân hàng ... Máy sẽ tự
điền số tiền, nội dung chuyển khoản, khách chỉ việc quét Face ID là xong"*):
dùng dịch vụ deeplink công khai của VietQR, dạng
    https://dl.vietqr.io/pay?app=<mã app>&ba=<số TK>@<mã NH>&am=<tiền>&tn=<nội dung>
(www.vietqr.io/danh-sach-api/deeplink-app-ngan-hang). Danh sách app và cờ tự
điền đọc từ api.vietqr.io/v2/ios-app-deeplinks ngày 20/11/2026: chỉ năm app
tự điền sẵn số tiền và nội dung; app khác chỉ mở app, nên trang khách chép
sẵn nội dung vào bộ nhớ tạm trước khi mở.
"""

from urllib.parse import quote

TEN_CK = "Chuyển khoản"
TEN_CK_SHINHAN = "Chuyển khoản - Shinhan"
# Mọi phương thức chuyển khoản đối soát bằng SePay. Thứ tự: MB trước.
DS_CK = (TEN_CK, TEN_CK_SHINHAN)

# Tài khoản Shinhan công ty (Bank Account "SHINHAN-700037279585", sổ cái 11212).
# Chỉ dùng để khai dòng tài khoản cho Hình thức thanh toán lúc nâng cấp, khi
# kế toán chưa tự khai; mã QR và hạch toán đọc từ dòng đã khai.
STK_SHINHAN = "700037279585"


def la_ck(pt):
	"""Phương thức này là chuyển khoản đối soát bằng SePay không."""
	return str(pt or "").strip() in DS_CK


# App ngân hàng cho trang khách. (mã app vietqr, tên hiện, tự điền).
# Năm app tự điền đứng đầu; còn lại theo độ phổ biến ở cửa hàng.
APP_NGAN_HANG = (
	("mb", "MB Bank", 1),
	("icb", "VietinBank", 1),
	("bidv", "BIDV", 1),
	("acb", "ACB", 1),
	("ocb", "OCB", 1),
	("vcb", "Vietcombank", 0),
	("tcb", "Techcombank", 0),
	("vpb", "VPBank", 0),
	("tpb", "TPBank", 0),
	("vba", "Agribank", 0),
	("hdb", "HDBank", 0),
	("shbvn", "Shinhan SOL", 0),
	("vib-2", "MyVIB", 0),
	("shb", "SHB SAHA", 0),
	("cake", "CAKE", 0),
	("timo", "Timo", 0),
)

# Mã ngân hàng nhận tiền trong tham số ba=<stk>@<mã> (chữ thường, theo bảng
# mã của vietqr). Khoá là mã viết tắt trong tai_khoan.NGAN_HANG.
MA_NH_VIETQR = {
	"MB": "mb", "VCB": "vcb", "ICB": "icb", "BIDV": "bidv", "VBA": "vba",
	"TCB": "tcb", "ACB": "acb", "VPB": "vpb", "TPB": "tpb", "STB": "stb",
	"HDB": "hdb", "SHB": "shb", "EIB": "eib", "VIB": "vib", "OCB": "ocb",
	"MSB": "msb", "SCB": "scb", "SHBVN": "shbvn", "LPB": "lpb", "SEAB": "seab",
}


def ma_nh_vietqr(ma):
	"""Mã ngân hàng cho tham số ba của deeplink. Rỗng khi không biết."""
	return MA_NH_VIETQR.get(str(ma or "").strip().upper(), "")


def link_app(app, stk, ma_nh, tien, noi_dung, ten=""):
	"""Đường dẫn mở app ngân hàng `app` với số tiền và nội dung điền sẵn.

	Rỗng khi thiếu số tài khoản hoặc mã ngân hàng: thà không hiện nút còn
	hơn mở app với tài khoản sai."""
	app = str(app or "").strip().lower()
	stk = str(stk or "").strip()
	ma_nh = str(ma_nh or "").strip().lower()
	if not (app and stk and ma_nh):
		return ""
	try:
		so = int(round(float(tien or 0)))
	except (TypeError, ValueError):
		so = 0
	if so <= 0:
		return ""
	ra = "https://dl.vietqr.io/pay?app=%s&ba=%s@%s&am=%d&tn=%s" % (
		quote(app, safe="-"), quote(stk, safe=""), quote(ma_nh, safe=""), so,
		quote(str(noi_dung or "").strip(), safe=""))
	if ten:
		ra += "&bn=" + quote(str(ten).strip(), safe="")
	return ra


def ck_cua_tk(ba, tk_shinhan):
	"""Phương thức chuyển khoản ứng với tài khoản ngân hàng tiền đã về.

	ba          Bank Account của dòng sao kê
	tk_shinhan  Bank Account đang khai cho "Chuyển khoản - Shinhan" (rỗng là
	            chưa khai)
	Tiền về Shinhan là phương thức Shinhan; về tài khoản khác là "Chuyển khoản"
	(tài khoản ảo MB của điểm và tài khoản chính MB đều hạch toán 11211)."""
	ba = str(ba or "").strip()
	if not ba:
		return ""
	if tk_shinhan and ba == str(tk_shinhan).strip():
		return TEN_CK_SHINHAN
	return TEN_CK


def soat_tk_ck(pt, gd, tk_shinhan, tach=None):
	"""Phương thức chuyển khoản trên bill có đúng ngân hàng tiền về không. THUẦN.

	pt          phương thức chính của bill
	gd          [(Bank Account, số tiền)] của các dòng sao kê bill đang gạch
	tk_shinhan  Bank Account của "Chuyển khoản - Shinhan" (rỗng là chưa khai)
	tach        {phương thức: tiền} của dòng thanh toán (thanh_toan_nhieu.tach_theo_pt),
	            rỗng khi bill không chia dòng

	Trả (loại, chi tiết):
	  ("", None)      khớp, hoặc không kết luận được (dòng thiếu Bank Account)
	  ("doi", pt)     tiền về MỘT ngân hàng khác phương thức đang ghi: đổi sang pt
	  ("nhieu", {pt: tiền})  Codex #597 vòng 1: tiền về nhiều ngân hàng mà dòng
	                  thanh toán không chia đúng số từng ngân hàng (trước đây cho qua)."""
	if not la_ck(pt):
		return "", None
	nhan = {}
	for ba, tien in gd or []:
		k = ck_cua_tk(ba, tk_shinhan)
		if not k:
			return "", None
		nhan[k] = nhan.get(k, 0) + float(tien or 0)
	if not nhan:
		return "", None
	ck = {p: float(t or 0) for p, t in (tach or {}).items() if la_ck(p) and float(t or 0) > 0}
	if len(nhan) == 1:
		dung = next(iter(nhan))
		if ck and set(ck) != {dung}:
			return "nhieu", nhan
		return ("", None) if dung == (next(iter(ck)) if ck else str(pt or "").strip()) else ("doi", dung)
	if set(ck) == set(nhan) and all(abs(ck[p] - nhan[p]) <= 0.5 for p in nhan):
		return "", None
	return "nhieu", nhan

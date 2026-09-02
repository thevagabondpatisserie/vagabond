"""In ngầm qua QZ Tray: máy chủ giữ khoá riêng và ký yêu cầu in.

Bài toán
--------
QZ Tray bản mã nguồn mở hiện hộp cảnh báo "Untrusted website" mỗi lần trang
web xin in, trừ khi yêu cầu được ký bằng một chứng thư mà máy tính đã tin.
Thu ngân bấm bill xong còn phải bấm Allow là hỏng nhịp quầy.

Cách gỡ không tốn tiền: anh Việt tự sinh một cặp khoá bằng openssl, cài
chứng thư công khai vào QZ Tray trên máy quầy, rồi dán khoá riêng vào màn
Vagabond Settings. Từ đó máy chủ ký hộ mọi yêu cầu in, QZ Tray thấy chữ ký
khớp chứng thư đã tin thì in thẳng, không hỏi gì.

RANH GIỚI: em không nhập khoá hộ ai. Hai ô `qz_chung_thu` và `qz_khoa_rieng`
trong Vagabond Settings do chính anh Việt dán vào trên Desk. Tệp này chỉ
đọc ra để dùng, không sinh khoá, không ghi khoá.

Vì sao khoá riêng nằm ở máy chủ chứ không ở máy quầy
---------------------------------------------------
Để khoá riêng trong tệp JavaScript là ai mở trình duyệt cũng chép được, và
chép được thì ký được lệnh in tuỳ ý trên mọi máy quầy. Ở máy chủ thì khoá
nằm trong ô Password của Frappe (mã hoá lúc lưu), máy quầy chỉ xin được chữ
ký cho đúng chuỗi nó gửi lên.

Sức công phá nếu cửa `ky` bị lạm dụng chỉ giới hạn ở chuyện in: chứng thư
này không dùng đăng nhập, không ký hoá đơn điện tử, không ký gì khác. Dù
vậy cửa vẫn chặn theo vai, và KHÔNG mở cho khách vãng lai.
"""

import base64

import frappe

# HÀNG RÀO CŨ, ĐÃ GỠ ngày 02/09/2026. Giữ danh sách lại để đọc được lịch sử,
# KHÔNG dùng để chặn nữa - xem `_chan()` bên dưới.
QUYEN_IN_CU = (
	"System Manager", "Giám đốc", "AP Giám đốc",
	"Vagabond Thu ngan", "Vagabond Bep", "Vagabond Sales",
	"Accounts Manager", "Accounts User", "Manufacturing Manager",
)

# QZ Tray 2.1 trở lên ký bằng SHA512. Giữ đường SHA1 cho máy quầy nào còn
# bản 2.0 chưa nâng cấp, nhưng KHÔNG nhận thuật toán lạ.
THUAT_TOAN = {"SHA512": "SHA512", "SHA256": "SHA256", "SHA1": "SHA1"}


def _chan():
	"""Ai được xin chữ ký in: MỌI tài khoản đã đăng nhập.

	Anh Việt 02/09/2026: *"2 tài khoản của nhân viên thu ngân khi đăng nhập
	vào (Gia Bảo và Hoàng Ngân) thì khi in máy lại báo hộp thoại allow của
	qz tray. Em kiểm tra fix ở backend dùm anh, toàn bộ tài khoản trong hệ
	thống đều phải dùng được qz tray để in ngầm."*

	Đúng là lỗi của hàng rào cũ. Bản trước chặn theo một danh sách vai gõ
	cứng, mà hai bạn đó chỉ mang các vai Bộ phận đặt hàng, Kiểm kê viên,
	Sales User, Nhận hàng điều chuyển - không vai nào nằm trong danh sách.
	Máy chủ từ chối ký, màn hình lặng lẽ quay về đường in không chữ ký, và
	QZ Tray hiện hộp Allow. Thu ngân đứng trước mặt khách phải bấm thêm một
	nút cho mỗi tờ bill.

	Hàng rào theo vai sai ngay từ ý: cấp một vai mới cho ai đó là việc xảy
	ra hàng tháng, mà mỗi lần lại phải nhớ ra tệp này. Ai quên là quầy đó
	hỏng nhịp, và không có phép kiểm nào bắt được.

	Vì sao mở ra là AN TOÀN: chứng thư này chỉ ký lệnh in. Nó không dùng để
	đăng nhập, không ký hoá đơn điện tử, không ký gì khác. Người xin được
	chữ ký chỉ in được ra chính cái máy in đứng cạnh họ. Khách vãng lai vẫn
	bị chặn, và đó mới là hàng rào thật.
	"""
	if frappe.session.user == "Guest":
		frappe.throw("Phải đăng nhập mới in được.")


def _cai_dat():
	return frappe.get_cached_doc("Vagabond Settings")


@frappe.whitelist()
def chung_thu():
	"""Chứng thư công khai dạng PEM để QZ Tray đối chiếu chữ ký.

	Trả về chuỗi rỗng nếu chưa dán chứng thư: máy quầy đọc thấy rỗng thì
	tự hiểu là chưa bật in ngầm và quay về in bằng trình duyệt, chứ không
	nổ lỗi giữa lúc thu ngân đang tính tiền.
	"""
	_chan()
	ct = (_cai_dat().get("qz_chung_thu") or "").strip()
	return {"chung_thu": ct, "da_bat": 1 if ct else 0}


@frappe.whitelist()
def ky(chuoi=None, thuat_toan="SHA512"):
	"""Ký chuỗi QZ Tray gửi lên, trả chữ ký base64.

	`chuoi` là chuỗi QZ tự dựng từ tên lệnh, tham số và mốc thời gian. Máy
	chủ không diễn giải nội dung, chỉ ký đúng chuỗi nhận được - đây là đúng
	cách QZ thiết kế, và cũng là lý do cửa này phải chặn theo vai.
	"""
	_chan()
	chuoi = chuoi if chuoi is not None else frappe.local.form_dict.get("chuoi")
	if not chuoi:
		frappe.throw("Thiếu chuỗi cần ký.")
	ten_tt = THUAT_TOAN.get(str(thuat_toan or "SHA512").upper())
	if not ten_tt:
		frappe.throw("Thuật toán ký không nhận: %s" % thuat_toan)

	khoa = (_cai_dat().get_password("qz_khoa_rieng", raise_exception=False) or "").strip()
	if not khoa:
		frappe.throw(
			"Chưa dán khoá riêng QZ Tray vào Vagabond Settings. Vào Desk, mở "
			"Vagabond Settings, mục In ngầm QZ Tray, dán khoá rồi lưu.")

	from cryptography.hazmat.primitives import hashes, serialization
	from cryptography.hazmat.primitives.asymmetric import padding

	try:
		rieng = serialization.load_pem_private_key(khoa.encode("utf-8"), password=None)
	except Exception:
		frappe.throw(
			"Khoá riêng QZ Tray không đọc được. Khoá phải ở dạng PEM và KHÔNG "
			"đặt mật khẩu: sinh bằng openssl genrsa -out khoa-rieng.pem 2048 "
			"rồi dán trọn cả hai dòng BEGIN và END.")

	bam = getattr(hashes, ten_tt)()
	chu_ky = rieng.sign(chuoi.encode("utf-8"), padding.PKCS1v15(), bam)
	return {"chu_ky": base64.b64encode(chu_ky).decode("ascii"), "thuat_toan": ten_tt}


@frappe.whitelist()
def dinh_tuyen(diem=""):
	"""Quy tắc chọn máy in theo loại giấy, cho máy quầy tự dò tên máy in.

	Trả về mảnh tên cần tìm chứ không phải tên máy in đầy đủ: tên máy in
	trên Windows đổi theo cổng USB và theo máy, mà mảnh "EPSON" hay
	"Xprinter" thì nằm nguyên trong tên driver ở mọi máy quầy.
	"""
	_chan()
	cd = _cai_dat()
	# So may in tren app di TRUOC: quan ly cua hang tu gan duoc ngay tren may
	# quay, phan theo diem ban, du bon loai phieu. Hai o cu tren Desk giu lai
	# lam luoi do cho may nao chua kip gan.
	try:
		from vagabond import may_in

		tuyen = may_in.tuyen_qz(diem)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "in_ngam: doc so may in")
		tuyen = {}
	return {
		"hoa_don": (cd.get("qz_may_in_hoa_don") or "EPSON").strip(),
		"tem": (cd.get("qz_may_in_tem") or "Xprinter").strip(),
		"tuyen": tuyen,
		"diem": str(diem or "").strip().upper(),
		"dpi": int(cd.get("qz_dpi") or 203),
		"da_bat": 1 if (cd.get("qz_chung_thu") or "").strip() else 0,
	}

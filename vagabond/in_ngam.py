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
import re

import frappe

# Vai được phép xin chữ ký in. Quầy, bếp và quản lý - tức những người thật
# sự đứng cạnh một cái máy in.
QUYEN_IN = (
	"System Manager", "Giám đốc", "AP Giám đốc",
	"Vagabond Thu ngan", "Vagabond Bep", "Vagabond Sales",
	"Accounts Manager", "Accounts User", "Manufacturing Manager",
)

# QZ Tray 2.1 trở lên ký bằng SHA512. Giữ đường SHA1 cho máy quầy nào còn
# bản 2.0 chưa nâng cấp, nhưng KHÔNG nhận thuật toán lạ.
THUAT_TOAN = {"SHA512": "SHA512", "SHA256": "SHA256", "SHA1": "SHA1"}


_MAU_PEM = re.compile(r"-----BEGIN ([A-Z0-9 ]+)-----(.*?)-----END \1-----", re.S)


def _chuan_pem(chuoi):
	"""Dựng lại khối PEM khi ô nhập đã ăn mất xuống dòng (Dễ 26/08/2026).

	Ô `qz_khoa_rieng` khai kiểu Password, mà Password trong Frappe là một ô
	MỘT DÒNG. Dán một khoá RSA hai mươi mấy dòng vào đó thì trình duyệt nuốt
	sạch dấu xuống dòng, nối tất cả thành một dòng dài. OpenSSL đọc PEM theo
	dòng nên khoá một dòng là không đọc được, và người dán thì không thấy gì
	bất thường vì ô Password che hết nội dung.

	Không đổi ô đó sang Text được: kiểu Password là thứ khiến Frappe mã hoá
	khoá lúc lưu. Đổi sang Text là khoá nằm trần trong cơ sở dữ liệu.

	Nên vá ở đây: lấy phần ruột, bỏ hết khoảng trắng, xuống dòng lại mỗi 64
	ký tự đúng chuẩn PEM. Chuỗi vốn đã đúng dạng thì đi qua hàm này vẫn y
	nguyên nội dung, chỉ chuẩn lại cách xuống dòng.
	"""
	s = (chuoi or "").strip()
	if not s:
		return s
	m = _MAU_PEM.search(s)
	if not m:
		return s
	ten = m.group(1)
	than = re.sub(r"\s+", "", m.group(2))
	dong = [than[i:i + 64] for i in range(0, len(than), 64)]
	return "-----BEGIN %s-----\n%s\n-----END %s-----\n" % (ten, "\n".join(dong), ten)


def _la_pem(chuoi):
	"""Có phải một khối PEM không, hay là người dán nhầm thứ khác vào."""
	return "-----BEGIN" in (chuoi or "") and "-----END" in (chuoi or "")


def _chan():
	if frappe.session.user == "Guest":
		frappe.throw("Phải đăng nhập mới in được.")
	if not set(frappe.get_roles()) & set(QUYEN_IN):
		frappe.throw("Tài khoản này không có quyền in. Báo quản lý cấp vai.")


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

	khoa = _chuan_pem(_cai_dat().get_password("qz_khoa_rieng", raise_exception=False))
	if not khoa:
		frappe.throw(
			"Chưa dán khoá riêng QZ Tray vào Vagabond Settings. Vào Desk, mở "
			"Vagabond Settings, mục In ngầm QZ Tray, dán khoá rồi lưu.")
	if not _la_pem(khoa):
		frappe.throw(
			"Ô khoá riêng QZ Tray đang chứa một chuỗi KHÔNG phải khoá PEM. Ô đó "
			"khai kiểu Password nên trình duyệt hay tự điền mật khẩu đăng nhập "
			"vào, che mất nội dung thật. Vào Desk, mở Vagabond Settings, xoá "
			"sạch ô đó rồi dán lại trọn tệp khoá riêng, kể cả hai dòng BEGIN và "
			"END.")

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
def tu_kiem():
	"""Chứng thư và khoá riêng có phải MỘT CẶP không.

	Vì sao cần cửa này (Dễ 25/08/2026: *"qz tray vẫn báo lỗi invalid với máy
	in GODEX khi in tem"*). Hộp "Cannot verify trust - Invalid Signature" của
	QZ Tray chỉ nói được đúng một câu: chữ ký không khớp chứng thư. Nó không
	phân biệt được ba nguyên nhân hoàn toàn khác nhau:

	  1. Chứng thư và khoá riêng không cùng một cặp. Sinh lại khoá bằng
	     openssl mà quên dán lại chứng thư, hoặc ngược lại, là ra ngay cảnh
	     này. Máy chủ vẫn ký êm ru, QZ vẫn từ chối, mãi mãi.
	  2. Máy quầy chạy QZ Tray đời 2.0, chỉ đối chiếu được SHA1. Việc này
	     app tự dò và tự hạ thuật toán, xem inNoiQz ở 27-in-ngam.js.
	  3. Chưa dán gì cả.

	Ngồi ở quầy thì không tài nào đoán ra là cái nào. Nên máy chủ tự ký thử
	một chuỗi rồi tự đối chiếu bằng khoá công khai đọc từ chính chứng thư
	đang dán: khớp thì loại hẳn nguyên nhân 1, không khớp thì nói thẳng phải
	dán lại cặp nào.

	CHỈ ĐỌC và chỉ tính trong bộ nhớ, không sinh khoá, không ghi gì.
	"""
	_chan()
	cd = _cai_dat()
	ct = _chuan_pem(cd.get("qz_chung_thu"))
	khoa = _chuan_pem(cd.get_password("qz_khoa_rieng", raise_exception=False))
	if not ct and not khoa:
		return {"hop": 0, "ma": "chua_dan", "loi": "Chưa dán chứng thư và khoá riêng QZ Tray."}
	if not ct:
		return {"hop": 0, "ma": "thieu_chung_thu", "loi": "Đã có khoá riêng nhưng chưa dán chứng thư."}
	if not khoa:
		return {"hop": 0, "ma": "thieu_khoa", "loi": "Đã dán chứng thư nhưng chưa dán khoá riêng."}
	# Benh nay bat truoc moi benh khac, vi no la benh hay gap nhat va cung la
	# benh nhin man hinh khong the thay: o Password che sach noi dung.
	if not _la_pem(khoa):
		return {"hop": 0, "ma": "khoa_khong_phai_pem", "loi":
			"Ô khoá riêng đang chứa một chuỗi không phải khoá PEM, nhiều khả năng "
			"là mật khẩu đăng nhập do trình duyệt tự điền. Xoá sạch ô đó rồi dán "
			"lại trọn tệp khoá riêng, kể cả hai dòng BEGIN và END."}

	from cryptography import x509
	from cryptography.exceptions import InvalidSignature
	from cryptography.hazmat.primitives import hashes, serialization
	from cryptography.hazmat.primitives.asymmetric import padding

	try:
		rieng = serialization.load_pem_private_key(khoa.encode("utf-8"), password=None)
	except Exception:
		return {"hop": 0, "ma": "khoa_hong", "loi":
			"Khoá riêng không đọc được. Khoá phải ở dạng PEM và KHÔNG đặt mật khẩu."}
	try:
		chung = x509.load_pem_x509_certificate(ct.encode("utf-8"))
		cong = chung.public_key()
	except Exception:
		return {"hop": 0, "ma": "chung_thu_hong", "loi":
			"Chứng thư không đọc được. Dán trọn cả hai dòng BEGIN CERTIFICATE và END CERTIFICATE."}

	# Ky thu roi tu doi chieu. Chuoi thu la co dinh, khong dinh gi toi lenh in.
	thu = b"vagabond-qz-tu-kiem"
	try:
		cong.verify(
			rieng.sign(thu, padding.PKCS1v15(), hashes.SHA512()),
			thu, padding.PKCS1v15(), hashes.SHA512())
	except InvalidSignature:
		return {"hop": 0, "ma": "lech_cap", "loi":
			"Chứng thư và khoá riêng KHÔNG cùng một cặp. Sinh lại cả hai bằng "
			"openssl rồi dán lại cả hai vào Vagabond Settings, không dán mỗi cái "
			"một lần."}
	except Exception as e:
		return {"hop": 0, "ma": "khong_ky_duoc", "loi": "Không ký thử được: %s" % e}

	# `not_valid_after` da bi khai tu trong cryptography moi, nhung ban cu
	# lai chua co `not_valid_after_utc`. Thu cai moi truoc, khong co thi lui
	# ve cai cu - han chung thu chi de hien cho de xem, hong thi bo qua.
	het = None
	try:
		mo = getattr(chung, "not_valid_after_utc", None) or chung.not_valid_after
		het = mo.strftime("%d/%m/%Y")
	except Exception:
		pass
	return {"hop": 1, "ma": "khop", "loi": "", "het_han": het}


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

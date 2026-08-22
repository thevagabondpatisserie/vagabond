"""Ca kiểm cho phần chỉ lỗi QZ Tray trên màn Cài đặt máy in.

Anh Việt 22/08/2026: đã dán chứng thư rồi mà hộp vàng vẫn khuyên đi dán
chứng thư, vì dòng hướng dẫn cũ chỉ có đúng một câu cho mọi loại lỗi.

Hai lỗi này khác hẳn nhau:

  - Chưa dán chứng thư: việc ở máy chủ, làm một lần cho cả tiệm.
  - Không nối được QZ: việc ở chính máy thu ngân, chứng thư không liên quan.

Mọi ca ở đây chạy trên phép THUẦN: đọc thẳng mã nguồn, không cần Frappe,
không cần site, không cần mạng.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


@ca("chi loi QZ: loi noi mang KHONG duoc khuyen di dan chung thu")
def _khong_do_oan_chung_thu():
	s = _doc("18-doi-chieu-may-in.js")
	i = s.find("function miGoY(")
	than = s[i:i + 2600]
	dung("co ham chi loi rieng", i > 0)
	# Cau chot: noi thang rang chung thu khong phai thu pham.
	dung("noi ro day khong phai loi chung thu", "KHÔNG phải lỗi chứng thư" in than)
	dung("nhan dien loi noi mang", "connection|connect|websocket|refus|timeout|unable" in than)


@ca("chi loi QZ: loi noi mang thi chi ba buoc lam tren MAY THU NGAN")
def _ba_buoc_tren_may():
	s = _doc("18-doi-chieu-may-in.js")
	i = s.find("function miGoY(")
	than = s[i:i + 2600]
	dung("buoc 1 xem QZ co chay khong", "khay đồng hồ" in than)
	dung("buoc 2 vao thang cua de xem", "https://localhost:8181" in than)
	dung("buoc 3 bam nut kiem tra", "bấm nút kiểm tra" in than)
	# May vua khoi dong lai la ca hay gap nhat, phai noi ra.
	dung("nhac may vua khoi dong lai", "khởi động lại" in than)


@ca("chi loi QZ: van con duong dan chung thu cho dung loai loi do")
def _van_giu_duong_chung_thu():
	s = _doc("18-doi-chieu-may-in.js")
	i = s.find("function miGoY(")
	than = s[i:i + 2600]
	dung("loi chung thu thi chi vao Vagabond Settings", "Vagabond Settings" in than)
	dung("van tro toi project doc v256", "v256" in than)


@ca("do QZ: thu RIENG tung cua de biet hong o dau")
def _do_tung_cua():
	s = _doc("18-doi-chieu-may-in.js")
	dung("co ham do mot cua", "function miDoMotCua(" in s)
	i = s.find("async function miDoQzChay()")
	than = s[i:i + 2200]
	dung("thu cua localhost", "wss://localhost:8181" in than)
	dung("thu cua localhost.qz.io", "wss://localhost.qz.io:8181" in than)


@ca("do QZ: ca hai cua im lang thi ket luan QZ KHONG chay")
def _im_lang_la_khong_chay():
	s = _doc("18-doi-chieu-may-in.js")
	i = s.find("async function miDoQzChay()")
	than = s[i:i + 2200]
	dung("ket luan QZ khong chay", "đang KHÔNG chạy" in than)
	dung("chi cach mo len", "Start menu" in than)


@ca("do QZ: chi cua localhost hong thi la trinh duyet chua chiu chung thu cua no")
def _chi_localhost_hong():
	s = _doc("18-doi-chieu-may-in.js")
	i = s.find("async function miDoQzChay()")
	than = s[i:i + 2200]
	dung("noi QZ van dang chay", "QZ Tray đang chạy" in than)
	dung("chi duong bam Nang cao", "Nâng cao" in than)


@ca("do QZ: khong bao gio treo man, moi cua co han gio")
def _co_han_gio():
	s = _doc("18-doi-chieu-may-in.js")
	i = s.find("function miDoMotCua(")
	than = s[i:i + 900]
	# Cua khong tra loi va cung khong bao loi la ca that: tuong lua nuot goi
	# im lang. Khong co han gio thi nut kiem tra quay mai khong ra ket qua.
	dung("co dat han gio", "setTimeout(" in than)
	dung("huy han gio khi da co ket qua", "clearTimeout(het)" in than)
	# Mot cua chi duoc tra loi DUNG MOT LAN, khong thi promise settle hai
	# lan va ket qua nhay lung tung.
	dung("chan tra loi hai lan", "if (kip) return;" in than)


@ca("do QZ: dung WebSocket tho chu khong qua thu vien QZ")
def _dung_websocket_tho():
	s = _doc("18-doi-chieu-may-in.js")
	i = s.find("function miDoMotCua(")
	than = s[i:i + 900]
	# Thu vien QZ nuot mat ket qua tung cua, chi tra ve mot cau chung. Do
	# tho moi tach duoc hai benh ra.
	dung("mo thang WebSocket", "new WebSocket(url)" in than)
	dung("khong goi qz.websocket.connect", "qz.websocket.connect" not in than)

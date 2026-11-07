"""v643: ba lỗi của hộp thư đối soát doisoat@ đọc trên site ngày 07/11/2026.

1. ShopeeFood 06/11: bản CSV gửi qua email ghi ĐỒNG có dấu phân cách
   ("1,095,000"), máy vẫn đọc theo nghìn đồng như mẫu cũ. 17 dòng ra đúng số do
   trùng hợp ("160,000" đọc kiểu nghìn cũng là 160.000 đồng), dòng 1.095.000 đ
   thì báo lỗi. Đơn vị nay chọn cho cả tệp.
2. GreenSM 06/11 (2 thư) bị chặn "chữ ký không khớp". Đối chiếu trên trình duyệt
   bằng WebCrypto với khoá DNS thật: khối mã hoá của chữ ký hợp lệ (đúng khoá),
   và chữ ký khớp khi thêm lại "Sender: no-reply@greensm.com". Thư gốc có ô
   Sender, Mailgun ký cả ô đó; bộ lọc chuyển account@ sang doisoat@ của máy chủ
   thư tiệm gỡ ô Sender. Bộ kiểm không sai chuẩn: dkimpy cũng báo hỏng.
3. Anh Việt 07/11: "đồng ý luôn thư forward tự động". Thư chuyển tiếp từ hộp
   nội bộ trong Cài đặt được nhận ngay khi thư đúng là của hộp đó.

Thư mẫu mới trong mau_doi_soat/dkim/ do dkimpy 1.1.8 ký thật (bản chép tại chỗ
chỉ để thêm thẻ x=), khoá bí mật ngoài repo; chặng chuyển tiếp của máy chủ
dựng theo đúng tiêu đề thư thật trên site (tên máy, thứ tự ô Received).
"""
import json
import time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import doi_soat_doc as D
from vagabond import doi_soat_dkim as K
from vagabond import doi_soat_mau as M
from vagabond import doi_soat_thu as T
from vagabond import doi_soat_vendor as V
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

THU_MUC = Path(__file__).parent / "mau_doi_soat" / "dkim"
DNS = json.loads((THU_MUC / "dns.json").read_text())
NG = [dict(ten=t, mien=T.tach_mien(m), bat_buoc=b) for t, m, b in T.NGUOI_GUI_MAC_DINH]
CH = dict(nguoi_gui=NG, noi_bo=list(T.NOI_BO_MAC_DINH))
# Giờ máy chủ tiệm nhận thư GreenSM (ô Received trên cùng): 07/11/2026 03:10:10 +07.
LUC_GSM = 1793995810


def _thu(ten):
	return (THU_MUC / ten).read_bytes()


def _dns(ten):
	v = DNS.get(ten)
	return v.encode() if v else None


def _csv(ten, chu):
	return D.doc_tep(ten, chu.replace("\n", "\r\n").encode("utf-8"))[0]


def _quyet(tho, ch=CH):
	t = T.doc_thu(tho)
	with patch.object(K, "lay_khoa_dns", _dns):
		return T._quyet(tho, t, ch)


# ------------------------------------------------------------ 1. ShopeeFood

DAU = ("STT,Mã Đơn Hàng,ID cửa hàng,Tên cửa hàng,Thời gian hoàn thành/ huỷ đơn,Giá trị đơn hàng,Khuyến mại từ quán,"
	"Phí dịch vụ,Phí vận chuyển trả cho quán,Chiết khấu,Thuế khấu trừ,Thực thu\n")
# Ba dòng theo đúng hình dạng tệp 06/11/2026 (mã đơn giả). Dòng 3 có phí ship
# trả quán 500 đồng: đọc kiểu nghìn là 500.000 đồng, sai hẳn.
SHOPEE_DONG = DAU + (
	'1,06116-900000001,10322362,TCV,06/11/2026 09:23:58,"160,000","24,000",0,0,"20,033",0,"115,967"\n'
	'2,06116-900000007,10322362,TCV,06/11/2026 10:17:19,"1,095,000","261,125",0,0,"122,830",0,"711,045"\n'
	'3,06116-900000009,10332477,NVT,06/11/2026 11:02:00,"200,000",0,0,500,"25,500",0,"175,000"\n')


@ca("v643 ShopeeFood: bản CSV email ghi đồng có dấu phân cách, đọc nguyên số cho cả tệp, không còn dòng lỗi")
def _():
	t = _csv("Shopeefood_Income_Details_Merchant_06-11-2026.csv", SHOPEE_DONG)
	la("nhận mẫu", M.nhan_dien(t), "shopeefood")
	kq = M.doc(t)
	la("ba dòng, không lỗi", (len(kq["dong"]), kq["dong_loi"], kq["loi"]), (3, [], []))
	la("đơn 1.095.000 đ", (kq["dong"][1]["tien_hang"], kq["dong"][1]["giam_gia"], kq["dong"][1]["phi"],
		kq["dong"][1]["thuc_nhan"]), (833875, 261125, 122830, 711045))
	la("ship trả quán 500 đ là 500 đ", (kq["dong"][2]["tien_hang"], kq["dong"][2]["phi"], kq["dong"][2]["thuc_nhan"]),
		(200000, 25000, 175000))
	la("dòng trùng hợp cũ vẫn đúng", (kq["dong"][0]["tien_hang"], kq["dong"][0]["thuc_nhan"]), (136000, 115967))
	la("ghi chú đơn vị nói đồng", kq["ghi_chu_don_vi"], M.GHI_CHU_SHOPEE["dong"])


@ca("v643 ShopeeFood: mẫu nghìn đồng cũ không đổi; tệp lẫn hai đơn vị là lỗi tệp, không đoán")
def _():
	cu = DAU + ('1,28036-1,10322362,TCV,28/03/2026 09:31:10,140,60,0,0,"11,784",0,"68,216"\n'
		'2,28036-3,10332477,NVT,28/03/2026 11:42:39,100,15,0,0,"12,521",0,"72,48"\n')
	kq = M.doc(_csv("Shopeefood_Income_Details_Merchant_28-03-2026.csv", cu))
	la("nghìn: 140 là 140.000 đ", (kq["dong"][0]["tien_hang"], kq["dong"][1]["thuc_nhan"], kq["dong_loi"]), (80000, 72480, []))
	la("ghi chú nghìn", kq["ghi_chu_don_vi"], M.GHI_CHU_SHOPEE["nghin"])
	lan = cu + '3,06116-9,10322362,TCV,06/11/2026 10:17:19,"1,095,000","261,125",0,0,"122,830",0,"711,045"\n'
	kq = M.doc(_csv("x.csv", lan))
	dung("lẫn hai đơn vị: lỗi tệp (%s)" % kq["loi"], any("lẫn" in x for x in kq["loi"]))


@ca("v643 ShopeeFood: dấu hiệu đơn vị theo Giá trị đơn hàng; ô số Excel ghi đồng không bị nhân 1.000")
def _():
	la("bảng dấu hiệu", [M.dau_don_vi_shopee(v) for v in (
		"1,095,000", "1.095.000", "72,48", "87,5", "160,000", "82.488", "140", "0", "1095000", "2500",
		1095000, 82.488, 140, 2500)],
		["dong", "dong", "nghin", "nghin", "", "", "nghin", "", "dong", "", "dong", "nghin", "nghin", ""])
	la("đọc đồng hai kiểu dấu", [M.tien_dong_shopee(v) for v in ("1,095,000", "1.095.000", "950", "0", 1095000)],
		[1095000, 1095000, 950, 0, 1095000])
	for v in ("1,095.5", "1,09,500", "72,48", "1.095,000"):
		nem("đồng sai dạng %s" % v, lambda v=v: M.tien_dong_shopee(v), M.LoiDong)
	# Bản tải trên cổng (ô số) mà ghi đồng: trước v643 là nhân 1.000 thành 1,095 tỷ.
	o = D.doc_csv(DAU.encode())[0]["o"] + [[1, "06116-9", "10322362", "TCV", "06/11/2026 10:17:19", 1095000, 261125, 0, 0,
		122830, 0, 711045]]
	kq = M.doc(dict(ten="Shopeefood_Income_Details_Merchant_06-11-2026.xlsx", loai="xlsx", sha256="x",
		trang=[dict(ten="Sheet1", o=o)]))
	la("ô số đồng đọc nguyên", (kq["dong"][0]["tien_hang"] if kq["dong"] else None, kq["dong_loi"]), (833875, []))
	la("THUẦN chọn: không dấu hiệu, hai cách cùng số là nghìn",
		M.chon_don_vi_shopee({""}, ([1], []), ([1], [])), ("nghin", ""))
	la("THUẦN chọn: không dấu hiệu, cách nào ít lỗi hơn", M.chon_don_vi_shopee(set(), ([1], [9]), ([2], [])), ("dong", ""))
	dung("THUẦN chọn: hai cách khác số, cùng số lỗi là lỗi tệp", M.chon_don_vi_shopee(set(), ([1], []), ([2], []))[1])


# ------------------------------------------------------------ 2. GreenSM qua bộ lọc chuyển tiếp

@ca("v643 GreenSM: thư gốc ký cả ô Sender; qua bộ lọc mất Sender vẫn nhận, ghi rõ đã dựng lại ô Sender")
def _():
	goc = K.kiem_thu(_thu("greensm_goc.eml"), _dns, LUC_GSM)
	la("thư gốc (còn Sender) đạt, không cần bù", [(x["dat"], x.get("ghi_chu")) for x in goc], [(True, None)])
	qua = _thu("greensm_qua_loc.eml")
	dung("thư qua lọc thật sự mất ô Sender", b"\r\nSender:" not in qua.split(b"\r\n\r\n", 1)[0])
	r = K.kiem_thu(qua, _dns, LUC_GSM)
	la("qua lọc: đạt nhờ thêm lại Sender = From", [(x["d"], x["dat"], bool(x.get("ghi_chu"))) for x in r],
		[("greensm.com", True, True)])
	qd, _ck = _quyet(qua)
	la("nhận vào đường Từ thư", (qd["ket_qua"], qd["nguon"], qd["ky_boi"]), (T.KQ_XAC_THUC, "GreenSM (Xanh SM)", "greensm.com"))
	dung("lý do nói đã dựng lại ô Sender (%s)" % qd["ly_do"], "gỡ ô Sender" in qd["ly_do"])


@ca("v643 GreenSM: bù Sender không mở cửa cho thư sửa; Sender khác From thì vẫn chặn (giới hạn đã biết)")
def _():
	qua = _thu("greensm_qua_loc.eml")
	sua = qua.replace(b"doanh_thu_06/11/2026", b"doanh_thu_07/11/2026")
	la("sửa tiêu đề sau khi ký: hỏng dù đã bù", K.kiem_thu(sua, _dns, LUC_GSM)[0]["dat"], False)
	sua = qua.replace(b"To: hoadon@", b"To: ketoan@")
	la("sửa người nhận: hỏng", K.kiem_thu(sua, _dns, LUC_GSM)[0]["dat"], False)
	r = K.kiem_thu(_thu("greensm_sender_khac.eml"), _dns, LUC_GSM)
	la("Sender gốc khác From: không đoán được, vẫn hỏng", r[0]["dat"], False)
	tieu, _than = K.tach_thu(qua)
	h = [b"from", b"sender"]
	la("THUẦN: chỉ thử đúng địa chỉ From", [x[1] for x in K.o_sender_bu(tieu, h, "relaxed")], [b" no-reply@greensm.com\r\n"])
	la("THUẦN: simple không bù", K.o_sender_bu(tieu, h, "simple"), [])
	la("THUẦN: h= không ký Sender thì không bù", K.o_sender_bu(tieu, [b"from"], "relaxed"), [])
	co = tieu + [(b"Sender", b" a@b.c\r\n", b"")]
	la("THUẦN: thư còn ô Sender thì không bù", K.o_sender_bu(co, h, "relaxed"), [])
	ten = [(b"From", b" GreenSM <no-reply@greensm.com>\r\n", b"")]
	la("THUẦN: From có tên: thử địa chỉ trơn rồi nguyên văn", [x[1] for x in K.o_sender_bu(ten, h, "relaxed")],
		[b" no-reply@greensm.com\r\n", b" GreenSM <no-reply@greensm.com>\r\n"])


@ca("v643 GreenSM: hạn x= của Mailgun (2 giờ) so với giờ máy chủ tiệm nhận thư, nên Kiểm lại thư sau đó vẫn đạt")
def _():
	qua = _thu("greensm_qua_loc.eml")
	la("giờ nhận đọc từ ô Received trên cùng", K.luc_nhan(qua), LUC_GSM)
	la("so với giờ hiện tại: hết hạn", K.kiem_thu(qua, _dns)[0]["ly_do"], "Chữ ký số đã hết hạn.")
	qd, _ck = _quyet(qua)
	dung("đường xử lý thật dùng giờ nhận: đạt (%s)" % qd["ly_do"][:60], qd["ket_qua"] == T.KQ_XAC_THUC and time.time() > LUC_GSM + 7200)
	la("không có Received: None", K.luc_nhan(b"From: a@b.c\r\n\r\nx"), None)
	la("Received không có ngày: None", K.luc_nhan(b"Received: from x by y\r\nFrom: a@b.c\r\n\r\nx"), None)
	# Đồng hồ máy chủ thư chạy nhanh: ô Received ghi 07/11 05:20 (+07), quá hạn x=
	# (05:10), trong khi giờ hiện tại của ERP mới 03:11. Lấy giờ nhỏ hơn.
	tuong_lai = b"Received: from x by y; Sat, 07 Nov 2026 05:20:10 +0700\r\n" + qua
	with patch.object(K, "lay_khoa_dns", _dns), patch("time.time", lambda: LUC_GSM + 60):
		qd2, _ = T._quyet(tuong_lai, T.doc_thu(tuong_lai), CH)
	la("giờ nhận ở tương lai (đồng hồ lệch): lấy giờ hiện tại, còn hạn", qd2["ket_qua"], T.KQ_XAC_THUC)


# ------------------------------------------------------------ 3. thư chuyển tiếp từ hộp nội bộ

@ca("v643 chuyển tiếp nội bộ: Gmail của tiệm có chữ ký gmail.com, account@ gửi qua máy chủ tiệm có đăng nhập: nhận ngay")
def _():
	qd, ck = _quyet(_thu("noi_bo_gmail.eml"))
	la("Gmail: nhận, ký bởi gmail.com", (qd["ket_qua"], qd["nguon"], qd["ky_boi"], qd.get("noi_bo")),
		(T.KQ_XAC_THUC, T.NGUON_NOI_BO, "gmail.com", 1))
	dung("lý do nói tệp không còn chữ ký gốc", "không còn chữ ký gốc" in qd["ly_do"])
	qd, ck = _quyet(_thu("noi_bo_account.eml"))
	la("account@: không chữ ký, gửi có đăng nhập: nhận, ô Chữ ký số để trống", (qd["ket_qua"], qd["ky_boi"], ck),
		(T.KQ_XAC_THUC, "", []))
	dung("lý do nói có đăng nhập", "có đăng nhập" in qd["ly_do"])


@ca("v643 chuyển tiếp nội bộ: thư mạo danh hộp nội bộ bị chặn và báo Zalo; Cài đặt trống là chặn như cũ")
def _():
	qd, _ck = _quyet(_thu("noi_bo_gia.eml"))
	la("người ngoài tự chèn Received esmtpsa bên dưới: chặn, báo Zalo", (qd["ket_qua"], qd["bao_zalo"]), (T.KQ_CHAN, 1))
	sua = _thu("noi_bo_gmail.eml").replace(b"Subject: Fwd: ShopeeFood", b"Subject: Fwd: ShopeeFood sua")
	qd, _ck = _quyet(sua)
	la("Gmail chữ ký hỏng, không đăng nhập: chặn, báo Zalo", (qd["ket_qua"], qd["bao_zalo"]), (T.KQ_CHAN, 1))
	qd, _ck = _quyet(_thu("noi_bo_account.eml"), dict(nguoi_gui=NG, noi_bo=[]))
	la("Cài đặt trống: chặn như người lạ, không báo", (qd["ket_qua"], qd["bao_zalo"], qd["nguon"]), (T.KQ_CHAN, 0, ""))
	la_khac = _thu("noi_bo_gmail.eml").replace(b"thevagabondbakery@gmail.com", b"ke.gian@gmail.com")
	qd, _ck = _quyet(la_khac)
	la("Gmail khác danh sách: chặn như người lạ", (qd["ket_qua"], qd["nguon"]), (T.KQ_CHAN, ""))


@ca("v643 chuyển tiếp nội bộ THUẦN: chặng SMTP đầu tiên của máy chủ tiệm phải có đăng nhập, Return-Path đúng địa chỉ")
def _():
	A = "account@thevagabondpatisserie.com"
	lmtp = ("Received", " from pro10.emailserver.vn by pro10.emailserver.vn with LMTP; Fri, 06 Nov 2026 18:24:17 +0700")
	auth = ("Received", " from [40.99.68.165] by pro10.emailserver.vn with esmtpsa (TLS1.3); Fri, 06 Nov 2026 18:24:17 +0700")
	rp = ("Return-Path", " <%s>" % A)
	la("đủ: đạt", T.qua_may_chu_dang_nhap([rp, lmtp, auth], A), True)
	la("esmtpa cũng đạt", T.qua_may_chu_dang_nhap([rp, lmtp, ("Received", auth[1].replace("esmtpsa", "esmtpa"))], A), True)
	la("Return-Path khác: không", T.qua_may_chu_dang_nhap([("Return-Path", " <x@y.vn>"), lmtp, auth], A), False)
	la("không Return-Path: không", T.qua_may_chu_dang_nhap([lmtp, auth], A), False)
	ngoai = ("Received", " from mail.x by pro10.emailserver.vn with esmtps (TLS1.3); x")
	la("chặng đầu không đăng nhập, dưới có esmtpsa giả: không", T.qua_may_chu_dang_nhap([rp, lmtp, ngoai, auth], A), False)
	khac = ("Received", " from [1.2.3.4] by mail.khac.vn with esmtpsa; x")
	la("chặng đầu do máy khác nhận: không", T.qua_may_chu_dang_nhap([rp, lmtp, khac], A), False)
	la("chỉ có chặng nội bộ (gửi bằng lệnh trên máy chủ): không", T.qua_may_chu_dang_nhap([rp, lmtp,
		("Received", " from u1 by pro10.emailserver.vn with local; x")], A), False)
	la("không Received: không", T.qua_may_chu_dang_nhap([rp], A), False)
	G = "thevagabondbakery@gmail.com"
	la("chữ ký hợp lệ của tên miền khác không thay được chữ ký gmail.com",
		T.quyet_noi_bo(G, 1, [dict(d="ke-gian.example", dat=True)], False)["ket_qua"], T.KQ_CHAN)
	la("chữ ký tên miền con của gmail.com vẫn là gmail.com", T.quyet_noi_bo(G, 1, [dict(d="gmail.com", dat=True)], False)["ket_qua"],
		T.KQ_XAC_THUC)
	la("hai địa chỉ người gửi: chặn", T.quyet_noi_bo(G, 2, [dict(d="gmail.com", dat=True)], True)["ket_qua"], T.KQ_CHAN)
	la("tách địa chỉ Cài đặt", T.tach_dia_chi("Account@TheVagabondPatisserie.com\nKế toán <kt@x.vn>; sai, a@b.vn, a@b.vn"),
		["account@thevagabondpatisserie.com", "kt@x.vn", "a@b.vn"])


@ca("v643 chuyển tiếp nội bộ: _xu_ly ghi đường Từ thư, đọc tệp trong thư lồng; không tệp thì không dựng nguồn thư không tệp")
def _():
	nhan, ghi_truong = [], {}

	def chay(tho):
		nhan.clear()
		ghi_truong.clear()
		thu = NS(name="DST-1", nhan_luc="2026-11-06 18:24:17", sha256="x",
			insert=lambda **k: None, db_set=lambda *a, **k: ghi_truong.update(a[0] if isinstance(a[0], dict) else {a[0]: a[1]}))
		fr = NS(db=NS(get_value=lambda *a, **k: None), get_doc=lambda *a, **k: (ghi_truong.update(a[0]) if a and isinstance(a[0], dict) else None) or thu,
			utils=NS(now_datetime=lambda: "2026-11-07 10:00:00"))

		def nhan_byte(ten, byte, kenh, **k):
			nhan.append((ten, k["them"]["duong_vao"]))
			return [dict(name="DSN-1", ten_tep=ten)]
		with patch.object(T, "_frappe", lambda: fr), patch.object(K, "lay_khoa_dns", _dns), \
				patch.object(V, "_cong_ty", lambda: "A"), patch.object(V, "_nhan_byte", nhan_byte), \
				patch.object(T, "_luu_tep_an_toan", lambda *a: "/private/files/x"), \
				patch.object(T, "_ghi_thu_khong_tep", lambda *a: nhan.append("khong_tep") or []), \
				patch.object(V, "thu_co_bao_cao", lambda *a: True):
			return T._xu_ly(tho, 5, CH)
	chay(_thu("noi_bo_account.eml"))
	la("đọc tệp CSV, đường Từ thư", nhan, [("Shopeefood_Income_Details_Merchant_06-11-2026.csv", T.DV_THU)])
	la("sổ thư: kết quả, đối tác, nguồn", (ghi_truong.get("ket_qua"), ghi_truong.get("doi_tac"), ghi_truong.get("nguon")),
		(T.KQ_XAC_THUC, T.NGUON_NOI_BO, "DSN-1"))
	# Outlook "chuyển tiếp dạng đính kèm": tệp nằm trong thư lồng message/rfc822.
	goc = _thu("noi_bo_account.eml")
	dau, than = goc.split(b"\r\n\r\n", 1)
	trong = b"\r\n".join(x for x in dau.split(b"\r\n") if not x.lower().startswith((b"received", b"return-path",
		b"delivered-to", b"\t"))) + b"\r\n\r\n" + than
	dau_ngoai = dau.split(b"From:")[0]
	long = (dau_ngoai + b"From: <account@thevagabondpatisserie.com>\r\nTo: doisoat@thevagabondpatisserie.com\r\n"
		b"Subject: FW: ShopeeFood\r\nMIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary=\"NGOAI\"\r\n\r\n"
		b"--NGOAI\r\nContent-Type: text/plain\r\n\r\nxem tep\r\n--NGOAI\r\nContent-Type: message/rfc822\r\n\r\n" + trong +
		b"\r\n--NGOAI--\r\n")
	la("THUẦN: thư đối tác không đi vào thư lồng", [x[0] for x in T.doc_thu(long)["tep"]], [])
	la("THUẦN: thư nội bộ đi vào thư lồng", [x[0] for x in T.doc_thu(long, vao_long=True)["tep"]],
		["Shopeefood_Income_Details_Merchant_06-11-2026.csv"])
	chay(long)
	la("thư nội bộ chuyển tiếp dạng đính kèm: đọc tệp trong thư lồng", [x[0] for x in nhan],
		["Shopeefood_Income_Details_Merchant_06-11-2026.csv"])
	khong = goc.split(b"--NB643\r\nContent-Type: text/csv")[0] + b"--NB643--\r\n"
	chay(khong)
	la("thư nội bộ không tệp: không dựng nguồn thư không tệp", (nhan, ghi_truong.get("ket_qua")), ([], T.KQ_KHONG_TEP))
	import sys
	bao = []
	import vagabond as goi
	zl = NS(bao_hoac_ghi_loi=lambda *a, **k: bao.append((a[2], k["khoa"])))
	with patch.dict(sys.modules, {"vagabond.kenh_zalo": zl}), patch.object(goi, "kenh_zalo", zl, create=True):
		chay(_thu("noi_bo_gia.eml"))
	la("thư mạo danh: không đọc tệp nào", nhan, [])
	la("báo Zalo đúng tên hộp nội bộ", bao, [("Chặn 1 thư tự xưng hộp thư nội bộ account@thevagabondpatisserie.com",
		"ds_gia_danh:DST-1")])


@ca("v643 Kiểm lại thư: thư Bị chặn chạy lại đúng đường thư mới; thư đã nhận vẫn không đọc lại")
def _():
	chay = []
	thu = dict(name="THU-1", ket_qua=T.KQ_CHAN, xong=1, tep_goc="/private/files/a.eml", uid="5")
	tho = _thu("greensm_qua_loc.eml")
	import hashlib
	ghi = []

	def get_value(dt, name, f=None, as_dict=False):
		if f == "sha256":
			return hashlib.sha256(tho).hexdigest()
		if isinstance(f, list) and "tep_goc" in f:
			return NS(**thu)
		return NS(ket_qua=T.KQ_XAC_THUC, ly_do="")

	class Nem(Exception):
		pass
	nguon = []
	fr = NS(db=NS(get_value=get_value, sql=lambda q, *a, **k: [[1]], commit=lambda: ghi.append("commit"),
		rollback=lambda: ghi.append("rollback")), get_doc=lambda *a, **k: NS(get_content=lambda: tho),
		get_all=lambda dt, filters=None, pluck=None: list(nguon) if filters == {"thu": "THU-1"} else [],
		throw=lambda m, *a, **k: (_ for _ in ()).throw(Nem(m)), ValidationError=Nem, log_error=lambda *a, **k: None)
	with patch.object(T, "_frappe", lambda: fr), patch.object(T, "cau_hinh", lambda: CH), \
			patch.object(T, "_xu_ly", lambda t, u, c, kiem_lai=False, giu_xac_thuc=False: chay.append((u, kiem_lai, giu_xac_thuc))):
		ra = T.doc_lai_thu("THU-1")
		la("Bị chặn: chạy lại với cờ kiểm lại, commit", (chay, "commit" in ghi, ra.ket_qua), ([("5", True, False)], True, T.KQ_XAC_THUC))
		chay.clear()
		thu.update(ket_qua=T.KQ_XAC_THUC)
		nguon[:] = ["Đã khớp", "Cần xử lý"]
		ra = T.doc_lai_thu("THU-1")
		la("Đã xác thực mà còn nguồn Cần xử lý: đọc lại tệp, giữ kết quả xác thực", chay, [("5", True, True)])
		for kq, ng in ((T.KQ_XAC_THUC, ["Đã khớp"]), (T.KQ_XAC_THUC, []), (T.KQ_KHONG_TEP, ["Cần xử lý"]), (T.KQ_CHO, [])):
			chay.clear()
			nguon[:] = ng
			thu.update(ket_qua=kq)
			try:
				T.doc_lai_thu("THU-1")
				ra = "chạy"
			except Nem as e:
				ra = str(e)
			dung("%s: không đọc lại (%s)" % (kq, ra), "đã xử lý xong" in ra and chay == [])


@ca("v643 Kiểm lại thư: _xu_ly có cờ kiểm lại mới xử lý thư đã xong; lượt đọc hộp thư thường vẫn bỏ qua")
def _():
	viec = []
	fr = NS(db=NS(get_value=lambda *a, **k: NS(name="DST-9", xong=1, tep_goc="x")),
		get_doc=lambda *a, **k: NS(name="DST-9", nhan_luc="x", db_set=lambda *a, **k: viec.append(a[0] if a else k)))
	with patch.object(T, "_frappe", lambda: fr), patch.object(K, "lay_khoa_dns", _dns), patch.object(V, "_cong_ty", lambda: "A"), \
			patch.object(V, "_nhan_byte", lambda *a, **k: []), patch.object(V, "thu_co_bao_cao", lambda *a: False):
		la("lượt thường: bỏ qua thư đã xong", T._xu_ly(_thu("greensm_qua_loc.eml"), 5, CH), None)
		la("kiểm lại: xử lý lại", T._xu_ly(_thu("greensm_qua_loc.eml"), 5, CH, kiem_lai=True), "DST-9")
	dung("đã ghi lại kết quả mới", any(isinstance(x, dict) and x.get("ket_qua") == T.KQ_XAC_THUC for x in viec))


@ca("v643 Đọc lại thư gốc: thư ĐÃ xác thực mà nay kiểm lại không đạt (đối tác đổi khoá) thì dừng, không hạ thành Bị chặn, không báo thư giả")
def _():
	viec = []

	class Nem(Exception):
		pass
	fr = NS(db=NS(get_value=lambda *a, **k: NS(name="DST-9", xong=1, tep_goc="x")),
		get_doc=lambda *a, **k: NS(name="DST-9", nhan_luc="x", db_set=lambda *a, **k: viec.append(a[0] if a else k)),
		throw=lambda m, *a, **k: (_ for _ in ()).throw(Nem(m)))
	doi_khoa = dict(DNS, **{"smtp._domainkey.greensm.com": DNS["t643._domainkey.gmail.com"]})
	with patch.object(T, "_frappe", lambda: fr), patch.object(K, "lay_khoa_dns", lambda ten: doi_khoa.get(ten, "").encode() or None), \
			patch.object(V, "_cong_ty", lambda: "A"), patch.object(V, "_nhan_byte", lambda *a, **k: viec.append("nhan") or []):
		try:
			T._xu_ly(_thu("greensm_qua_loc.eml"), 5, CH, kiem_lai=True, giu_xac_thuc=True)
			ra = "chạy"
		except Nem as e:
			ra = str(e)
	dung("dừng và nói giữ kết quả cũ (%s)" % ra[:80], "giữ nguyên kết quả cũ" in ra)
	la("không ghi gì, không đọc tệp", viec, [])

	def tam(ten):
		raise K.LoiDnsTam("Timeout")
	with patch.object(T, "_frappe", lambda: fr), patch.object(K, "lay_khoa_dns", tam), patch.object(V, "_cong_ty", lambda: "A"):
		try:
			T._xu_ly(_thu("greensm_qua_loc.eml"), 5, CH, kiem_lai=True, giu_xac_thuc=True)
			ra = "chạy"
		except K.LoiDnsTam:
			ra = "LoiDnsTam"
		except Nem as e:
			ra = str(e)
	la("DNS lỗi tạm: vẫn báo thử lại sau, không nói đổi khoá", ra, "LoiDnsTam")


@ca("v643 Cài đặt: ô Hộp thư nội bộ được chuyển tiếp gieo một lần khi trống, xoá trắng thì không gieo lại")
def _():
	g, o, loi = {}, {}, []
	fr = NS(get_meta=lambda dt: NS(has_field=lambda f: True),
		db=NS(get_global=lambda k: g.get(k), set_global=lambda k, v: g.__setitem__(k, v),
			get_single_value=lambda dt, f: o.get(f), set_single_value=lambda dt, f, v: o.__setitem__(f, v)),
		clear_document_cache=lambda *a: None, log_error=lambda *a, **k: loi.append(1))
	with patch.object(T, "_frappe", lambda: fr):
		T.gieo_noi_bo()
		la("gieo hai địa chỉ mặc định", (T.tach_dia_chi(o.get("ds_thu_noi_bo")), loi), (list(T.NOI_BO_MAC_DINH), []))
		o["ds_thu_noi_bo"] = ""
		T.gieo_noi_bo()
		la("anh xoá trắng: không gieo lại", o["ds_thu_noi_bo"], "")
		g.clear()
		o["ds_thu_noi_bo"] = "kt@x.vn"
		T.gieo_noi_bo()
		la("đã có giá trị: không đè", o["ds_thu_noi_bo"], "kt@x.vn")
	s = (Path(T.__file__).parent / "vagabond/doctype/vagabond_settings/vagabond_settings.json").read_text()
	d = json.loads(s)
	thu_tu = d["field_order"]
	la("ô đứng ngay sau bảng Người gửi tin cậy", thu_tu[thu_tu.index("ds_nguoi_gui") + 1], "ds_thu_noi_bo")
	f = next(x for x in d["fields"] if x["fieldname"] == "ds_thu_noi_bo")
	dung("nhãn và mô tả tiếng Việt có dấu, nói rõ để trống", f["label"] == "Hộp thư nội bộ được chuyển tiếp"
		and "Để trống là không nhận" in f["description"])
	with patch.object(T, "_frappe", lambda: NS(get_cached_doc=lambda dt: NS(get=lambda k, d=None: {
			"ds_thu_noi_bo": "A@B.vn\nc@d.vn"}.get(k, d)))), patch.object(T, "_bang", lambda doc, fn: []):
		la("cấu hình đọc ô vào danh sách", T.cau_hinh()["noi_bo"], ["a@b.vn", "c@d.vn"])

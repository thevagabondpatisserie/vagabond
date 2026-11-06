"""v641: đối soát tự động qua hộp thư doisoat@ (anh Việt duyệt 06/11/2026).

Thư mẫu trong mau_doi_soat/dkim/ do dkimpy 1.1.8 KÝ THẬT bằng khoá RSA sinh
riêng cho ca kiểm (bộ ký độc lập với bộ kiểm doi_soat_dkim tự viết). Khoá bí mật
không đưa vào repo; dns.json là các bản ghi TXT khoá công khai tương ứng, thay
cho tra DNS thật. Tên miền là tên miền thật của đối tác nhưng khoá là khoá giả:
ca kiểm chỉ chứng minh bộ kiểm đúng chuẩn, không nói gì về khoá thật của họ.

Ca dựng đúng chuỗi của máy chủ: byte thư gốc -> doc_thu -> kiem_thu (chữ ký)
-> quyet_dinh (nhận, chờ duyệt hay chặn). Không gọi thêm hàm nào "cho chắc".
"""
import json
import subprocess
from datetime import date
from pathlib import Path

from vagabond import doi_soat_dkim as K
from vagabond import doi_soat_thu as T
from vagabond import doi_soat_vendor as V
from vagabond import doi_soat_mau as M
from vagabond.khung.kiem_thu.nen import ca, dung, la

THU_MUC = Path(__file__).parent / "mau_doi_soat" / "dkim"
DNS = json.loads((THU_MUC / "dns.json").read_text())


def _thu(ten):
	return (THU_MUC / ten).read_bytes()


def _dns(ten):
	v = DNS.get(ten)
	return v.encode() if v else None


def _kiem(tho, dns=_dns):
	return K.kiem_thu(tho, dns)


NG = [dict(ten=t, mien=T.tach_mien(m), bat_buoc=b) for t, m, b in T.NGUOI_GUI_MAC_DINH]


def _qd(tho, ng=NG):
	t = T.doc_thu(tho)
	return T.quyet_dinh(t["mien"], t["so_from"], _kiem(tho), ng), t


# ------------------------------------------------------------ chữ ký số

@ca("v641 DKIM: thư dkimpy ký thật (relaxed, simple, l= đủ thân, tên miền con) đều kiểm đạt")
def _():
	for ten, mien in (("relaxed.eml", "onepay.vn"), ("simple.eml", "onepay.vn"), ("do_dai_l.eml", "onepay.vn"),
			("grab.eml", "grab.com"), ("khoa_1024.eml", "onepay.vn")):
		r = _kiem(_thu(ten))
		la("%s một chữ ký đạt" % ten, [(x["d"], x["dat"], x["ly_do"]) for x in r], [(mien, True, "")])


@ca("v641 DKIM: sửa một chữ trong thân thư hay trong tệp đính kèm là chữ ký hỏng")
def _():
	b = _thu("relaxed.eml")
	for cu, moi in ((b"Kinh gui", b"Kinh goi"), (b"TmdheS", b"TmdheC")):
		dung("mẫu sửa có trong thư", b.count(cu) == 1)
		r = _kiem(b.replace(cu, moi))
		la("hỏng vì thân thư", (r[0]["dat"], "đã bị sửa" in r[0]["ly_do"]), (False, True))


@ca("v641 DKIM: sửa tiêu đề đã ký (Subject) là chữ ký không khớp")
def _():
	b = _thu("simple.eml").replace(b"tam ung 05/11", b"tam ung 06/11")
	r = _kiem(b)
	la("không khớp", (r[0]["dat"], "không khớp" in r[0]["ly_do"]), (False, True))


@ca("v641 DKIM: thẻ l= mà nối thêm phần sau phần đã ký thì không nhận")
def _():
	b = _thu("do_dai_l.eml") + b"--XYZ\r\nContent-Type: text/csv; name=\"x.csv\"\r\n\r\n1,2\r\n"
	r = _kiem(b)
	la("chặn l=", (r[0]["dat"], "một phần thân thư" in r[0]["ly_do"]), (False, True))


@ca("v641 DKIM: rsa-sha1, khoá thu hồi, không có khoá, khoá sai, khoá quá ngắn đều không đạt")
def _():
	la("sha1", _kiem(_thu("sha1.eml"))[0]["dat"], False)
	b = _thu("relaxed.eml")
	la("khoá thu hồi", _kiem(b, lambda n: b"v=DKIM1; k=rsa; p=")[0]["ly_do"], "Khoá chữ ký đã bị đối tác thu hồi.")
	la("không tìm thấy khoá", "Không tìm thấy khoá" in _kiem(b, lambda n: None)[0]["ly_do"], True)
	la("khoá của bên khác", _kiem(b, lambda n: _dns("k1._domainkey.thu-gia.example"))[0]["dat"], False)
	n = (1 << 511) | 12345
	der = _der(0x30, _der(0x02, b"\x00" + n.to_bytes(64, "big")) + _der(0x02, b"\x01\x00\x01"))
	import base64

	txt = b"v=DKIM1; k=rsa; p=" + base64.b64encode(der)
	la("khoá 512 bit", "quá ngắn" in _kiem(b, lambda x: txt)[0]["ly_do"], True)


def _der(the, nd):
	return bytes([the, len(nd)]) + nd if len(nd) < 128 else bytes([the, 0x81, len(nd)]) + nd


@ca("v641 DKIM: thư lưu lại chỉ còn LF vẫn kiểm đúng; thư không chữ ký trả danh sách rỗng")
def _():
	la("LF", _kiem(_thu("relaxed.eml").replace(b"\r\n", b"\n"))[0]["dat"], True)
	b = _thu("relaxed.eml")
	tach = b.index(b"From: ")
	la("bỏ chữ ký", _kiem(b[tach:]), [])


# ------------------------------------------------------------ quyết định nhận thư

@ca("v641 quyết định: chữ ký đúng tên miền đối tác thì nhận; chữ ký của bên khác thì chặn và báo Zalo")
def _():
	q, t = _qd(_thu("relaxed.eml"))
	la("nhận OnePay", (q["ket_qua"], q["nguon"], q["ky_boi"], t["mien"]), (T.KQ_XAC_THUC, "OnePay", "onepay.vn", "onepay.vn"))
	q, _t = _qd(_thu("mien_khac.eml"))
	la("chặn, báo Zalo", (q["ket_qua"], q["bao_zalo"], "thu-gia.example" in q["ly_do"]), (T.KQ_CHAN, 1, True))
	q, _t = _qd(_thu("hai_chu_ky.eml"))
	la("có chữ ký đúng bên cạnh chữ ký lạ vẫn nhận", q["ket_qua"], T.KQ_XAC_THUC)
	q, _t = _qd(_thu("grab.eml"))
	la("merchant.grab.com ký grab.com", (q["ket_qua"], q["nguon"]), (T.KQ_XAC_THUC, "Grab"))


@ca("v641 quyết định: thư giả không chữ ký bị chặn; Cài đặt tắt bắt buộc chữ ký thì chờ giám đốc duyệt")
def _():
	b = _thu("relaxed.eml")
	gia = b[b.index(b"From: "):]
	q, _t = _qd(gia)
	la("chặn", (q["ket_qua"], q["bao_zalo"], q["ly_do"]), (T.KQ_CHAN, 1, "Thư không có chữ ký số của onepay.vn."))
	ng = [dict(x, bat_buoc=0) if x["ten"] == "OnePay" else x for x in NG]
	q, _t = _qd(gia, ng)
	la("chờ duyệt", (q["ket_qua"], q["bao_zalo"]), (T.KQ_CHO, 0))
	q, _t = _qd(_thu("sha1.eml"))
	la("chữ ký sha1 của chính onepay.vn: chặn, nêu lý do", (q["ket_qua"], "rsa-sha1" in q["ly_do"]), (T.KQ_CHAN, True))


@ca("v641 quyết định: người gửi ngoài danh sách bị chặn không báo Zalo; hai ô From bị chặn")
def _():
	b = _thu("relaxed.eml").replace(b"no-reply@onepay.vn", b"ketoan@gmail.com")
	q, _t = _qd(b)
	la("người lạ", (q["ket_qua"], q["bao_zalo"], q["nguon"]), (T.KQ_CHAN, 0, ""))
	# Kẻ gian chèn thêm một From lên đầu thư thật: chữ ký vẫn đúng với From cũ
	# ở dưới, nhưng phần mềm thư hiện From giả. Hai ô From thì chặn.
	hai = b"From: OnePay <no-reply@onepay.vn.lua.example>\r\n" + _thu("relaxed.eml")
	# Chữ ký vẫn ĐẠT (RFC 6376: h= chọn From dưới cùng), nên riêng chữ ký không
	# đủ chặn; phải chặn ở số ô From.
	la("chữ ký vẫn đạt với From dưới", _kiem(hai)[0]["dat"], True)
	q, t = _qd(hai)
	la("hai From", (t["so_from"], q["ket_qua"]), (2, T.KQ_CHAN))


@ca("v641 tên miền: tên miền con được tính, tên miền giống tên thì không")
def _():
	g = T.tach_mien("grab.com, Grabtaxi.com;")
	la("tách", g, ["grab.com", "grabtaxi.com"])
	la("con", T.thuoc("merchant.grab.com", g), True)
	la("giả dạng", (T.thuoc("evilgrab.com", g), T.thuoc("grab.com.evil.vn", g)), (False, False))
	la("địa chỉ", T.mien_cua("OnePay <no-reply@OnePay.vn>"), "onepay.vn")


@ca("v641 đọc thư: lấy đúng tệp đính kèm, bỏ tệp nằm trong thư chuyển tiếp lồng")
def _():
	t = T.doc_thu(_thu("relaxed.eml"))
	la("một tệp", [(a, b) for a, b in t["tep"]], [("TB_TAMUNG_0511.csv", "Ngay,So tien\r\n05/11/2026,18014760\r\n".encode())])
	la("tiêu đề", t["tieu_de"], "Thong bao tam ung 05/11/2026")
	long = (b"From: a@onepay.vn\r\nSubject: fw\r\nMIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary=\"B\"\r\n\r\n"
		b"--B\r\nContent-Type: text/plain\r\n\r\nxem\r\n--B\r\nContent-Type: message/rfc822\r\n\r\n"
		b"From: x@onepay.vn\r\nContent-Type: text/csv; name=\"a.csv\"\r\nContent-Disposition: attachment; filename=\"a.csv\"\r\n\r\n1,2\r\n--B--\r\n")
	la("thư lồng không lấy tệp", T.doc_thu(long)["tep"], [])


# ------------------------------------------------------------ sáu bước, đường vào

def _n(**k):
	r = dict(kenh_nhan=T.KENH, duong_vao="Từ thư", trang_thai="Đã nhận", nhom="Tiền bán",
		trang_thai_tien="Đã thấy tiền về", so_chua_noi=0, so_da_noi=3, kiem_so_du="", phi_vuot=0, xac_nhan_luc=None)
	r.update(k)
	return r


@ca("v641 sáu bước: thư hợp lệ đủ năm bước thì chờ kế toán xác nhận; xác nhận xong là đã khép")
def _():
	b = T.buoc_nguon(_n())
	la("chờ xác nhận", (b["tt"], b["hien"], b["xac_nhan_duoc"]), ("xxxxxv", 6, 1))
	b = T.buoc_nguon(_n(xac_nhan_luc="2026-11-06 10:00:00"))
	la("đã khép", (b["tt"], b["hien"], b["ghi"], b["xac_nhan_duoc"]), ("xxxxxx", 7, "Đã khép", 0))
	b = T.buoc_nguon(_n(xac_nhan_luc="2026-11-06 10:00:00", so_chua_noi=1))
	la("xác nhận rồi mà số đổi thì bước 6 đỏ", b["tt"], "xxxxvd")


@ca("v641 sáu bước: tải tay chờ duyệt vàng ở bước 2, không xác nhận được; từ chối thì đỏ")
def _():
	b = T.buoc_nguon(_n(kenh_nhan="Tải tay", duong_vao="Chờ duyệt"))
	la("chờ duyệt", (b["tt"], b["hien"], b["xac_nhan_duoc"]), ("xvxxxn", 2, 0))
	b = T.buoc_nguon(_n(kenh_nhan="Tải tay", duong_vao="Từ chối", ly_do_duyet="Sai kỳ"))
	la("từ chối", (b["tt"][1], b["nhan"][1]), ("d", "Giám đốc đã từ chối: Sai kỳ"))
	b = T.buoc_nguon(_n(kenh_nhan="Tải tay", duong_vao="Đã duyệt"))
	la("đã duyệt thì được xác nhận", (b["tt"], b["xac_nhan_duoc"]), ("xxxxxv", 1))


@ca("v641 sáu bước: nguồn cũ trước khi có thư xám bước 2 nhưng vẫn lọc được theo bước kẹt sau")
def _():
	b = T.buoc_nguon(_n(kenh_nhan="Tải tay", duong_vao=None, trang_thai_tien="Lệch tiền về"))
	la("cũ, lệch tiền", (b["tt"], b["hien"]), ("xnxdxn", 4))
	la("đếm bước kẹt", T.dem_buoc([_n(kenh_nhan="Tải tay", duong_vao=None, trang_thai_tien="Lệch tiền về"),
		_n(trang_thai="Lỗi tệp", trang_thai_tien="Chưa đối chiếu"), _n(so_chua_noi=2), _n(), _n(xac_nhan_luc="x")]),
		{4: 1, 3: 1, 5: 1, 6: 1})
	dung("lọc bước 4 thấy nguồn cũ", V.buoc_ket(_n(kenh_nhan="Tải tay", duong_vao=None, trang_thai_tien="Lệch tiền về"), "4"))
	dung("bước lạ không làm vỡ", not V.buoc_ket(_n(), "9") and not V.buoc_ket(_n(), "x"))


@ca("v641 sáu bước: thẻ tín dụng theo phương trình dư nợ; phí vượt biểu là đỏ ở bước khớp tiền")
def _():
	la("thẻ khớp", T.buoc_nguon(_n(nhom="Thẻ tín dụng", trang_thai_tien="Không áp dụng", kiem_so_du="Khớp"))["tt"][3], "x")
	la("thẻ lệch", T.buoc_nguon(_n(nhom="Thẻ tín dụng", trang_thai_tien="Không áp dụng", kiem_so_du="Lệch"))["tt"][3], "d")
	la("thẻ gõ tay", T.buoc_nguon(_n(nhom="Thẻ tín dụng", trang_thai_tien="Không áp dụng", kiem_so_du="Gõ tay"))["tt"][3], "v")
	la("phí vượt", T.buoc_nguon(_n(phi_vuot=2544))["tt"][3], "d")
	la("chuyến đi không cần khớp tiền", T.buoc_nguon(_n(nhom="Chuyến đi", trang_thai_tien="Không áp dụng"))["tt"][3], "x")


@ca("v641 đường vào: chip lọc ở máy chủ cùng nghĩa với nhãn trên từng dòng")
def _():
	mau = [_n(), _n(duong_vao="Đã duyệt"), _n(duong_vao="Chờ duyệt"), _n(kenh_nhan="Tải tay", duong_vao="Chờ duyệt"),
		_n(kenh_nhan="Tải tay", duong_vao="Đã duyệt"), _n(kenh_nhan="Tải tay", duong_vao="Từ chối"),
		_n(kenh_nhan="Tải tay", duong_vao=None), _n(kenh_nhan="Email", duong_vao=None), _n(kenh_nhan="Email", duong_vao="")]
	for k, _ten in T.DUONG:
		for r in mau:
			la("%s / %s %s" % (k, r["kenh_nhan"], r["duong_vao"]), V.khop_loc(r, T.loc_duong(k)), T.duong_vao(r) == k)
	la("đếm", [T.duong_vao(r) for r in mau], ["thu", "thu", "cho_duyet", "cho_duyet", "da_duyet", "tu_choi", "cu", "cu", "cu"])


@ca("v641 tải tay rồi thư thật về cùng tệp: nguồn tải tay được xác thực bằng thư; từ chối thì đọc lại")
def _():
	moi = dict(thu="DST-1", duong_vao="Từ thư")
	la("chờ duyệt -> nâng", V.nang_cap_tu_thu(dict(kenh_nhan="Tải tay", duong_vao="Chờ duyệt"), T.KENH, moi), "nang")
	la("cũ -> nâng", V.nang_cap_tu_thu(dict(kenh_nhan="Tải tay", duong_vao=None), T.KENH, moi), "nang")
	la("từ chối -> đọc lại", V.nang_cap_tu_thu(dict(kenh_nhan="Tải tay", duong_vao="Từ chối"), T.KENH, moi), "doc_lai")
	la("đã từ thư -> thôi", V.nang_cap_tu_thu(dict(kenh_nhan=T.KENH, duong_vao="Từ thư"), T.KENH, moi), "")
	la("thư không chữ ký không nâng tệp tải tay", V.nang_cap_tu_thu(dict(kenh_nhan="Tải tay", duong_vao="Chờ duyệt"), T.KENH,
		dict(thu="DST-2", duong_vao="Chờ duyệt")), "")
	la("tải tay không nâng", V.nang_cap_tu_thu(dict(kenh_nhan="Tải tay", duong_vao="Chờ duyệt"), "Tải tay", moi), "")
	la("không có nguồn cũ", V.nang_cap_tu_thu(None, T.KENH, moi), "")
	# Ngược lại: nguồn từ thư bị tải tay lại cùng tệp (đọc lại) thì KHÔNG hạ xuống tải tay.
	giu = V.giu_khi_doc_lai(dict(kenh_nhan=T.KENH, duong_vao="Từ thư"), "Tải tay")
	dung("giữ kênh, đường vào, thư", all(k in giu for k in ("kenh_nhan", "duong_vao", "thu")))
	la("đã duyệt giữ kết luận", V.giu_khi_doc_lai(dict(kenh_nhan="Tải tay", duong_vao="Đã duyệt"), "Tải tay"), ("duong_vao",))


# ------------------------------------------------------------ thư chưa về

LICH = [dict(vendor="Shinhan POS", tan_suat="Hằng ngày", han_gio=12, ngay_lam_viec=1),
	dict(vendor="GrabFood", tan_suat="Hằng ngày", han_gio=12, ngay_lam_viec=0),
	dict(vendor="Thẻ tín dụng Shinhan", tan_suat="Hằng tháng", han_ngay=5)]


def _src(vendor, tu, den=None, kenh=T.KENH, tk=""):
	return dict(vendor=vendor, tai_khoan=tk, tu_ngay=tu, den_ngay=den or tu, kenh_nhan=kenh)


@ca("v641 thư chưa về: quá hạn 12:00 mà chưa có thư ngày hôm qua thì báo; tải tay không tính là thư đã về")
def _():
	hn = date(2026, 11, 11)  # thứ Tư
	ng = [_src("GrabFood", "2026-11-10", kenh="Tải tay"), _src("Shinhan POS", "2026-11-10")]
	ra = T.thu_thieu(LICH, hn, 13, ng, "2026-11-01")
	la("thiếu GrabFood", [(x["vendor"], x["ngay"]) for x in ra], [("GrabFood", "2026-11-10")])
	la("chưa tới hạn thì chưa báo", T.thu_thieu(LICH, hn, 11, ng, "2026-11-01"), [])
	la("trước ngày bật hộp thư không xét", T.thu_thieu(LICH, hn, 13, ng, "2026-11-11"), [])
	la("hộp thư chưa từng chạy thì không báo", T.thu_thieu(LICH, hn, 13, ng, None), [])


@ca("v641 thư chưa về: đối tác chỉ gửi ngày làm việc thì thứ Bảy, Chủ nhật không báo; báo cáo gộp kỳ vẫn tính")
def _():
	la("thứ Bảy", [x["vendor"] for x in T.thu_thieu(LICH[:1], date(2026, 11, 14), 13, [], "2026-11-01")], [])
	ng = [_src("Shinhan POS", "2026-11-13", "2026-11-15")]
	la("thứ Hai: báo cáo 13-15 gộp cuối tuần", T.thu_thieu(LICH[:1], date(2026, 11, 16), 13, ng, "2026-11-01"), [])


@ca("v641 thư chưa về: nguồn nhiều tài khoản xét từng tài khoản đã thấy 14 ngày; thư tháng sau hạn ngày")
def _():
	hn = date(2026, 11, 11)
	ng = [_src("GrabFood", "2026-11-09", tk="TCV"), _src("GrabFood", "2026-11-09", tk="NVHTN"), _src("GrabFood", "2026-11-10", tk="TCV")]
	la("thiếu NVHTN", [(x["tai_khoan"], x["ngay"]) for x in T.thu_thieu(LICH[1:2], hn, 13, ng, "2026-11-01")], [("NVHTN", "2026-11-10")])
	la("tháng: trước ngày 5 chưa báo", T.thu_thieu(LICH[2:], date(2026, 12, 4), 9, [], "2026-11-01"), [])
	la("tháng: ngày 5 chưa có sao kê tháng 11", [(x["vendor"], x["ngay"]) for x in T.thu_thieu(LICH[2:], date(2026, 12, 5), 9, [], "2026-11-01")],
		[("Thẻ tín dụng Shinhan", "2026-11")])
	ng = [_src("Thẻ tín dụng Shinhan", "2026-11-01", "2026-11-30")]
	la("tháng: có rồi", T.thu_thieu(LICH[2:], date(2026, 12, 5), 9, ng, "2026-11-01"), [])


# ------------------------------------------------------------ biểu phí Shinhan POS

@ca("v641 biểu phí: Shinhan POS gom phí theo loại thẻ; thu cao hơn biểu hợp đồng thì ra đúng số dư")
def _():
	from vagabond.khung.kiem_thu.thu_doi_soat_mau_579 import _shinhan_ngay

	kq = M.doc(_shinhan_ngay())
	la("gom ba nhóm", kq["them"]["phi_the"], [
		dict(the="MASTERCARD", vung="DOMESTIC", mdr=2.5, gop=240000, phi=6000, so=1),
		dict(the="NAPAS", vung="DOMESTIC", mdr=0.78, gop=95000, phi=741, so=1),
		dict(the="VISA", vung="DOMESTIC", mdr=1.44, gop=200000, phi=2880, so=1)])
	tong, ct = T.phi_vuot(kq["them"]["phi_the"], dict(noi_dia="1,44"))
	# 240.000 x 1,44% = 3.456 đ; bị thu 6.000 đ; dư 2.544 đ. Napas chưa khai biểu thì không kiểm.
	la("dư", (tong, [(x["the"], x["du"]) for x in ct]), (2544, [("MASTERCARD", 2544)]))
	la("biểu trống không kiểm", T.phi_vuot(kq["them"]["phi_the"], dict(noi_dia="")), (0, []))
	la("dưới ngưỡng không báo", T.phi_vuot([dict(the="VISA", vung="DOMESTIC", mdr=1.5, gop=100000, phi=1500, so=1)],
		dict(noi_dia="1,44"), 0.1), (0, []))


@ca("v641 biểu phí: ô Cài đặt nhận mọi cách điền hợp lý")
def _():
	for v, mong in (("1,44", 1.44), ("1.44", 1.44), ("1,44%", 1.44), (" 1.44 % ", 1.44), (1.44, 1.44), ("", 0.0),
			(None, 0.0), ("abc", 0.0), ("-2", 0.0)):
		la("so_bieu(%r)" % (v,), T.so_bieu(v), mong)
	la("Napas", T.bieu_cho("Napas", "DOMESTIC", dict(noi_dia="1,44", napas="0,78")), 0.78)
	la("quốc tế chưa khai", T.bieu_cho("VISA", "INTERNATIONAL", dict(noi_dia="1,44")), 0.0)


# ------------------------------------------------------------ máy chủ thư, lỗi

@ca("v641 máy chủ IMAP: để trống thì lấy máy chủ của hộp erp@ cùng tên miền; nhận nhiều cách ghi")
def _():
	hop = [dict(email_id="sales@khac.vn", email_server="mail.khac.vn", incoming_port=993),
		dict(email_id="erp@thevagabondpatisserie.com", email_server="mail9.matbao.net", incoming_port=0)]
	la("lấy erp@", T.chon_may_chu("doisoat@thevagabondpatisserie.com", "", 0, hop), ("mail9.matbao.net", 993))
	la("ghi kèm cổng", T.chon_may_chu("x@y.vn", "imaps://mail.y.vn:143/", 0, []), ("mail.y.vn", 143))
	la("không có gì", T.chon_may_chu("x@y.vn", "", 0, hop), ("", 993))
	la("sai mật khẩu", T.ly_do_imap("b'[AUTHENTICATIONFAILED] Authentication failed.'"), "sai mật khẩu hoặc tên đăng nhập hộp thư.")
	la("quá giờ", T.ly_do_imap("timed out"), "máy chủ thư không trả lời (quá giờ chờ).")


# ------------------------------------------------------------ tin Zalo (nội dung anh duyệt ở ảnh 7)

@ca("v641 tin Zalo: đúng số tiền, đúng chiều thiếu dư, không dấu gạch dài")
def _():
	t, d = T.tin_lech_tien("Shinhan POS", "ngày 05/11", 12418440, 12356880)
	la("lệch", (t, d), ("Lệch tiền về: Shinhan POS, ngày 05/11", ["Shinhan POS báo chuyển: 12.418.440 đ",
		"Ngân hàng nhận thật (SePay): 12.356.880 đ", "Thiếu: 61.560 đ"]))
	la("dư", T.tin_lech_tien("Payoo", "ngày 05/11", 1000, 1500)[1][2], "Dư: 500 đ")
	t, d = T.tin_phi_cao("Shinhan POS", "ngày 05/11", [dict(the="JCB", vung="DOMESTIC", mdr=2.2, bieu=1.44, du=61560, gop=8100000)], 412300)
	la("phí", d, ["Thẻ Jcb nội địa: thu 2,2%, hợp đồng 1,44%, dư 61.560 đ trên 8.100.000 đ", "Tháng này đã dư 412.300 đ."])
	t, d = T.tin_gia_danh("OnePay", "payment@onepay.vn", "2026-11-06 09:40:00", "Thư không có chữ ký số của onepay.vn.")
	la("giả danh", (t, d[0]), ("Chặn 1 thư tự xưng OnePay", "Người gửi ghi: payment@onepay.vn, 09:40 06/11"))
	t, d = T.tin_thieu_thu([dict(vendor="Payoo", tai_khoan="", ngay="2026-11-05"), dict(vendor="Thẻ tín dụng Shinhan",
		tai_khoan="", ngay="2026-10")], 1)
	la("thiếu thư", (t, d[:2]), ("Còn 2 thư đối soát chưa về", ["Payoo, ngày 05/11", "Thẻ tín dụng Shinhan, tháng 10/2026"]))
	t, d = T.tin_tai_tay("Dung", "ShopeeFood", "ngày 04/11", 9, 1845000, "ShopeeFood không gửi thư")
	la("tải tay", (t, d), ("Dung vừa tải tay 1 tệp đối soát, chờ Giám đốc duyệt",
		["ShopeeFood ngày 04/11, 9 dòng, 1.845.000 đ", "Lý do: ShopeeFood không gửi thư"]))
	tat_ca = [T.tin_gia_danh("A", "b", "", "c"), T.tin_thieu_thu([], 2), T.tin_hop_thu_loi("2026-11-06 10:15:00", "x"),
		T.tin_tep_loi("A", "b", "c"), T.tin_chua_thay_tien([dict(vendor="A", ky="b", tien=1)]),
		T.tin_don_thieu_erp([dict(vendor="A", ngay="2026-11-05", gio="14:32:00", tien=650000)])]
	chu = json.dumps(tat_ca, ensure_ascii=False)
	dung("không em dash, en dash", "\u2014" not in chu and "\u2013" not in chu)
	la("đơn thiếu", T.tin_don_thieu_erp([dict(vendor="OnePay", ngay="2026-11-05", gio="14:32:00", tien=650000)])[1][0],
		"OnePay 05/11 14:32: 650.000 đ")


@ca("v641 tin Zalo: mỗi tin đối soát có mã trong danh mục và nơi phát gọi đúng mã")
def _():
	import ast

	from vagabond import kenh_zalo as kz

	cay = ast.parse((Path(__file__).parents[2] / "doi_soat_thu.py").read_text(encoding="utf-8"))
	ma = sorted({k.value.value for n in ast.walk(cay) if isinstance(n, ast.Call) for k in n.keywords
		if k.arg == "ma_tin" and isinstance(k.value, ast.Constant)})
	la("chín mã", ma, sorted(["bgd_ds_tai_tay", "kt_ds_thu_gia_danh", "kt_ds_thieu_thu", "kt_ds_tep_loi", "kt_ds_lech_tien",
		"kt_ds_chua_thay_tien", "kt_ds_phi_cao", "kt_ds_don_thieu_erp", "ht_ds_hop_thu_loi"]))
	dung("đều có trong danh mục", all(m in kz.TIN for m in ma))
	la("điều kiện thư chưa về", kz.DIEU_KIEN.get("ds_thieu_thu"), "vagabond.doi_soat_thu.con_thieu_thu")


@ca("v641 màn Đối soát nhà cung cấp chạy thật trong node: hộp thư, tiến độ, đường vào, duyệt, xác nhận")
def _():
	goc = Path(__file__).parents[3]
	for tep, so in (("doi_soat_hop_thu_641.js", "14 dat, 0 hong"), ("doi_soat_vendor_579.js", "22 dat, 0 hong")):
		r = subprocess.run(["node", str(goc / "vagabond/khung/kiem_thu/hanh_vi" / tep)], capture_output=True, text=True, timeout=120)
		dung("%s chạy được: %s" % (tep, (r.stdout[-1500:] + r.stderr[-800:])), r.returncode == 0)
		dung("%s đủ số ca" % tep, so in r.stdout)

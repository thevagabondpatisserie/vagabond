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
	la("mười mã (v647 thêm bill không khớp đối tác)", ma, sorted(["bgd_ds_tai_tay", "kt_ds_thu_gia_danh", "kt_ds_thieu_thu",
		"kt_ds_tep_loi", "kt_ds_lech_tien", "kt_ds_chua_thay_tien", "kt_ds_phi_cao", "kt_ds_don_thieu_erp", "ht_ds_hop_thu_loi",
		"kt_ds_bill_lech"]))
	dung("đều có trong danh mục", all(m in kz.TIN for m in ma))
	la("điều kiện thư chưa về", kz.DIEU_KIEN.get("ds_thieu_thu"), "vagabond.doi_soat_thu.con_thieu_thu")


@ca("v641 màn Đối soát nhà cung cấp chạy thật trong node: hộp thư, tiến độ, đường vào, duyệt, xác nhận")
def _():
	goc = Path(__file__).parents[3]
	for tep, so in (("doi_soat_hop_thu_641.js", "17 dat, 0 hong"), ("doi_soat_vendor_579.js", "26 dat, 0 hong")):
		r = subprocess.run(["node", str(goc / "vagabond/khung/kiem_thu/hanh_vi" / tep)], capture_output=True, text=True, timeout=120)
		dung("%s chạy được: %s" % (tep, (r.stdout[-1500:] + r.stderr[-800:])), r.returncode == 0)
		dung("%s đủ số ca" % tep, so in r.stdout)


# ------------------------------------------------------------ Codex #544 vòng 1

class _Nem(Exception):
	pass


def _frappe_gia(ghi):
	from types import SimpleNamespace as NS

	def sql(q, *a, **k):
		return [[1]]
	return NS(db=NS(sql=sql, commit=lambda: ghi.append("commit"), rollback=lambda: ghi.append("rollback")),
		log_error=lambda *a, **k: ghi.append("log"), utils=NS(now_datetime=lambda: "2026-11-06 10:00:00"),
		throw=lambda m, exc=None, *a, **k: (_ for _ in ()).throw((exc or _Nem)(m)), PermissionError=_Nem)


class _ImapGia:
	def __init__(self, uids):
		self.uids = uids

	def uid(self, lenh, *a):
		if lenh == "search":
			return "OK", [b" ".join(str(u).encode() for u in self.uids)]
		return "OK", [(b"1 (BODY[] {3}", b"thu-%s" % a[0].encode())]

	def logout(self):
		pass


def _chay_doc(lan, loi_uid, trang):
	"""Chạy doc_hop_thu THẬT `lan` lượt với hộp thư giả có UID 5 và 6; _xu_ly
	nổ cho các UID trong loi_uid (đếm số lần thử). Trả (nhật ký thử, trạng thái)."""
	from unittest.mock import patch
	thu, ghi = [], []

	def xu_ly(tho, uid, ch):
		thu.append(uid)
		if uid in loi_uid:
			raise RuntimeError("CSDL tạm lỗi")
	luu = []
	with patch.object(T, "_frappe", lambda: _frappe_gia(ghi)), patch.object(T, "_ket_noi", lambda ch: _ImapGia([5, 6])), \
			patch.object(T, "_chon_thu_muc", lambda m, tm: 77), patch.object(T, "_xu_ly", xu_ly), \
			patch.object(T, "trang_thai", lambda: dict(trang)), \
			patch.object(T, "_ghi_trang_thai", lambda **k: trang.update(k) or dict(trang)), \
			patch.object(T, "_ghi_thu_loi", lambda tho, uid, ch, ly, dns=False: luu.append(uid), create=True):
		for _ in range(lan):
			T.doc_hop_thu(dict(thu_muc="INBOX"))
	return thu, trang, luu


@ca("Codex #544 F1: thư xử lý lỗi không bị bỏ qua: lượt sau thử lại, quá 3 lần mới ghi sổ lỗi rồi đi tiếp")
def _():
	thu, tt, luu = _chay_doc(2, {5}, {})
	la("hai lượt đều thử lại UID 5, chưa đọc UID 6", thu, [5, 5])
	la("mốc chưa vượt UID 5", int(tt.get("uid") or 0) < 5, True)
	dung("hộp thư báo đang có thư lỗi", "UID 5" in (tt.get("loi") or ""))
	thu, tt, luu = _chay_doc(4, {5}, {})
	la("3 lần lỗi rồi ghi sổ lỗi, đọc tiếp UID 6", (thu, luu, tt.get("uid")), ([5, 5, 5, 6], [5], 6))
	thu, tt, luu = _chay_doc(1, set(), {})
	la("không lỗi: đọc hết, mốc 6, trạng thái lành", (thu, tt.get("uid"), tt.get("loi")), ([5, 6], 6, ""))


@ca("Codex #544 F2: danh sách thư bị chặn, chờ duyệt, thư chưa về và số đếm hộp thư chỉ trong pháp nhân được xem")
def _():
	from unittest.mock import patch
	from types import SimpleNamespace as NS
	loc = []

	def get_all(dt, filters=None, **k):
		loc.append((dt, dict(filters or {})))
		return []

	def count(dt, filters=None):
		loc.append((dt, dict(filters or {})))
		return 0
	fr = NS(get_all=get_all, db=NS(count=count), utils=NS(nowdate=lambda: "2026-11-06", add_days=lambda d, n: d,
		now_datetime=lambda: __import__("datetime").datetime(2026, 11, 6, 13)), get_roles=lambda: ["Accounts User"])
	with patch.object(T, "_frappe", lambda: fr), patch.object(V, "_chan", lambda *a, **k: None), \
			patch.object(V, "_cong_ty_xem", lambda: ["A"]), \
			patch.object(T, "cau_hinh", lambda: dict(bat=1, dia_chi="", lich=[], nguoi_gui=[])), \
			patch.object(T, "trang_thai", lambda: {"ngay_bat": "2026-11-01"}), patch.object(T, "la_giam_doc", lambda: False):
		for l in ("chan", "tai_tay", "chua_ve"):
			V.ds_thu(l)
		V.hop_thu()
	thieu = [(dt, f) for dt, f in loc if f.get("company") != ["in", ["A"]]]
	la("mọi truy vấn đều lọc pháp nhân A", thieu, [])
	dung("có truy vấn", len(loc) >= 5)


@ca("Codex #544 F3: nguồn đã bị giám đốc từ chối không dùng được bản sửa của vendor")
def _():
	from contextlib import nullcontext
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	viec = []
	nguon = NS(name="N1", company="A", duong_vao="Từ chối", du_lieu=json.dumps(dict(ban_sua=[dict(khoa="K", vi_tri=1,
		nhom="ban", vendor="Grab", tai_khoan="", dong=dict(dau_noi_dung="moi"))])))
	with patch.object(V, "_chan", lambda *a, **k: None), patch.object(V, "_chan_cong_ty", lambda c: None), \
			patch.object(V, "khoa_doi_chieu", lambda *a, **k: nullcontext()), \
			patch.object(V.frappe.db, "get_value", lambda dt, f=None, *a, **k: NS(name="N1", company="A") if dt == V.DT_NGUON
				else NS(name="D1", nguon="N0", dau_noi_dung="cu", thuc_nhan=1), create=True), \
			patch.object(V.frappe, "get_doc", lambda *a, **k: nguon, create=True), \
			patch.object(V.frappe, "throw", lambda m, *a, **k: (_ for _ in ()).throw(_Nem(m))), \
			patch.object(V.frappe.db, "sql", lambda *a, **k: viec.append("sql"), create=True), \
			patch.object(V, "_chen_dong", lambda *a, **k: viec.append("chen")):
		try:
			V.dung_ban_sua("N1", "K", "cu")
			ra = "không chặn"
		except _Nem as e:
			ra = str(e)
	dung("chặn và nói lý do: " + ra, "từ chối" in ra)
	la("không đổi dòng nào", viec, [])
	la("từ chối thì bản sửa chờ chọn không hiện nữa", V._ban_sua_hien(dict(duong_vao="Từ chối"), json.loads(nguon.du_lieu)), [])


# ------------------------------------------------------------ Codex #544 vòng 2

def _chay_doc2(lan, trang, hong=None, uv=77, uids=(5, 6), gio=None, rong=(), may="mail.a.vn", tm="INBOX"):
	"""Chạy doc_hop_thu THẬT `lan` lượt. hong: {uid: số lần đầu nổ, hoặc
	"dns" để luôn ném LoiDnsTam}. gio: danh sách giờ của từng lượt. rong: UID
	mà máy chủ thư không trả nội dung. Trả (nhật ký thử, trạng thái, thư ghi lỗi)."""
	from unittest.mock import patch
	from types import SimpleNamespace as NS
	hong = dict(hong or {})
	thu, ghi, luu = [], [], []
	dong_ho = list(gio or ["2026-11-06 10:00:00"] * lan)
	bay = [dong_ho[0]]

	def xu_ly(tho, uid, ch):
		thu.append(uid)
		h = hong.get(uid)
		if h == "dns":
			raise K.LoiDnsTam("Timeout")
		if h:
			hong[uid] = h - 1
			raise RuntimeError("CSDL tạm lỗi")

	class Imap(_ImapGia):
		def uid(self, lenh, *a):
			if lenh == "fetch" and int(a[0]) in rong:
				return "OK", [b")"]
			return _ImapGia.uid(self, lenh, *a)

	fr = _frappe_gia(ghi)
	fr.utils = NS(now_datetime=lambda: bay[0])
	def ket_noi(ch):
		m = Imap(list(uids))
		m.vgb_may, m.vgb_cong = may, 993
		return m
	with patch.object(T, "_frappe", lambda: fr), patch.object(T, "_ket_noi", ket_noi), \
			patch.object(T, "_chon_thu_muc", lambda m, tm: uv), patch.object(T, "_xu_ly", xu_ly), \
			patch.object(T, "trang_thai", lambda: json.loads(json.dumps(trang))), \
			patch.object(T, "_ghi_trang_thai", lambda **k: trang.update(json.loads(json.dumps(k))) or dict(trang)), \
			patch.object(T, "_ghi_thu_loi", lambda tho, uid, ch, ly, dns=False: luu.append((uid, dns))):
		for i in range(lan):
			bay[0] = dong_ho[i]
			T.doc_hop_thu(dict(thu_muc=tm, dia_chi="doisoat@x.vn"))
	return thu, trang, luu


@ca("Codex #544 vòng 2 F1: hộp thư đổi UIDVALIDITY mà thư đầu lỗi thì lượt sau vẫn đọc thư mới từ đầu, không lấy UID cũ")
def _():
	# Đúng chuỗi Codex: mốc cũ validity 66 / UID 100, hộp mới validity 77, UID 5 lỗi lần đầu.
	thu, tt, luu = _chay_doc2(2, {"uidvalidity": 66, "uid": 100}, hong={5: 1})
	la("lượt 2 đọc lại UID 5 rồi UID 6", thu, [5, 5, 6])
	la("mốc theo hộp mới", (tt.get("uidvalidity"), tt.get("uid")), (77, 6))
	# Lượt đầu chỉ ghi mốc mới, không thư nào lỗi: vẫn bỏ mốc cũ.
	thu, tt, luu = _chay_doc2(1, {"uidvalidity": 66, "uid": 100, "loi_uid": {"5": 2}})
	la("hộp mới đọc từ đầu, bỏ đếm lỗi cũ", (thu, tt.get("uid"), tt.get("loi_uid")), ([5, 6], 6, {}))
	la("THUẦN: đổi validity thì mốc về 0", T.moc_doc({"uidvalidity": 66, "uid": 100, "loi_uid": {"5": 1}}, 77),
		dict(uid=0, loi_uid={}, dns_tu={}, doi=True))
	la("THUẦN: cùng validity giữ mốc", T.moc_doc({"uidvalidity": 77, "uid": 9, "loi_uid": {"10": 1}}, 77)["uid"], 9)


@ca("Codex #544 vòng 2 (thêm): máy chủ thư không trả nội dung thư thì không vượt im lặng, thử lại rồi ghi sổ lỗi")
def _():
	thu, tt, luu = _chay_doc2(4, {"uidvalidity": 77, "uid": 4}, rong=(5,))
	la("không gọi xử lý thư rỗng, 3 lần mới ghi sổ lỗi rồi đọc UID 6", (thu, luu, tt.get("uid")), ([6], [(5, False)], 6))
	thu, tt, luu = _chay_doc2(1, {"uidvalidity": 77, "uid": 4}, rong=(5,))
	la("lượt đầu dừng ở UID 5, chưa đọc UID 6", (thu, tt.get("uid")), ([], 4))
	dung("báo lỗi thư trên hộp thư", "UID 5" in (tt.get("loi") or ""))


@ca("Codex #544 vòng 2 F3: tra khoá DKIM lỗi tạm thì không chặn thư: thử lại tới 24 giờ, quá hạn mới ghi Lỗi xử lý")
def _():
	gio = ["2026-11-06 %02d:00:00" % h for h in range(10, 16)] + ["2026-11-07 09:59:00", "2026-11-07 10:00:00", "2026-11-07 10:15:00"]
	thu, tt, luu = _chay_doc2(7, {"uidvalidity": 77, "uid": 4}, hong={5: "dns"}, gio=gio)
	la("6 lượt trong ngày vẫn thử lại (quá 3 lần), chưa ghi lỗi, chưa đọc UID 6", (thu, luu, tt.get("uid")), ([5] * 7, [], 4))
	dung("hộp thư nói rõ đang chờ tra khoá", "tra khoá" in (tt.get("loi") or ""))
	thu, tt, luu = _chay_doc2(9, {"uidvalidity": 77, "uid": 4}, hong={5: "dns"}, gio=gio)
	la("đủ 24 giờ mới ghi Lỗi xử lý (kiểu DNS) rồi đọc UID 6", (thu, luu, tt.get("uid")), ([5] * 8 + [6], [(5, True)], 6))
	la("THUẦN: 23 giờ 59 thử lại, 24 giờ ghi lỗi",
		(T.xu_ly_loi(9, "2026-11-06 10:00:00", "2026-11-07 09:59:00"), T.xu_ly_loi(1, "2026-11-06 10:00:00", "2026-11-07 10:00:00")),
		("thu_lai", "ghi_loi"))


@ca("Codex #544 vòng 2 F3: thư ký thật mà tra khoá lỗi tạm thì chưa kết luận; DNS trả lời không có khoá mới là chặn")
def _():
	def tam(ten):
		raise K.LoiDnsTam("Timeout")
	tho = _thu("relaxed.eml")
	r = K.kiem_thu(tho, tam)
	la("chữ ký chưa kiểm được, đánh dấu tạm", [(x["dat"], bool(x.get("tam"))) for x in r], [(False, True)])
	t = T.doc_thu(tho)
	qd = T.quyet_dinh(t["mien"], t["so_from"], r, NG)
	la("phải đọc lại, không kết luận chặn", T.phai_doc_lai_dns(qd["ket_qua"], r), True)
	r2 = K.kiem_thu(tho, lambda ten: None)
	qd2 = T.quyet_dinh(t["mien"], t["so_from"], r2, NG)
	la("DNS chắc chắn không có khoá: chặn, không đọc lại", (qd2["ket_qua"], T.phai_doc_lai_dns(qd2["ket_qua"], r2)), (T.KQ_CHAN, False))
	qd3 = T.quyet_dinh(t["mien"], t["so_from"], _kiem(tho), NG)
	la("DNS ổn: nhận", (qd3["ket_qua"], T.phai_doc_lai_dns(qd3["ket_qua"], _kiem(tho))), (T.KQ_XAC_THUC, False))


@ca("Codex #544 vòng 2 F3: _xu_ly với DNS lỗi tạm không ghi sổ thư, không đánh dấu xong; lần sau tra khoá lại")
def _():
	from unittest.mock import patch
	from types import SimpleNamespace as NS
	tra, viec = [], []

	def lay(ten):
		tra.append(ten)
		raise K.LoiDnsTam("Timeout")
	fr = NS(db=NS(get_value=lambda *a, **k: None),
		get_doc=lambda *a, **k: viec.append("ghi") or NS(insert=lambda **k: viec.append("insert"), db_set=lambda *a, **k: None))
	tho = _thu("relaxed.eml")
	with patch.object(T, "_frappe", lambda: fr), patch.object(K, "lay_khoa_dns", lay), patch.object(V, "_cong_ty", lambda: "A"):
		for _ in range(2):
			try:
				T._xu_ly(tho, 5, dict(nguoi_gui=NG))
				ra = "không ném"
			except K.LoiDnsTam:
				ra = "LoiDnsTam"
			la("lượt xử lý ném lỗi tạm", ra, "LoiDnsTam")
	la("hai lượt tra khoá hai lần", len(tra), 2)
	la("không ghi sổ thư nào", viec, [])


@ca("Codex #544 vòng 2 F3: bộ tra DNS: hết giờ, máy chủ lỗi, mất mạng là lỗi tạm; NXDOMAIN, không có TXT là không có khoá")
def _():
	import sys
	import types
	from unittest.mock import patch
	la("DoH Status 3 (NXDOMAIN)", K.txt_doh({"Status": 3}), None)
	la("DoH Status 0 không có TXT", K.txt_doh({"Status": 0, "Answer": [{"type": 5, "data": "x"}]}), None)
	la("DoH Status 0 có TXT", K.txt_doh({"Status": 0, "Answer": [{"type": 16, "data": '"v=DKIM1; " "p=AB"'}]}), b"v=DKIM1; p=AB")
	for d in ({"Status": 2}, {"Status": 5}, {}, "x", None):
		try:
			K.txt_doh(d)
			ra = "trả"
		except K.LoiDnsTam:
			ra = "tạm"
		la("DoH %r là lỗi tạm" % (d,), ra, "tạm")

	class Timeout(Exception):
		pass

	class NXDOMAIN(Exception):
		pass

	class NoAnswer(Exception):
		pass
	for loi, mong in ((Timeout, "tạm"), (NXDOMAIN, None), (NoAnswer, None), (OSError, "tạm")):
		res = types.ModuleType("dns.resolver")
		res.NXDOMAIN, res.NoAnswer = NXDOMAIN, NoAnswer

		def resolve(*a, _l=loi, **k):
			raise _l("x")
		res.resolve = resolve
		goc = types.ModuleType("dns")
		goc.resolver = res
		goc.exception = types.ModuleType("dns.exception")
		with patch.dict(sys.modules, {"dns": goc, "dns.resolver": res, "dns.exception": goc.exception}):
			try:
				ra = K.lay_khoa_dns("s._domainkey.onepay.vn")
			except K.LoiDnsTam:
				ra = "tạm"
		la("dnspython %s" % loi.__name__, ra, mong)

	class Req:
		@staticmethod
		def get(*a, **k):
			raise OSError("mất mạng")
	with patch.dict(sys.modules, {"dns": None, "requests": Req}):
		try:
			ra = K.lay_khoa_dns("s._domainkey.onepay.vn")
		except K.LoiDnsTam:
			ra = "tạm"
	la("DoH mất mạng là lỗi tạm", ra, "tạm")


def _nguon_tu_choi(tt="Cần xử lý"):
	from types import SimpleNamespace as NS
	return {"sha-1": NS(name="N9", trang_thai=tt, company="B", kenh_nhan="Tải tay", duong_vao="Từ chối")}


@ca("Codex #544 vòng 2 F2: tệp đã bị giám đốc từ chối không quay về Chờ duyệt khi tải lại, thư kênh cũ hay thư không chữ ký")
def _():
	from vagabond.khung.kiem_thu.thu_doi_soat_khop_579 import _goi_tai_tay
	url = "/private/files/bc.csv"
	for tt in ("Cần xử lý", "Lỗi tệp", "Đã nhận"):
		ra, nk = _goi_tai_tay("nhan", dict(file_url=url, cong_ty="B"), nguon_cu=_nguon_tu_choi(tt))
		la("tải tay lại (nguồn %s): không ghi gì" % tt, nk["ghi"], [])
		la("trả về đã có, bị từ chối", [(x.get("name"), x.get("tu_choi")) for x in ra], [("N9", 1)])
		ra, nk = _goi_tai_tay("xem_truoc", dict(file_url=url, cong_ty="B"), nguon_cu=_nguon_tu_choi(tt))
		la("xem trước nói rõ đã bị từ chối, không mời đọc lại (%s)" % tt, [(x["da_co"], x["doc_lai"], x.get("tu_choi")) for x in ra],
			[("N9", "", 1)])
	for kenh, them in (("Email", None), (T.KENH, {"duong_vao": "Chờ duyệt", "thu": "T1"})):
		ra, nk = _goi_tai_tay("_nhan_byte", dict(ten="bc.csv", byte=b"x", kenh=kenh, cong_ty="B", them=them),
			nguon_cu=_nguon_tu_choi())
		la("%s: không ghi, không đổi đường vào" % kenh, nk["ghi"], [])
	ra, nk = _goi_tai_tay("_nhan_byte", dict(ten="bc.csv", byte=b"x", kenh=T.KENH, cong_ty="B",
		them={"duong_vao": "Từ thư", "thu": "T2"}), nguon_cu=_nguon_tu_choi())
	la("đúng một lối mở lại: cùng tệp về qua thư có chữ ký", nk["ghi"], [("B", "N9")])


@ca("Codex #544 vòng 2 F2: lớp thứ hai ở cửa ghi nguồn: ghi lại nguồn từ chối bị chặn trước khi gỡ dòng cũ")
def _():
	from unittest.mock import patch
	from types import SimpleNamespace as NS
	viec = []
	cu = NS(name="N9", duong_vao="Từ chối", kenh_nhan="Tải tay")
	with patch.object(V.frappe.db, "get_value", lambda *a, **k: cu, create=True), \
			patch.object(V.frappe, "throw", lambda m, *a, **k: (_ for _ in ()).throw(_Nem(m))), \
			patch.object(V, "_bo_dong_cu", lambda n: viec.append("go") or []):
		for kenh, them in (("Tải tay", {"duong_vao": "Chờ duyệt"}), ("Email", None), (T.KENH, {"duong_vao": "Chờ duyệt"})):
			try:
				V._ghi_nguon("B", dict(ten="bc.csv", sha256="sha-1"), {}, {}, kenh, None, None, co_san="N9", them=them)
				ra = "không chặn"
			except _Nem as e:
				ra = str(e)
			dung("%s: chặn và nói lý do (%s)" % (kenh, ra), "từ chối" in ra)
	la("không gỡ dòng cũ nào", viec, [])
	la("THUẦN: chỉ thư có chữ ký mở lại được", [V.da_tu_choi_khoa(cu, k, t) for k, t in (
		("Tải tay", None), (T.KENH, {"duong_vao": "Chờ duyệt"}), (T.KENH, {"duong_vao": "Từ thư"}))], [True, True, False])
	la("THUẦN: nguồn không từ chối thì không chặn", V.da_tu_choi_khoa(NS(duong_vao="Chờ duyệt"), "Tải tay", None), False)


@ca("Codex #544 vòng 2: nút Đọc lại thư chỉ cho thư Lỗi xử lý, chạy lại đúng đường đọc thư, DNS lỗi tạm thì báo thử lại")
def _():
	import hashlib
	from unittest.mock import patch
	from types import SimpleNamespace as NS
	tho = _thu("relaxed.eml")
	sha = hashlib.sha256(tho).hexdigest()
	chay = []

	def lam(thu, xu_ly):
		ghi = []
		fr = _frappe_gia(ghi)
		fr.ValidationError = _Nem

		def get_value(dt, name, f=None, as_dict=False):
			if f == "sha256":
				return thu.get("sha256", sha)
			if isinstance(f, list) and "tep_goc" in f:
				return NS(**thu) if thu else None
			return NS(ket_qua=thu.get("ket_qua_sau", thu.get("ket_qua")), ly_do="")
		fr.db.get_value = get_value
		fr.get_doc = lambda *a, **k: NS(get_content=lambda: tho)
		fr.get_all = lambda *a, **k: []
		with patch.object(T, "_frappe", lambda: fr), patch.object(T, "_xu_ly", xu_ly), patch.object(T, "cau_hinh", lambda: {}):
			try:
				return T.doc_lai_thu("THU-1"), ghi
			except _Nem as e:
				return str(e), ghi

	def ok(t, u, c, kiem_lai=False, giu_xac_thuc=False):
		chay.append(u)
	ra, ghi = lam(dict(name="THU-1", ket_qua=T.KQ_LOI, xong=0, tep_goc="/private/files/a.eml", uid="5",
		ket_qua_sau=T.KQ_XAC_THUC), ok)
	la("đọc lại chạy _xu_ly đúng UID, commit", (chay, "commit" in ghi, getattr(ra, "ket_qua", ra)), (["5"], True, T.KQ_XAC_THUC))
	# v643: thư Bị chặn nay kiểm lại được (ca riêng trong thu_doi_soat_643); thư
	# Đã xác thực không còn nguồn cần đọc lại vẫn bị từ chối.
	for thu, y in ((dict(name="THU-1", ket_qua=T.KQ_XAC_THUC, xong=1, tep_goc="x", uid="5"), "đã xử lý xong"),
			(dict(name="THU-1", ket_qua=T.KQ_LOI, xong=0, tep_goc="", uid="5"), "không lưu được bản gốc"),
			(dict(name="THU-1", ket_qua=T.KQ_LOI, xong=0, tep_goc="x", uid="5", sha256="khac"), "không còn khớp")):
		chay.clear()
		ra, ghi = lam(thu, ok)
		dung("chặn: %s (%s)" % (y, ra), y in str(ra) and chay == [])

	def dns(t, u, c, kiem_lai=False, giu_xac_thuc=False):
		raise K.LoiDnsTam("Timeout")
	ra, ghi = lam(dict(name="THU-1", ket_qua=T.KQ_LOI, xong=0, tep_goc="x", uid="5"), dns)
	dung("DNS lỗi tạm: báo thử lại sau, lùi giao dịch (%s)" % ra, "Thử lại sau" in str(ra) and "rollback" in ghi)


# ------------------------------------------------------------ Codex #544 vòng 3

@ca("Codex #544 vòng 3 F1: đổi máy chủ, tài khoản hay thư mục mà UIDVALIDITY trùng số thì mốc vẫn về 0, đọc đủ thư mới")
def _():
	cu = T.danh_hop("mail.cu.vn", 993, "doisoat@x.vn", "INBOX")
	# Đúng chuỗi Codex: mốc validity 1 / UID 100 của hộp cũ, hộp mới cũng validity 1, thư 5 và 6.
	thu, tt, luu = _chay_doc2(2, {"uidvalidity": 1, "uid": 100, "hop": cu}, uv=1, may="mail.moi.vn")
	la("đổi máy chủ: đọc 5 và 6, mốc của hộp mới", (thu, tt.get("uid"), tt.get("hop")),
		([5, 6], 6, T.danh_hop("mail.moi.vn", 993, "doisoat@x.vn", "INBOX")))
	thu, tt, luu = _chay_doc2(1, {"uidvalidity": 1, "uid": 100, "hop": cu}, uv=1, may="mail.cu.vn", tm="Doi soat")
	la("đổi thư mục: đọc 5 và 6", thu, [5, 6])
	thu, tt, luu = _chay_doc2(1, {"uidvalidity": 1, "uid": 4, "hop": cu}, uv=1, may="MAIL.CU.VN")
	la("cùng hộp (máy chủ viết hoa khác): giữ mốc, chỉ đọc thư mới", (thu, tt.get("uid")), ([5, 6], 6))
	thu, tt, luu = _chay_doc2(1, {"uidvalidity": 1, "uid": 5}, uv=1, may="mail.cu.vn")
	la("mốc cũ chưa có danh tính: nhận danh tính, không đọc lại từ đầu", (thu, tt.get("hop")), ([6], cu))
	la("THUẦN: danh tính khác tài khoản", T.danh_hop("m", 993, "a@x", "INBOX") != T.danh_hop("m", 993, "b@x", "INBOX"), True)
	la("THUẦN: inbox viết thường là INBOX", T.danh_hop("M.", 0, "A@X", "inbox"), "m:993|a@x|INBOX")


@ca("Codex #544 vòng 3 F2: thư có chữ ký về đúng lúc giám đốc bấm Từ chối hay Duyệt: đọc lại trong khoá, không đè nguồn Từ thư")
def _():
	from contextlib import contextmanager
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	viec = []
	db = {"N1": dict(name="N1", company="A", owner="kt@x", duong_vao="Chờ duyệt", kenh_nhan="Tải tay", thu=None)}

	@contextmanager
	def khoa(*a, **k):
		# Lượt đọc hộp thư giữ khoá trước và nâng nguồn lên Từ thư; giám đốc
		# chờ khoá xong mới vào.
		db["N1"].update(duong_vao="Từ thư", kenh_nhan=T.KENH, thu="THU-2")
		viec.append("khoa")
		yield

	def get_value(dt, name, f=None, as_dict=False):
		return NS(**db[name]) if dt == T.DT_NGUON else None
	ghi = []
	fr = _frappe_gia(ghi)
	fr.db.get_value = get_value
	fr.db.set_value = lambda *a, **k: viec.append(("ghi",) + a[:2])
	fr.session = NS(user="gd@x")
	fr.utils.now_datetime = lambda: "2026-11-06 10:00:00"
	for ham, tham in ((T.tu_choi, ("N1", "Số liệu sai")), (T.duyet, ("N1",))):
		db["N1"].update(duong_vao="Chờ duyệt", kenh_nhan="Tải tay", thu=None)
		viec.clear()
		with patch.object(T, "_frappe", lambda: fr), patch.object(V, "_chan", lambda *a, **k: None), \
				patch.object(V, "_chan_cong_ty", lambda c: None), patch.object(V, "khoa_doi_chieu", khoa), \
				patch.object(V, "_bo_dong_cu", lambda n: viec.append("go_dong")), patch.object(T, "la_giam_doc", lambda: True):
			try:
				ham(*tham)
				ra = "không chặn"
			except _Nem as e:
				ra = str(e)
		dung("%s: chặn vì nguồn vừa đổi (%s)" % (ham.__name__, ra), "vừa đổi" in ra)
		la("%s: không gỡ dòng, không ghi gì" % ham.__name__, viec, ["khoa"])
		la("%s: nguồn vẫn Từ thư" % ham.__name__, db["N1"]["duong_vao"], "Từ thư")
	la("THUẦN: còn chờ duyệt", [T.con_cho_duyet(dict(duong_vao=d, kenh_nhan=k)) for d, k in (
		("Chờ duyệt", "Tải tay"), ("", "Tải tay"), ("Từ thư", T.KENH), ("", T.KENH), ("Từ chối", "Tải tay"))],
		[True, True, False, False, False])


@ca("Codex #544 vòng 3 (thêm): kế toán bấm Xác nhận đúng lúc giám đốc từ chối: đọc các bước trong khoá, không xác nhận nguồn đã từ chối")
def _():
	from contextlib import contextmanager
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	viec = []
	r = dict(name="N1", company="A", owner="kt@x", kenh_nhan=T.KENH, duong_vao="Từ thư", trang_thai="Đã nhận", nhom="Tiền bán",
		trang_thai_tien="Đã thấy tiền về", so_chua_noi=0, so_da_noi=5, kiem_so_du=1, phi_vuot=0, xac_nhan_luc=None, thu="T1")
	la("trước khi bị từ chối thì xác nhận được", T.buoc_nguon(r)["xac_nhan_duoc"], 1)

	@contextmanager
	def khoa(*a, **k):
		r.update(duong_vao="Từ chối")
		yield
	ghi = []
	fr = _frappe_gia(ghi)
	class D(dict):
		__getattr__ = dict.get
	fr.db.get_value = lambda dt, name, f=None, as_dict=False: D(r)
	fr.db.set_value = lambda *a, **k: viec.append("ghi")
	fr.session = NS(user="kt@x")
	with patch.object(T, "_frappe", lambda: fr), patch.object(V, "_chan", lambda *a, **k: None), \
			patch.object(V, "_chan_cong_ty", lambda c: None), patch.object(V, "khoa_doi_chieu", khoa), \
			patch.object(T, "_vai", lambda: {"Accounts User"}), patch.object(T, "la_giam_doc", lambda: False):
		try:
			T.xac_nhan("N1")
			ra = "không chặn"
		except _Nem as e:
			ra = str(e)
	dung("chặn: %s" % ra, ra.startswith("Chưa xác nhận được"))
	la("không ghi xác nhận", viec, [])


# ------------------------------------------------------------ Codex #544 vòng 4

def _db_xac_nhan():
	"""Nguồn N1 năm bước xanh, một dòng nối hoá đơn SI-A; bảng giả đủ cho
	xac_nhan, kiem_xac_nhan, buoc_nguon chạy THẬT."""
	from contextlib import nullcontext
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	class D(dict):
		__getattr__ = dict.get
	nguon = D(name="N1", company="A", owner="kt@x", kenh_nhan=T.KENH, duong_vao="Từ thư", trang_thai="Đã nhận", nhom="Tiền bán",
		trang_thai_tien="Đã thấy tiền về", giao_dich_ngan_hang="GD1", so_chua_noi=0, so_da_noi=1, kiem_so_du="", phi_vuot=0,
		thuc_nhan=100000.0, so_dong=1, xac_nhan_luc=None, xac_nhan_boi=None, xac_nhan_dau="", thu="T1")
	dong = [D(name="R1", nguon="N1", trang_thai_khop="Đã nối", sales_invoice="SI-A", purchase_invoice=None, van_don=None,
		thuc_nhan=100000, phi=0)]
	nhan_xet = []

	def get_value(dt, name, f=None, as_dict=False):
		if isinstance(f, (list, tuple)):
			return D({k: nguon.get(k) for k in f})
		return nguon.get(f)

	def set_value(dt, name, cap, *a, **k):
		nguon.update(cap)
	ghi = []
	fr = _frappe_gia(ghi)
	fr.db.get_value, fr.db.set_value = get_value, set_value
	fr.get_all = lambda dt, filters=None, fields=None, **k: [D({x: d.get(x) for x in fields}) for d in dong]
	fr.get_doc = lambda d: NS(insert=lambda **k: nhan_xet.append(d.get("content")))
	fr.session = NS(user="kt@x")
	fr.utils.now_datetime = lambda: "2026-11-06 10:00:00"
	vong = [patch.object(T, "_frappe", lambda: fr), patch.object(V, "_chan", lambda *a, **k: None),
		patch.object(V, "_chan_cong_ty", lambda c: None), patch.object(V, "khoa_doi_chieu", lambda *a, **k: nullcontext()),
		patch.object(T, "_vai", lambda: {"Accounts User"}), patch.object(T, "la_giam_doc", lambda: False)]
	return nguon, dong, nhan_xet, vong


@ca("Codex #544 vòng 4: hoá đơn nối bị huỷ rồi nối hoá đơn thay: xác nhận cũ hết hiệu lực, nguồn không tự về Đã khép, kế toán xác nhận lại")
def _():
	from contextlib import ExitStack
	nguon, dong, nhan_xet, vong = _db_xac_nhan()
	with ExitStack() as st:
		for v in vong:
			st.enter_context(v)
		T.xac_nhan("N1")
		dung("xác nhận ghi dấu số liệu", len(nguon.xac_nhan_dau or "") == 64)
		la("đối chiếu lại ra cùng kết quả: giữ xác nhận", (T.kiem_xac_nhan("N1"), T.buoc_nguon(nguon)["hien"]), (False, 7))
		# Hoá đơn SI-A bị huỷ: đối chiếu lại gỡ nối.
		dong[0].update(sales_invoice=None, trang_thai_khop="Chưa nối")
		nguon.update(so_chua_noi=1, so_da_noi=0)
		la("gỡ xác nhận cũ", (T.kiem_xac_nhan("N1"), nguon.xac_nhan_luc, nguon.xac_nhan_boi), (True, None, None))
		dung("ghi nhận xét để tra: " + str(nhan_xet), len(nhan_xet) == 1 and "hết hiệu lực" in nhan_xet[0])
		# Nối hoá đơn thay SI-B: số dòng như cũ nhưng chứng từ khác.
		dong[0].update(sales_invoice="SI-B", trang_thai_khop="Đã nối")
		nguon.update(so_chua_noi=0, so_da_noi=1)
		T.kiem_xac_nhan("N1")
		b = T.buoc_nguon(nguon)
		la("không tự về Đã khép, nút Xác nhận mở", (b["hien"], b["xac_nhan_duoc"], b["ghi"]), (6, 1, "Chờ kế toán xác nhận"))
		T.xac_nhan("N1")
		la("xác nhận lại thì khép", T.buoc_nguon(nguon)["hien"], 7)
		# Chỉ đổi giao dịch tiền về (trạng thái tiền vẫn khớp) cũng phải xác nhận lại.
		nguon.update(giao_dich_ngan_hang="GD2")
		la("đổi giao dịch tiền về: gỡ xác nhận", T.kiem_xac_nhan("N1"), True)
	a = T.dau_doi_chieu(dict(thuc_nhan=1.0), [dict(name="R2", sales_invoice="X"), dict(name="R1", sales_invoice="Y")])
	b = T.dau_doi_chieu(dict(thuc_nhan=1), [dict(name="R1", sales_invoice="Y"), dict(name="R2", sales_invoice="X")])
	la("THUẦN: dấu không phụ thuộc thứ tự dòng, 1.0 bằng 1", a, b)
	la("THUẦN: đổi hoá đơn nối là dấu khác", a != T.dau_doi_chieu(dict(thuc_nhan=1), [dict(name="R1", sales_invoice="Z"),
		dict(name="R2", sales_invoice="X")]), True)


@ca("Codex #544 vòng 4: mọi lối đối chiếu lại và nối tay đều kiểm lại xác nhận của kế toán")
def _():
	from contextlib import nullcontext
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	viec = []
	nguon = NS(name="N1", nhom="Tiền bán", trang_thai_tien="Đã thấy tiền về", get=lambda k, d=None: None,
		db_set=lambda *a, **k: None)
	with patch.object(V.frappe, "get_doc", lambda *a, **k: nguon, create=True), \
			patch.object(V.frappe, "get_all", lambda *a, **k: [], create=True), \
			patch.object(V, "_noi_hoa_don_ban", lambda n, d: viec.append("noi")), patch.object(V, "_tien_ve", lambda n: None), \
			patch.object(V, "_dem_noi", lambda n: viec.append("dem")), \
			patch.object(T, "sau_doi_chieu", lambda n, t: viec.append("sau")), \
			patch.object(T, "kiem_xac_nhan", lambda n: viec.append(("kiem", n))):
		V._doi_chieu("N1")
	la("đối chiếu lại: kiểm xác nhận sau cùng", viec, ["noi", "dem", "sau", ("kiem", "N1")])
	viec.clear()

	def get_value(dt, name, f=None, as_dict=False):
		return NS(name="R1", nguon="N1", company="A", trang_thai_khop="Nối theo tiền", sales_invoice="SI-A")
	with patch.object(V, "_chan", lambda *a, **k: None), patch.object(V, "_chan_cong_ty", lambda c: None), \
			patch.object(V, "khoa_doi_chieu", lambda *a, **k: nullcontext()), patch.object(V, "_goi_y_con_dung", lambda n: True), \
			patch.object(V, "_kieu_nguon", lambda n: "grab"), \
			patch.object(V.frappe.utils, "now", lambda: "2026-11-06 10:00:00", create=True), \
			patch.object(V.frappe, "session", NS(user="kt@x"), create=True), \
			patch.object(V.frappe.db, "get_value", get_value, create=True), \
			patch.object(V.frappe.db, "set_value", lambda *a, **k: viec.append("ghi"), create=True), \
			patch.object(V.frappe, "get_all", lambda *a, **k: [], create=True), \
			patch.object(V.frappe, "get_doc", lambda *a, **k: nguon, create=True), \
			patch.object(V, "_dem_noi", lambda n: viec.append("dem")), \
			patch.object(T, "kiem_xac_nhan", lambda n: viec.append(("kiem", n))):
		V.xac_nhan_noi("R1")
	la("nối tay theo tiền: kiểm xác nhận sau khi đếm", viec, ["ghi", "dem", ("kiem", "N1")])


# ------------------------------------------------------------ v642

@ca("v642: gieo mặc định trên Cài đặt lõi (doctype Single, không có bảng riêng) không gọi has_column, gieo đủ dòng một lần")
def _():
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	viec, loi, toan_cuc = [], [], {}

	def has_column(dt, col):
		# Đúng hành vi ERPNext thật với doctype Single (site 06/11/2026).
		raise RuntimeError("TableMissingError: DocType %s" % dt)
	fr = NS(db=NS(has_column=has_column, table_exists=lambda dt: True, get_global=lambda k: toan_cuc.get(k),
		set_global=lambda k, v: toan_cuc.__setitem__(k, v), count=lambda dt, f=None: 0,
		get_single_value=lambda dt, f: None, set_single_value=lambda dt, f, v: None),
		get_meta=lambda dt: NS(has_field=lambda f: True),
		get_doc=lambda d: NS(db_insert=lambda: viec.append((d["doctype"], d["parentfield"]))),
		clear_document_cache=lambda *a: None, log_error=lambda *a, **k: loi.append(k.get("title") or a))
	with patch.object(T, "_frappe", lambda: fr):
		T.gieo_mac_dinh()
		la("không ghi lỗi", loi, [])
		la("gieo đủ người gửi và lịch thư", (sum(1 for x in viec if x[1] == "ds_nguoi_gui"), sum(1 for x in viec if x[1] == "ds_lich_thu")),
			(len(T.NGUOI_GUI_MAC_DINH), len(T.LICH_MAC_DINH)))
		la("đánh dấu đã gieo", toan_cuc.get("vgb_ds_thu_gieo"), "1")
		viec.clear()
		T.gieo_mac_dinh()
		la("lượt migrate sau không gieo lại", viec, [])

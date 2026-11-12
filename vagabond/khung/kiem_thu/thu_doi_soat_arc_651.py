"""v651 (anh Việt 12/11/2026, hướng B): thư Shinhan nhận qua chuỗi ARC của Gmail.

Thư Shinhan 09/11 đến 12/11 (DST-2611-06588, 06670, 06768, 06854) ký DKIM bằng
bccardvn.com nhưng thân thư bị sửa SAU khi ký (Gmail lúc nhận cũng ghi "body
hash did not verify"), nên máy chặn. Gmail của tiệm ghi SPF đạt cho
admin@shinhan.com.vn vào ARC-Authentication-Results và google.com niêm phong
bằng ARC-Seal. Máy chỉ tin kết quả đó khi cả chuỗi ARC kiểm đạt, mọi bộ do
google.com niêm phong, và CHỈ cho đối tác trong TIN_ARC_GOOGLE.

Thư mẫu arc_*.eml do dkimpy 1.1 KÝ THẬT bằng khoá thử (bộ ký độc lập với bộ
kiểm của mình; dkimpy.arc_verify cho arc_shinhan.eml là pass). Thư thật không
đưa vào repo (có sao kê); đã kiểm riêng trên phần tiêu đề thật với khoá
arc-20260327 thật của google.com: đạt, sửa From hay sửa SPF thì hỏng.
"""
import json
from pathlib import Path
from unittest.mock import patch

from vagabond import doi_soat_dkim as K
from vagabond import doi_soat_thu as T
from vagabond.khung.kiem_thu.nen import ca, dung, la

THU_MUC = Path(__file__).parent / "mau_doi_soat" / "dkim"
DNS = json.loads((THU_MUC / "dns.json").read_text())
NG = [dict(ten=t, mien=T.tach_mien(m), bat_buoc=b) for t, m, b in T.NGUOI_GUI_MAC_DINH]
CH = dict(nguoi_gui=NG, noi_bo=list(T.NOI_BO_MAC_DINH))


def _thu(ten):
	return (THU_MUC / ten).read_bytes()


def _dns(ten):
	v = DNS.get(ten)
	return v.encode() if v else None


def _sua_aar1(tho):
	"""Đổi spf=softfail thành pass CHỈ trong ô ARC-Authentication-Results i=1."""
	dau = tho.index(b"ARC-Authentication-Results: i=1;")
	cuoi = tho.index(b"\r\n", tho.index(b"spf=softfail", dau))
	return tho[:dau] + tho[dau:cuoi].replace(b"spf=softfail", b"spf=pass") + tho[cuoi:]


def _quyet(tho, lay=_dns):
	with patch.object(K, "lay_khoa_dns", lay):
		return T._quyet(tho, T.doc_thu(tho), CH)


@ca("v651 ARC: thư Shinhan chữ ký bccardvn hỏng, chuỗi ARC google.com đạt, Gmail ghi SPF đạt: nhận")
def _():
	tho = _thu("arc_shinhan.eml")
	ck = K.kiem_thu(tho, _dns)
	la("chữ ký DKIM của bccardvn hỏng như thư thật", [(c["d"], c["dat"], c["ly_do"]) for c in ck],
		[("bccardvn.com", False, "Thân thư hoặc tệp đính kèm đã bị sửa sau khi đối tác ký.")])
	la("chuỗi ARC", K.kiem_arc(tho, _dns), dict(dat=True, spf_mien="shinhan.com.vn", ly_do="", tam=False))
	qd, ck = _quyet(tho)
	la("nhận", (qd["ket_qua"], qd["nguon"], qd["ky_boi"], qd["bao_zalo"]),
		(T.KQ_XAC_THUC, "Shinhan (POS và thẻ tín dụng)", "google.com (ARC)", 0))
	dung("lý do nói rõ SPF và ARC", "SPF đạt" in qd["ly_do"] and "google.com" in qd["ly_do"])
	la("sổ chữ ký ghi kèm dòng ARC", [(c["d"], c["s"], c["dat"]) for c in ck][-1], ("google.com", "arc", True))


@ca("v651 ARC: sửa thân thư, sửa From, sửa kết quả SPF đã niêm phong, bỏ chuỗi ARC đều KHÔNG nhận")
def _():
	tho = _thu("arc_shinhan.eml")
	ca_ = {
		"thân thư": tho.replace(b"Bao cao giao dich", b"Bao cao giao dick"),
		"ô From": tho.replace(b"From: \"BAIS\" <admin@shinhan.com.vn>", b"From: \"BAIS\" <admin@shinhan.com.vm>"),
		# Thư Gmail ghi SPF softfail, kẻ gian sửa thành pass trong ô đã niêm phong.
		"kết quả SPF bộ 1": _sua_aar1(_thu("arc_spf_khong_dat.eml")),
		"bỏ ARC": tho.replace(b"ARC-Seal:", b"X-ARC-Seal:").replace(b"ARC-Message-Signature:", b"X-AMS:")
			.replace(b"ARC-Authentication-Results:", b"X-AAR:"),
	}
	for ten, t in ca_.items():
		r = K.kiem_arc(t, _dns)
		dung("%s: không đạt (%s)" % (ten, r["ly_do"]), not r["dat"] and r["ly_do"])
		la("%s: thư không được nhận" % ten, _quyet(t)[0]["ket_qua"] == T.KQ_XAC_THUC, False)


@ca("v651 ARC: Gmail ghi SPF không đạt, hay một bộ do tên miền khác niêm phong: không nhận")
def _():
	r = K.kiem_arc(_thu("arc_spf_khong_dat.eml"), _dns)
	la("SPF softfail", (r["dat"], r["ly_do"]), (False, "Gmail không ghi SPF đạt cho người gửi."))
	r = K.kiem_arc(_thu("arc_mien_khac.eml"), _dns)
	la("bộ 1 do gmail-gia.example niêm phong", (r["dat"], r["ly_do"]), (False, "Chuỗi ARC có bộ không do google.com niêm phong."))
	for ten in ("arc_spf_khong_dat.eml", "arc_mien_khac.eml"):
		la("%s bị chặn" % ten, _quyet(_thu(ten))[0]["ket_qua"], T.KQ_CHAN)


@ca("v651 ARC chỉ cho Shinhan: cùng chuỗi ARC đạt nhưng người gửi là đối tác khác hay SPF của tên miền khác thì không nhận")
def _():
	arc = dict(dat=True, spf_mien="shinhan.com.vn", ly_do="", tam=False)
	ck = [dict(d="onepay.vn", dat=False, ly_do="Chữ ký không khớp.")]
	la("OnePay không mở ARC", T.quyet_dinh("onepay.vn", 1, ck, NG, arc)["ket_qua"], T.KQ_CHAN)
	la("OnePay dù Gmail ghi SPF đạt cho onepay.vn", T.quyet_dinh("onepay.vn", 1, ck, NG,
		dict(arc, spf_mien="onepay.vn"))["ket_qua"], T.KQ_CHAN)
	la("không cần kiểm ARC cho OnePay", T.can_kiem_arc("onepay.vn", ck, NG), False)
	la("Shinhan mà SPF ghi tên miền khác", T.quyet_dinh("shinhan.com.vn", 1, [], NG,
		dict(arc, spf_mien="evil.example"))["ket_qua"], T.KQ_CHAN)
	la("Shinhan có chữ ký đúng thì không cần ARC", T.can_kiem_arc("shinhan.com.vn",
		[dict(d="bccardvn.com", dat=True)], NG), False)
	la("Shinhan chữ ký hỏng thì kiểm ARC", T.can_kiem_arc("shinhan.com.vn",
		[dict(d="bccardvn.com", dat=False)], NG), True)


@ca("v651 ARC: tra khoá google.com lỗi tạm thì chưa kết luận, thư được đọc lại sau")
def _():
	def lay(ten):
		if ten.endswith("._domainkey.google.com"):
			raise K.LoiDnsTam("Timeout")
		return _dns(ten)
	qd, ck = _quyet(_thu("arc_shinhan.eml"), lay)
	la("chưa nhận", qd["ket_qua"] == T.KQ_XAC_THUC, False)
	la("phải đọc lại", T.phai_doc_lai_dns(qd["ket_qua"], ck), True)

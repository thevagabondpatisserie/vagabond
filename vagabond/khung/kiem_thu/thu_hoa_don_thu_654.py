# -*- coding: utf-8 -*-
"""v654 hoá đơn mua vào tự nhận XML, PDF từ hộp thư hoadon@ (anh Việt 13/11/2026).

Ca thật: HDM-26-11-00195, Hộ kinh doanh trái cây nhập khẩu An Phú, số 8882,
ngày 12/11/2026. Đo trên site 13/11: hộp thư bắt đầu được đọc 10:20, máy đọc từ
thư 13/08 lên 40 thư mỗi giờ, tới 11:17 mới tới thư 20/08.

Ca chốt:
  - đọc thư MỚI NHẤT trước; mốc v653 (một con trỏ) đổi đúng thành khoảng đã xong;
  - hoá đơn có trước thư, thư có trước hoá đơn: đều đính được;
  - người mua trên XML không phải công ty: không đính, ghi lý do;
  - thư gửi lại cùng hoá đơn: không tạo dòng thứ hai, chỉ bổ sung tệp còn thiếu;
  - chỉ XML, chỉ PDF, hai nhà cung cấp trùng số hoá đơn;
  - nhiều tờ M-Invoice trùng: không khớp bừa, ghi lý do;
  - quét lại thư cũ: chỉ bổ sung tệp, không trùng dòng, không trùng tệp;
  - màn Hoá đơn mua vào: nhãn XML, PDF theo tệp thật, thiếu thì có lý do.
"""

import json
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, gia_lap, la

fr = gia_lap()

from vagabond import hoa_don_thu as h  # noqa: E402
from vagabond.khung.kiem_thu import thu_hoa_don_thu_653 as c  # noqa: E402

CT = "0318561568"
AN_PHU = """<?xml version="1.0" encoding="UTF-8"?>
<HDon><DLHDon><TTChung><KHMSHDon>1</KHMSHDon><KHHDon>C26MYY</KHHDon><SHDon>8882</SHDon><NLap>2026-11-12</NLap></TTChung>
<NDHDon><NBan><Ten>HỘ KINH DOANH TRÁI CÂY NHẬP KHẨU AN PHÚ</Ten><MST>075191002965</MST></NBan>
<NMua><Ten>CÔNG TY TNHH PATISSERIE VAGABOND</Ten><MST>0318561568</MST></NMua>
<TToan><TgTTTBSo>820000</TgTTTBSo></TToan></NDHDon></DLHDon></HDon>""".encode()
PDF = b"%PDF-1.4 an phu 8882"
MI_AN_PHU = Doi(name="d271f6d8", mst_doi_tac="075191002965", so_hd="8882", ky_hieu="C26MYY", loai="Đầu vào")
DOC = __import__("vagabond.doi_soat_thu", fromlist=["x"]).doc_thu


def _kho(mi=True, pi="HDM-26-11-00195"):
	k = c.Kho()
	k.cong_ty = [CT]
	k.mi = [MI_AN_PHU] if mi else []
	k.pi = pi
	return k


def _thu(ma, tep):
	return c._thu(ma, [(t, b, ("application", "xml" if t.endswith(".xml") else "pdf")) for t, b in tep])


def _xl(kho, ma, tep, uid=1):
	return c._chay(kho, lambda: h.xu_ly_thu(h.doc_thu_hd(_thu(ma, tep), DOC), uid))


def _noi(kho):
	return sorted((x["attached_to_doctype"], x["attached_to_name"], x["file_name"]) for x in kho.tep if x["attached_to_doctype"] != h.DT)


@ca("v654 THUẦN: khoảng UID đã đọc, chọn thư mới nhất trước, đổi mốc v653, quét lại, ngày IMAP")
def _thuan():
	tat = list(range(1, 11))
	la("gộp khoảng liền", h.them_khoang([[1, 3]], [4, 5], tat), [[1, 5]])
	la("gộp qua UID không còn trong hộp thư", h.them_khoang([[1, 3]], [6], [1, 2, 3, 6, 7]), [[1, 6]])
	la("khoảng rời giữ rời", h.them_khoang([[1, 3]], [8], tat), [[1, 3], [8, 8]])
	la("mới nhất trước", h.chon_luot(tat, [[1, 3]], {}, 4), [10, 9, 8, 7])
	la("thư chờ đọc lại không tính là xong", h.chon_luot(tat, [[1, 10]], {5: 1}, 4), [5])
	la("mốc v653 {uid: 8935}: mọi thư tới 8935 đã xong", h.moc_khoang({"uid": 8935, "thu_lai": {"8900": 2}}, [8894, 8935, 9000]),
		([[8894, 8935]], {8900: 2}))
	la("mốc trống", h.moc_khoang({}, [1, 2]), ([], {}))
	la("quét lại từ UID 6", h.bo_tu([[1, 10]], 6), [[1, 5]])
	la("ngày IMAP", h.ngay_imap("2026-11-01"), "01-Nov-2026")
	la("người mua đúng công ty", h.nguoi_mua_sai("0318561568", [CT]), None)
	dung("người mua khác công ty có lý do", "0300000001" in h.nguoi_mua_sai("0300000001", [CT]))
	la("XML không ghi MST người mua (bán lẻ): không chặn", h.nguoi_mua_sai("", [CT]), None)


@ca("v654 hộp thư: thư mới nhất (12/11) được đọc ngay lượt đầu dù còn hàng trăm thư cũ; mốc v653 không đọc lại thư cũ")
def _moi_truoc():
	kho = _kho()
	thu = {u: c._thu("cu-%d" % u) for u in range(30, 120)}
	thu[200] = _thu("an-phu-8882", [("8882.xml", AN_PHU), ("8882.pdf", PDF)])
	kho.moc = json.dumps({"uv": 77, "uid": 40})
	may = c.Imap(thu)
	with um.patch("imaplib.IMAP4_SSL", may):
		r = c._chay(kho, lambda: h.doc_hop_thu(c.CH))
	doc = [int(x[2]) for x in may.lenh if x[:2] == ("uid", "fetch")]
	la("lượt đầu: đọc 40 thư, thư 12/11 đầu tiên", (r["so_thu"], doc[0], doc[1]), (40, 200, 119))
	dung("không đọc lại thư đã xong theo mốc cũ", min(doc) > 40)
	st = {d["tieu_de"]: d for d in kho.dong.values()}
	la("An Phú 8882 Đã đính ngay", (st["an-phu-8882"]["trang_thai"], st["an-phu-8882"]["hoa_don_mua"]), (h.TT_DINH, "HDM-26-11-00195"))
	la("XML vào hoá đơn mua, PDF vào M-Invoice", _noi(kho),
		[("MInvoice Invoice", "d271f6d8", "HDDT-C26MYY-8882-NCC.pdf"), ("Purchase Invoice", "HDM-26-11-00195", "XMLHD-1C26MYY-8882.xml")])
	m = json.loads(kho.moc)
	la("mốc mới: khoảng đã xong, còn bao nhiêu thư", (m["khoang"], m["con"]), ([[30, 40], [81, 200]], 40))
	may.lenh.clear()
	with um.patch("imaplib.IMAP4_SSL", may):
		c._chay(kho, lambda: h.doc_hop_thu(c.CH))
	doc2 = [int(x[2]) for x in may.lenh if x[:2] == ("uid", "fetch")]
	la("lượt sau đọc tiếp phần cũ còn lại, không đọc lại", (doc2[0], doc2[-1], len(doc2)), (80, 41, 40))


@ca("v654 hoá đơn có trước thư và thư có trước hoá đơn (ca An Phú 8882): đều đính đúng")
def _hai_chieu():
	kho = _kho()
	_xl(kho, "a", [("8882.xml", AN_PHU), ("8882.pdf", PDF)])
	la("hoá đơn có trước: Đã đính ngay", list(kho.dong.values())[0]["trang_thai"], h.TT_DINH)
	kho2 = _kho(mi=False, pi=None)
	_xl(kho2, "b", [("8882.xml", AN_PHU), ("8882.pdf", PDF)])
	d = list(kho2.dong.values())[0]
	la("thư có trước: Chờ khớp, có lý do", d["trang_thai"], h.TT_CHO)
	dung("lý do nói chờ M-Invoice", "Chưa thấy hoá đơn M-Invoice" in d["ghi_chu"] and "8882" in d["ghi_chu"])
	kho2.mi = [MI_AN_PHU]
	c._chay(kho2, h.khop_lai)
	la("M-Invoice về, chưa có hoá đơn mua: Thiếu tệp", d["trang_thai"], h.TT_THIEU)
	kho2.pi = "HDM-26-11-00195"
	c._chay(kho2, h.khop_lai)
	la("hoá đơn mua lập sau: Đã đính, đủ hai tệp", (d["trang_thai"], len(_noi(kho2))), (h.TT_DINH, 2))


@ca("v654 người mua trên XML không phải công ty: không đính vào đâu, ghi lý do cho kế toán")
def _nguoi_mua():
	kho = _kho()
	_xl(kho, "nham", [("8882.xml", AN_PHU.replace(b"0318561568", b"0300000001")), ("8882.pdf", PDF)])
	d = list(kho.dong.values())[0]
	la("trạng thái Lỗi, không đính hoá đơn nào", (d["trang_thai"], _noi(kho)), (h.TT_LOI, []))
	dung("lý do có MST sai", "0300000001" in d["ghi_chu"])


@ca("v654 thư gửi lại cùng hoá đơn: không tạo dòng thứ hai, chỉ bổ sung tệp còn thiếu; gửi lại y hệt không trùng tệp")
def _gui_lai():
	kho = _kho()
	_xl(kho, "lan1", [("8882.xml", AN_PHU)], uid=1)
	la("lần 1 chỉ XML", (len(kho.dong), [x[0] for x in _noi(kho)]), (1, ["Purchase Invoice"]))
	_xl(kho, "lan2", [("8882.xml", AN_PHU), ("8882.pdf", PDF)], uid=2)
	la("lần 2 khác mã thư: vẫn một dòng, thêm PDF", (len(kho.dong), [x[0] for x in _noi(kho)]), (1, ["MInvoice Invoice", "Purchase Invoice"]))
	n = len(kho.tep)
	_xl(kho, "lan3", [("8882.xml", AN_PHU), ("8882.pdf", PDF)], uid=3)
	la("lần 3 y hệt: không thêm tệp nào", (len(kho.dong), len(kho.tep)), (1, n))


@ca("v654 chỉ XML, chỉ PDF, hai nhà cung cấp trùng số hoá đơn")
def _ca_le():
	kho = _kho()
	_xl(kho, "xml", [("8882.xml", AN_PHU)])
	d = list(kho.dong.values())[0]
	la("chỉ XML: Đã đính, XML vào hoá đơn mua", (d["trang_thai"], _noi(kho)), (h.TT_DINH, [("Purchase Invoice", "HDM-26-11-00195", "XMLHD-1C26MYY-8882.xml")]))
	la("lý do trên màn khi thiếu PDF", h.ly_do_tep(True, False, d), "Thư hoá đơn của nhà cung cấp không kèm PDF. Cần thì xin nhà cung cấp gửi lại.")
	kho2 = _kho()
	_xl(kho2, "pdf", [("8882.pdf", PDF)])
	d2 = list(kho2.dong.values())[0]
	la("chỉ PDF: Lỗi, không đính hoá đơn mua", (d2["trang_thai"], _noi(kho2)), (h.TT_LOI, []))
	dung("lý do bảo đính tay", "đính tay" in d2["ghi_chu"])
	kho3 = _kho()
	khac = AN_PHU.replace(b"075191002965", b"0312345678").replace(b"C26MYY", b"C26TPH")
	kho3.mi = [MI_AN_PHU, Doi(name="MI-PHP-8882", mst_doi_tac="0312345678", so_hd="8882", ky_hieu="C26TPH", loai="Đầu vào")]
	_xl(kho3, "ap", [("8882.xml", AN_PHU), ("8882.pdf", PDF)], uid=1)
	_xl(kho3, "php", [("8882.xml", khac), ("8882.pdf", PDF + b"php")], uid=2)
	la("hai nhà cung cấp cùng số 8882: hai dòng, mỗi dòng đúng M-Invoice của mình",
		sorted((x["mst_ban"], x["hd_dien_tu"]) for x in kho3.dong.values()), [("0312345678", "MI-PHP-8882"), ("075191002965", "d271f6d8")])


@ca("v654 nhiều tờ M-Invoice trùng MST, số, ký hiệu: không khớp bừa, ghi lý do")
def _trung():
	kho = _kho()
	kho.mi = [MI_AN_PHU, Doi(name="d271-ban-sao", mst_doi_tac="075191002965", so_hd="08882", ky_hieu="1C26MYY", loai="Đầu vào")]
	_xl(kho, "a", [("8882.xml", AN_PHU), ("8882.pdf", PDF)])
	d = list(kho.dong.values())[0]
	la("Chờ khớp, không đính", (d["trang_thai"], _noi(kho)), (h.TT_CHO, []))
	dung("lý do: 2 tờ trùng, kế toán chọn tay", d["ghi_chu"].startswith("Có 2 hoá đơn M-Invoice"))


@ca("v654 quét lại thư cũ: đọc lại từ ngày chọn, chỉ bổ sung tệp còn thiếu, không trùng dòng, không trùng tệp")
def _quet_lai():
	kho = _kho()
	may = c.Imap({5: _thu("an-phu", [("8882.xml", AN_PHU), ("8882.pdf", PDF)])})
	with um.patch("imaplib.IMAP4_SSL", may):
		c._chay(kho, lambda: h.doc_hop_thu(c.CH))
	# Giả lập tệp PDF đính hỏng mất ở bản v653: xoá tệp PDF trên dòng thư và trên M-Invoice.
	kho.tep = [x for x in kho.tep if not x["file_name"].endswith(".pdf")]
	n_dong = len(kho.dong)
	with um.patch.object(fr, "get_roles", lambda *a, **k: ["Accounts Manager"], create=True), \
			um.patch.object(fr, "utils", Doi(getdate=lambda v: v, now_datetime=fr.utils.now_datetime), create=True):
		c._chay(kho, lambda: h.quet_lai("2026-11-01"))
	la("ghi mốc quét lại", json.loads(kho.moc)["quet_lai_tu"], "2026-11-01")
	may.lenh.clear()
	with um.patch("imaplib.IMAP4_SSL", may):
		c._chay(kho, lambda: h.doc_hop_thu(c.CH))
	dung("tìm thư từ 01/11", ("uid", "search", None, "SINCE", "01-Nov-2026") in may.lenh)
	la("đọc lại thư 5", [x[2] for x in may.lenh if x[:2] == ("uid", "fetch")], ["5"])
	la("không thêm dòng", len(kho.dong), n_dong)
	la("PDF bổ sung lại đúng một lần trên dòng thư và trên M-Invoice",
		sorted((x["attached_to_doctype"], x["file_name"]) for x in kho.tep if x["file_name"].endswith(".pdf")),
		[("MInvoice Invoice", "HDDT-C26MYY-8882-NCC.pdf"), (h.DT, "8882.pdf")])
	m = json.loads(kho.moc)
	dung("mốc không còn lệnh quét lại treo", "quet_lai_tu" not in m)


@ca("v654 màn Hoá đơn mua vào: nhãn XML, PDF theo tệp thật; thiếu thì có lý do")
def _nhan():
	f = [Doi(attached_to_name="HDM-1", file_name="XMLHD-1C26MYY-8882.xml", file_url="/private/files/a.xml", creation="2"),
		Doi(attached_to_name="MI-1", file_name="HDDT-C26MYY-8882.pdf", file_url="/private/files/mi.pdf", creation="1"),
		Doi(attached_to_name="MI-1", file_name="HDDT-C26MYY-8882-NCC.pdf", file_url="/private/files/ncc.pdf", creation="3")]
	dong = [Doi(hd_dien_tu="MI-2", ghi_chu="Có 2 hoá đơn M-Invoice cùng MST, số và ký hiệu: kế toán chọn tay tờ đúng.", trang_thai=h.TT_CHO)]

	def ga(dt_, filters=None, **k):
		return f if dt_ == "File" else dong if dt_ == h.DT else []
	rows = [{"name": "HDM-1", "custom_minvoice_id": "MI-1"}, {"name": "HDM-2", "custom_minvoice_id": "MI-2"},
		{"name": "HDM-3", "custom_minvoice_id": ""}]
	with um.patch.object(fr, "get_all", ga), um.patch.object(h, "_moc", lambda: {"con": 120}):
		h.gan_tep(rows)
	la("đủ hai tệp, PDF của nhà cung cấp đứng trước bản vẽ lại", (rows[0]["tep_xml"], rows[0]["tep_pdf"], rows[0]["tep_ly_do"]),
		("/private/files/a.xml", "/private/files/ncc.pdf", ""))
	la("chưa khớp: lý do của dòng thư", rows[1]["tep_ly_do"], dong[0]["ghi_chu"])
	dung("chưa thấy thư: nói còn bao nhiêu thư chưa đọc", "120 thư chưa đọc" in rows[2]["tep_ly_do"])

# -*- coding: utf-8 -*-
"""v635: chốt số dư đầu quỹ tiền mặt ngay trên màn Quỹ (anh Việt 03/11/2026).

Chị Dung mở Quỹ tiền mặt công ty thấy "Quỹ chưa chốt số dư đầu, chốt ở Cài đặt tài
chính" mà không bấm được gì: Cài đặt tài chính chỉ mở cho người Giám đốc chọn xem.
Nay người làm quỹ đếm theo mệnh giá và chốt ngay trên màn Quỹ, một lần duy nhất.

Ca chạm hệ chạy HÀM THẬT (quy_tien_mat.chot_dau, tai_chinh.ghi_moc, tai_chinh.luu_moc),
chỉ thay tầng Frappe và phép đọc sổ bằng bản giả ghi lại lời gọi. Phần bấm trên màn ở
hanh_vi/quy_tien_mat_628.js.
"""

import datetime as dt
import sys
import unittest.mock as um
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]

from vagabond import quy_tien_mat as q  # noqa: E402
from vagabond import tai_chinh as tc  # noqa: E402

D = dt.date


@ca("v635 quỹ: ngày mốc chốt đầu là hôm qua khi hôm nay chưa có khoản vào ra quỹ, là hôm nay khi đã có")
def _ngay_moc():
	la("chưa phát sinh", q.ngay_chot_dau(D(2026, 11, 3), False), D(2026, 11, 2))
	la("đã phát sinh", q.ngay_chot_dau(D(2026, 11, 3), True), D(2026, 11, 3))
	la("qua đầu tháng", q.ngay_chot_dau(D(2026, 11, 1), False), D(2026, 10, 31))


@ca("v635 quỹ: bảng rỗng là chưa đếm, gõ 0 là quỹ trống; ghi chú mốc giữ đủ bảng đếm")
def _da_go():
	la("rỗng", [q.co_o_da_go(x) for x in (None, "", "{}", {}, '{"500000": ""}', "hỏng", [])],
		[False] * 7)
	la("gõ 0, gõ số", [q.co_o_da_go('{"500000": "0"}'), q.co_o_da_go({"200000": "3"}),
		q.co_o_da_go([{"menh_gia": 500000, "so_to": "1"}])], [True, True, True])
	dong, tong, _l = q.doc_bang_dem('{"500000": "80", "50000": "2"}')
	g = q.ghi_chu_chot_dau(dong, "  đếm cùng anh Việt ")
	la("ghi chú", g, "Chốt số dư đầu trên màn Quỹ tiền mặt, đếm theo mệnh giá: "
		"500.000 đ x 80, 50.000 đ x 2. đếm cùng anh Việt")
	la("quỹ trống", q.ghi_chu_chot_dau([], ""), "Chốt số dư đầu trên màn Quỹ tiền mặt, đếm theo mệnh giá: quỹ trống")
	dung("không gạch dài", "—" not in g and "–" not in g)


class _Doc(dict):
	def __init__(self, d):
		super().__init__(d)
		self.name = "MOC-0001"

	def insert(self, **k):
		_GHI.append(dict(self))
		return self


_GHI = []


def _vat(moc=None, vao=0, ra=0, vai=("Accounts Manager",), hom="2026-11-03"):
	doc_quy = []

	def tinh_quy(m):
		doc_quy.append(dict(m))
		return {"vao": vao, "ra": ra, "so_phieu": 0, "so_du": 0}
	vat = [
		um.patch.object(q, "_vai", lambda: set(vai)),
		um.patch.object(q, "_khoa_quy", lambda: None),
		um.patch.object(q, "_so_quy", lambda: ((1.0, moc) if moc else (None, None))),
		um.patch.object(q, "nowdate", lambda: hom),
		um.patch.object(tc, "nowdate", lambda: hom),
		um.patch.object(tc, "tinh_quy", tinh_quy),
		um.patch.object(tc, "_cac_nguon", lambda so_bao=None: [
			{"nguon": tc.NGUON_QUY, "ten": tc.TEN_QUY, "loai": "Tiền mặt"},
			{"nguon": "nh:MB", "ten": "MB Bank", "loai": "Ngân hàng"}]),
		um.patch.object(_fr, "get_doc", lambda d, *a: _Doc(d)),
		um.patch.object(_fr, "session", NS(user="dung@x")),
	]
	return vat, doc_quy


def _chay(vat, ham):
	for v in vat:
		v.start()
	try:
		return ham()
	finally:
		for v in vat:
			v.stop()


@ca("v635 chốt đầu chạy thật: quỹ chưa mốc, hôm nay chưa phát sinh thì ghi mốc QUỸ ngày hôm qua đúng số đếm và bảng đếm")
def _chot_hom_qua():
	_GHI.clear()
	vat, doc_quy = _vat()
	kq = _chay(vat, lambda: q.chot_dau(bang='{"500000": "80", "50000": "2", "1000": ""}', ghi_chu="đầu ngày"))
	la("kết quả", (kq["ngay_chot"], kq["so_du"], kq["co_phat_sinh"]), ("2026-11-02", 40100000.0, 0))
	la("một mốc", len(_GHI), 1)
	m = _GHI[0]
	la("mốc quỹ", (m["doctype"], m["nguon"], m["ten_nguon"], m["ngay_chot"], m["so_du"], m["nguoi"]),
		(tc.DT_MOC, tc.NGUON_QUY, tc.TEN_QUY, "2026-11-02", 40100000.0, "dung@x"))
	dung("ghi chú có bảng đếm", "500.000 đ x 80, 50.000 đ x 2. đầu ngày" in m["ghi_chu"])
	la("đọc phát sinh tính từ cuối hôm qua", [x["ngay_chot"] for x in doc_quy], ["2026-11-02"])


@ca("v635 chốt đầu chạy thật: hôm nay đã có biên nhận vào quỹ (hoặc khoản chi) thì mốc ghi ngày hôm nay, không cộng hai lần")
def _chot_hom_nay():
	for vao, ra in ((8350000, 0), (0, 500000)):
		_GHI.clear()
		vat, _d = _vat(vao=vao, ra=ra)
		kq = _chay(vat, lambda: q.chot_dau(bang='{"500000": "10"}'))
		la("mốc hôm nay (vào %s, ra %s)" % (vao, ra), (kq["ngay_chot"], _GHI[0]["ngay_chot"], kq["co_phat_sinh"]),
			("2026-11-03", "2026-11-03", 1))


@ca("v635 chốt đầu chạy thật: quỹ trống gõ 0 thì chốt 0; chưa gõ ô nào thì chặn, không ghi mốc")
def _chot_trong():
	_GHI.clear()
	vat, _d = _vat()
	kq = _chay(vat, lambda: q.chot_dau(bang='{"500000": "0"}'))
	la("chốt 0", (kq["so_du"], _GHI[0]["so_du"]), (0.0, 0.0))
	_GHI.clear()
	vat, _d = _vat()
	nem("chưa đếm", lambda: _chay(vat, lambda: q.chot_dau(bang="{}")))
	vat, _d = _vat()
	nem("số tờ chữ", lambda: _chay(vat, lambda: q.chot_dau(bang='{"500000": "a"}')))
	la("không mốc nào", _GHI, [])


@ca("v635 chốt đầu chạy thật: quỹ đã có mốc thì chặn và chỉ sang Kiểm quỹ; người không làm quỹ bị chặn")
def _chot_chan():
	_GHI.clear()
	vat, _d = _vat(moc={"ngay_chot": "2026-10-31", "so_du": 45200000})
	try:
		_chay(vat, lambda: q.chot_dau(bang='{"500000": "1"}'))
		dung("phải chặn", False)
	except Exception as e:
		dung("câu chỉ sang Kiểm quỹ", "Kiểm quỹ" in str(e) and "31/10/2026" in str(e))
	vat, _d = _vat(vai=("Accounts User",))
	nem("không quyền", lambda: _chay(vat, lambda: q.chot_dau(bang='{"500000": "1"}')))
	vat, _d = _vat(vai=("Giám đốc",))
	_chay(vat, lambda: q.chot_dau(bang='{"500000": "1"}'))
	la("Giám đốc chốt được, chỉ một mốc", len(_GHI), 1)


@ca("v635 Cài đặt tài chính vẫn chốt như cũ qua cùng một cửa ghi mốc; ngày sau hôm nay vẫn bị chặn")
def _luu_moc_cu():
	_GHI.clear()
	vat, _d = _vat()
	vat.append(um.patch.object(tc, "_kiem", lambda: None))
	kq = _chay(vat, lambda: tc.luu_moc(nguon="nh:MB", ngay_chot="2026-11-01", so_du="1.628.400.000", ghi_chu="sao kê"))
	la("lưu", (kq["ok"], kq["name"]), (1, "MOC-0001"))
	la("mốc", (_GHI[0]["nguon"], _GHI[0]["ngay_chot"], _GHI[0]["so_du"], _GHI[0]["ghi_chu"]),
		("nh:MB", "2026-11-01", 1628400000.0, "sao kê"))
	vat, _d = _vat()
	vat.append(um.patch.object(tc, "_kiem", lambda: None))
	nem("ngày sau hôm nay", lambda: _chay(vat, lambda: tc.luu_moc(nguon="nh:MB", ngay_chot="2026-11-04", so_du="1")))
	la("không thêm mốc", len(_GHI), 1)


@ca("v635 câu báo chưa chốt quỹ ở Kiểm quỹ, Nộp ngân hàng chỉ đúng chỗ bấm mới, không còn chỉ sang Cài đặt tài chính")
def _cau_bao():
	loi = q.kiem_nop(1000, None, D(2026, 11, 3), None, D(2026, 11, 3))
	dung("nộp", "Chốt số dư đầu quỹ trên màn Quỹ tiền mặt" in loi)
	vat, _d = _vat()
	try:
		_chay(vat, lambda: q.kiem_quy(bang='{"500000": "1"}', ly_do="dem_sai"))
		dung("phải chặn", False)
	except Exception as e:
		dung("kiểm quỹ", "Chốt số dư đầu quỹ trên màn Quỹ tiền mặt" in str(e) and "Cài đặt tài chính" not in str(e))

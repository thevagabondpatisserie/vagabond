# -*- coding: utf-8 -*-
"""Câu báo khi ngày đơn mua muộn hơn ngày chứng từ.

Ca thật 27/08/2026: Uyên mua gấp, chưa kịp lập đơn mua. Hoá đơn về, lập đơn
mua để nối thì ERPNext chặn bằng một câu tiếng Anh nói ngược chiều việc đang
làm. Uyên tưởng hệ thống cấm lập đơn mua sau khi có hoá đơn.

Hệ thống KHÔNG cấm. Đo trên site: đơn DMH-2026-00147 mang ngày 20/08 do chính
Uyên tạo ngày 21/08, hệ thống cho qua. Chỉ đơn mua mang ngày MUỘN HƠN ngày
hoá đơn mới bị chặn, và chặn đó đúng nghiệp vụ.

Anh Việt chốt: giữ nguyên chốt của ERPNext, chỉ đổi câu báo.

Hai điều các ca dưới đây canh:

* Điều kiện chặn phải khớp TỪNG DẤU với bản gốc của ERPNext. Bản gốc so sánh
  LỚN HƠN. Chép nhầm thành lớn hơn hoặc bằng là chặn oan mọi đơn lập trong
  ngày, tức là biến một câu báo khó hiểu thành một cửa đóng sập.
* Câu báo phải nói đủ ba điều: chuyện gì, vì sao, và sửa cái gì.
"""

import io
import os

from vagabond import ngay_don_mua
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _py(ten):
	goc = os.path.dirname(os.path.abspath(ngay_don_mua.__file__))
	return io.open(os.path.join(goc, ten), encoding="utf-8").read()


# ------------------------------------------------------- điều kiện chặn


@ca("đơn mua muộn hơn ngày hoá đơn thì bị bắt")
def _():
	muon = ngay_don_mua.don_muon_hon("2026-08-24", [("DMH-202", "2026-08-25")])
	la("bắt đúng một đơn", len(muon), 1)
	la("đúng mã đơn", muon[0][0], "DMH-202")


@ca("đơn mua CÙNG NGÀY với hoá đơn thì cho qua")
def _():
	# ERPNext so sánh lớn hơn chứ không phải lớn hơn hoặc bằng. Sai chỗ này
	# là chặn oan mọi đơn lập trong ngày, tức phần lớn đơn của tiệm.
	la("cùng ngày", ngay_don_mua.don_muon_hon("2026-08-24", [("DMH-1", "2026-08-24")]), [])


@ca("đơn mua sớm hơn ngày hoá đơn thì cho qua")
def _():
	la("sớm hơn", ngay_don_mua.don_muon_hon("2026-08-24", [("DMH-1", "2026-08-20")]), [])


@ca("chứng từ không nối đơn mua nào thì không có gì để báo")
def _():
	la("không đơn", ngay_don_mua.don_muon_hon("2026-08-24", []), [])
	la("đơn rỗng", ngay_don_mua.don_muon_hon("2026-08-24", [("", "2026-08-25")]), [])


@ca("nhiều dòng cùng trỏ một đơn thì chỉ kể tên đơn đó một lần")
def _():
	muon = ngay_don_mua.don_muon_hon(
		"2026-08-24", [("DMH-1", "2026-08-25"), ("DMH-1", "2026-08-25")]
	)
	la("bỏ trùng", len(muon), 1)


@ca("chỉ kể những đơn thật sự muộn, không kéo cả đám vào")
def _():
	muon = ngay_don_mua.don_muon_hon(
		"2026-08-24",
		[("DMH-1", "2026-08-20"), ("DMH-2", "2026-08-25"), ("DMH-3", "2026-08-30")],
	)
	la("chỉ hai đơn muộn", [m for m, _d in muon], ["DMH-2", "DMH-3"])


@ca("ngày hỏng thì im, không nổ giữa lúc người ta đang lưu")
def _():
	la("ngày chứng từ hỏng", ngay_don_mua.don_muon_hon("khong-phai-ngay", [("DMH-1", "2026-08-25")]), [])
	la("ngày đơn hỏng", ngay_don_mua.don_muon_hon("2026-08-24", [("DMH-1", None)]), [])


# ------------------------------------------------------------- câu báo


@ca("không có đơn muộn thì không sinh câu báo nào")
def _():
	la("rỗng", ngay_don_mua.cau_bao("Purchase Invoice", "2026-08-24", []), "")


@ca("câu báo nói đủ: chuyện gì, vì sao, và sửa cái gì")
def _():
	from frappe.utils import getdate

	c = ngay_don_mua.cau_bao(
		"Purchase Invoice", "2026-08-24", [("DMH-2026-00202", getdate("2026-08-25"))]
	)
	dung("phải kể tên đơn mua", "DMH-2026-00202" in c)
	dung("phải nói ngày chứng từ theo lối Việt", "24/08/2026" in c)
	dung("phải nói ngày đơn mua", "25/08/2026" in c)
	dung("phải chỉ ra chỗ sửa", "Ngày" in c and "Cách sửa" in c)
	dung("phải nói rõ là lùi ngày được", "lùi ngày" in c)
	dung("phải gọi đúng tên chứng từ", "hoá đơn mua hàng" in c.lower())


@ca("phiếu nhập kho gọi đúng tên của nó, không gọi là hoá đơn")
def _():
	from frappe.utils import getdate

	c = ngay_don_mua.cau_bao("Purchase Receipt", "2026-08-24", [("DMH-1", getdate("2026-08-25"))])
	dung("gọi đúng tên", "phiếu nhập kho" in c.lower())
	la("không được gọi nhầm là hoá đơn", "hoá đơn" in c.lower(), False)


@ca("nhiều đơn muộn thì kể hết, và ngày phải sửa về là ngày chứng từ")
def _():
	from frappe.utils import getdate

	c = ngay_don_mua.cau_bao(
		"Purchase Invoice",
		"2026-08-24",
		[("DMH-1", getdate("2026-08-25")), ("DMH-2", getdate("2026-08-30"))],
	)
	dung("kể đơn thứ nhất", "DMH-1" in c)
	dung("kể đơn thứ hai", "DMH-2" in c)
	dung("nói ngày phải kéo về", "24/08/2026" in c)


@ca("câu báo viết bằng tiếng Việt, không lẫn câu gốc tiếng Anh")
def _():
	from frappe.utils import getdate

	c = ngay_don_mua.cau_bao("Purchase Invoice", "2026-08-24", [("DMH-1", getdate("2026-08-25"))])
	for t in ("Posting Date", "cannot be before", "Purchase Order date"):
		la("không được lẫn chữ %s" % t, t in c, False)


# ------------------------------------------------ nối vào đúng chỗ, không nới


@ca("hook đặt ở before_validate của cả hoá đơn mua lẫn phiếu nhập")
def _():
	m = _py("hooks.py")
	la("phải nối ở đúng hai chỗ", m.count("vagabond.ngay_don_mua.bao_ngay_don_mua"), 2)
	# Đặt ở validate là muộn: `validate_posting_date_with_po` nằm ngay dòng
	# đầu `validate()` của doctype, nó nổ trước và người ta lại đọc tiếng Anh.
	for kh in m.split('"Purchase '):
		if "ngay_don_mua" not in kh:
			continue
		dung("phải đặt ở before_validate", "before_validate" in kh)


@ca("mã không đè lên hàm nào của ERPNext lõi")
def _():
	m = _py("ngay_don_mua.py")
	# Đè lên lõi là gỡ chốt cho toàn hệ, anh Việt đã bác đường đó.
	for t in ("monkey", "validate_posting_date_with_po =", "override_whitelisted"):
		la("không được đè lõi bằng %s" % t, t in m, False)

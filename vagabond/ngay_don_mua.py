# -*- coding: utf-8 -*-
"""Nói cho ra tiếng người khi ngày đơn mua muộn hơn ngày chứng từ.

Ca thật 27/08/2026. Uyên mua gấp, chưa kịp lập đơn mua thì đã đi mua. Hoá
đơn của nhà cung cấp về, lập đơn mua để nối vào thì ERPNext chặn bằng câu:

    Posting Date 24-08-2026 cannot be before Purchase Order date for the
    following: DMH-2026-00202 (25-08-2026)

Câu đó tiếng Anh, nói ngược chiều với việc người ta đang làm, và không nói
phải sửa cái gì. Uyên đọc xong tưởng hệ thống cấm lập đơn mua sau khi có hoá
đơn, nên bỏ cuộc.

HỆ THỐNG KHÔNG CẤM VIỆC ĐÓ. Đã đo trên site: đơn DMH-2026-00147 mang ngày
20/08 nhưng chính Uyên tạo lúc 09:34 ngày 21/08, hệ thống cho qua, đơn đã gửi
duyệt bình thường. Site cũng không bật kỳ kế toán khoá nào, không khoá kho
trước ngày nào. Nghĩa là lập đơn mua muộn rồi để ngày đặt lùi về đúng ngày
đặt thật là chạy được, không cần sửa một dòng mã nào.

Cái duy nhất ERPNext chặn là đơn mua mang ngày MUỘN HƠN ngày hoá đơn hay
ngày phiếu nhập. Chặn đó đúng nghiệp vụ: hàng đã có hoá đơn ngày 24 thì
không thể đặt vào ngày 25.

Anh Việt chốt 27/08/2026: giữ nguyên chốt của ERPNext, chỉ thay câu báo.

CÁCH LÀM
========

Hook `before_validate` chạy trước `validate()` của doctype, mà
`validate_posting_date_with_po` nằm ngay dòng đầu của `validate()`. Nên mình
kiểm cùng một điều kiện và ném câu của mình trước. Không đè lên hàm nào của
lõi, không nới chốt nào: đơn nào ERPNext chặn thì ở đây cũng chặn, chỉ khác
là người đọc hiểu được phải làm gì.

Điều kiện phải bám sát bản gốc, `buying_controller.validate_posting_date_with_po`
của ERPNext v16:

    if getdate(po_date) > getdate(self.posting_date): chan

So sánh LỚN HƠN, không phải lớn hơn hoặc bằng. Đơn mua cùng ngày với hoá đơn
là hợp lệ. Chép sai chỗ này thành >= là chặn oan mọi đơn lập trong ngày.
"""

import frappe
from frappe.utils import getdate

# Tên gọi của từng loại chứng từ trong câu báo. Người đọc là Uyên chứ không
# phải người viết mã, nên gọi đúng tên trên màn hình họ đang nhìn.
TEN_CHUNG_TU = {
	"Purchase Invoice": "hoá đơn mua hàng",
	"Purchase Receipt": "phiếu nhập kho",
}


def _ngay_vn(ngay):
	try:
		return getdate(ngay).strftime("%d/%m/%Y")
	except Exception:
		return str(ngay or "")


def don_muon_hon(ngay_chung_tu, ds_don):
	"""Những đơn mua mang ngày muộn hơn ngày chứng từ. THUẦN.

	ngay_chung_tu  ngày hạch toán của hoá đơn hoặc phiếu nhập
	ds_don         [(ma_don, ngay_dat), ...]

	Trả [(ma_don, ngay_dat), ...] theo đúng thứ tự nhận vào, đã bỏ trùng.
	"""
	try:
		moc = getdate(ngay_chung_tu)
	except Exception:
		return []
	ra, da_thay = [], set()
	for ma, ngay in ds_don or []:
		ma = str(ma or "").strip()
		if not ma or ma in da_thay:
			continue
		try:
			d = getdate(ngay)
		except Exception:
			continue
		if d > moc:
			da_thay.add(ma)
			ra.append((ma, d))
	return ra


def cau_bao(loai, ngay_chung_tu, muon):
	"""Câu báo cho người dùng. THUẦN. Rỗng nghĩa là không có gì để báo.

	Câu này phải trả lời đủ ba điều, theo đúng thứ tự người ta cần biết:
	chuyện gì đang xảy ra, vì sao hệ thống không cho, và phải sửa cái gì.
	"""
	if not muon:
		return ""
	ten = TEN_CHUNG_TU.get(loai, "chứng từ")
	nc = _ngay_vn(ngay_chung_tu)
	dong = "".join(
		"<li><b>%s</b> đang ghi ngày đặt <b>%s</b></li>" % (ma, _ngay_vn(d))
		for ma, d in muon
	)
	# Ngày muộn nhất trong đám bị chặn chính là ngày phải kéo lùi về.
	som_nhat = min(d for _ma, d in muon)
	return (
		"<p>%s này ghi ngày <b>%s</b>, mà đơn mua nối vào lại ghi ngày đặt muộn "
		"hơn:</p><ul>%s</ul>"
		"<p>Hàng đã có %s ngày %s thì không thể đặt sau ngày đó được, nên hệ "
		"thống không cho nối.</p>"
		"<p><b>Cách sửa:</b> mở đơn mua ở trên, đổi ô <b>Ngày</b> về đúng ngày "
		"đặt hàng thật. Đơn lập muộn thì để chậm nhất là <b>%s</b>, tức bằng "
		"ngày %s. Hệ thống cho phép lập đơn mua lùi ngày, không cần xin quyền "
		"gì thêm.</p>"
		% (ten[0].upper() + ten[1:], nc, dong, ten, nc, nc, ten)
	)


def _ds_don_cua(doc):
	"""Cặp (mã đơn mua, ngày đặt) của các dòng trên chứng từ."""
	ma = []
	for d in doc.get("items") or []:
		m = str(d.get("purchase_order") or "").strip()
		if m and m not in ma:
			ma.append(m)
	if not ma:
		return []
	ngay = dict(
		frappe.get_all(
			"Purchase Order",
			filters={"name": ["in", ma]},
			fields=["name", "transaction_date"],
			as_list=True,
		)
	)
	return [(m, ngay.get(m)) for m in ma if ngay.get(m)]


def bao_ngay_don_mua(doc, method=None):
	"""Hook before_validate cho Hoá đơn mua hàng và Phiếu nhập kho.

	KHÔNG nới chốt: đơn nào ERPNext chặn thì đây cũng chặn. Chỉ khác câu chữ.
	"""
	if not doc.get("posting_date"):
		return
	muon = don_muon_hon(doc.get("posting_date"), _ds_don_cua(doc))
	if not muon:
		return
	frappe.throw(cau_bao(doc.doctype, doc.get("posting_date"), muon), title="Ngày đơn mua muộn hơn ngày chứng từ")

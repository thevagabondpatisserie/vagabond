# -*- coding: utf-8 -*-
"""Hoá đơn hàng biếu tặng: chốt chặn chống gian lận và ghi sổ đúng luật thuế.

Anh Việt đặt bài 26/08/2026, nối tiếp phân hệ CRM Tặng quà VIP đã có từ
25/08. Ba câu hỏi của anh và ba câu trả lời đã chốt:

  1. "Không thể để nhân viên tự ý tặng bánh rồi báo là tặng khách VIP nếu
     khách không có trong danh sách duyệt."
     -> Hoá đơn quà PHẢI gắn một phiếu tặng quà có thật, phiếu đó phải nằm
        trong một đợt Đang chạy, đúng khách, và chưa tặng lần nào.

  2. "Hàng biếu tặng vẫn phải xuất hoá đơn VAT như bình thường."
     -> Đúng. Hoá đơn ghi ĐỦ giá bán và thuế suất của món, không giảm giá.

  3. "Đảm bảo tổng tiền khách phải trả bằng 0."
     -> Số KHÁCH TRẢ về 0, không phải số trên hoá đơn về 0. Xem mục dưới.

VÌ SAO KHÔNG ÁP GIẢM 100% NHƯ ĐỀ BÀI VIẾT
------------------------------------------
Đề bài viết "áp Discount 100% cho món đó". Làm vậy thì tiền hàng về 0, và
tiền thuế GTGT cũng về 0 theo. Mà luật hàng biếu tặng bắt giá tính thuế
phải là giá bán của hàng cùng loại tại thời điểm tặng, còn tiệm là bên phải
kê khai và nộp thuế GTGT đầu ra. Hoá đơn ghi 0 đồng thuế là ghi sai căn cứ
tính thuế, và hoá đơn đã gửi cơ quan thuế thì rất khó gỡ lại.

Anh Việt chốt 26/08/2026 đi đường đúng luật. Nên ở đây:

    Hoá đơn      giữ nguyên giá bán và thuế suất, tổng tiền LỚN HƠN 0.
    Khách trả    0 đồng. Công nợ được gạt sang chi phí biếu tặng bằng một
                 bút toán riêng, có trỏ ngược về đúng số hoá đơn.
    Ghi chú      nối thêm "(Hàng tặng không thu tiền)" vào cuối diễn giải
                 của từng dòng hàng, để người đọc hoá đơn biết ngay.

Bút toán gạt công nợ, hai dòng:

    Nợ  chi phí biếu tặng      tổng tiền hoá đơn kể cả thuế
        Có  phải thu khách hàng    (gắn đúng khách và đúng số hoá đơn)

Tiền thuế GTGT đầu ra nằm trong tổng đó, tức là tiệm chịu, đúng như luật.

VÌ SAO KHÔNG DÙNG Ô "WRITE OFF" CÓ SẴN CỦA ERPNEXT
---------------------------------------------------
Đã dò mã nguồn ERPNext v16 trước khi viết. Hai chỗ chặn:

    allow_write_off_only_on_pos()  xoá trắng ô write_off_account nếu hoá
                                   đơn không phải hoá đơn quầy.
    make_write_off_gl_entry()      chỉ sinh bút toán khi is_pos bật.

Hoá đơn quà không đi qua quầy, nên điền hai ô đó là điền vào chỗ máy sẽ tự
xoá, và không có một dòng sổ cái nào được sinh ra. Người viết sau em rất dễ
tưởng là xong. Nên đi bút toán riêng, thấy được, huỷ được, soát được.

HOÁ ĐƠN QUÀ LÀ MỘT TỜ RIÊNG, KHÔNG TRỘN VỚI HÀNG BÁN
-----------------------------------------------------
Mọi dòng trên tờ có gắn phiếu quà đều phải nằm trong danh sách quà đã
duyệt, và số lượng không được vượt. Không cho trộn bánh bán tiền vào cùng
tờ với bánh tặng.

Hai lý do. Một là kế toán: cả tờ được gạt sang chi phí biếu tặng, trộn hàng
bán vào là gạt luôn cả doanh thu thật. Hai là chống gian lận: cho trộn thì
một tờ có một cái bánh tặng hợp lệ sẽ mở đường cho năm cái bánh khác đi
kèm mà không ai soi.

KHÁCH HẠNG OWNER KHÔNG ĐI ĐƯỜNG NÀY
------------------------------------
Hạng OWNER là đơn tiêu dùng nội bộ, `vagabond/noi_bo.py` tự áp giảm 100% và
chặn xuất hoá đơn điện tử. Hai luật ngược nhau trên cùng một tờ thì tờ đó
sai kiểu gì cũng sai. Nên chặn thẳng ở đây và bảo người dùng đi đường nội
bộ, thay vì để hai mô đun giằng nhau.
"""

import json

# --------------------------------------------------------------- phần thuần
#
# Đặt trên `import frappe` để bộ kiểm thử tầng khung chạy được ở CI mà không
# cần site, không cần requests. Ca kiểm ở khung/kiem_thu/thu_qua_tang_hoa_don.py.

SI = "Sales Invoice"
DT_PHIEU = "Vagabond Tang Qua VIP"
DT_DOT = "Vagabond Dot Tang Qua"

GHI_CHU_QUA = "(Hàng tặng không thu tiền)"

TT_CHO_TANG = ("Chua tang", "Dang xu ly")
TT_DA_TANG = "Da tang"
TT_DOT_CHAY = "Dang chay"

HANG_NOI_BO = "OWNER"


def them_ghi_chu(dien_giai):
	"""Nối "(Hàng tặng không thu tiền)" vào cuối diễn giải một dòng hàng.

	THUẦN. Nối một lần duy nhất: hàm này chạy ở before_submit, mà một tờ có
	thể bị huỷ rồi sửa rồi ghi sổ lại, nối mù thì diễn giải dài dần ra và
	tờ hoá đơn in ra nhìn như lỗi máy.
	"""
	goc = str(dien_giai or "").strip()
	if GHI_CHU_QUA in goc:
		return goc
	if not goc:
		return GHI_CHU_QUA
	return goc + " " + GHI_CHU_QUA


def loi_phieu(phieu, khach_don, hoa_don_dang_lam=None):
	"""Soi phiếu tặng quà có dùng được cho tờ hoá đơn này không. THUẦN.

	`phieu` là một tự điển các ô cần thiết, không phải bản ghi Frappe, để ca
	kiểm chạy được mà không cần site.

	Trả về DANH SÁCH câu lỗi. Rỗng nghĩa là hợp lệ. Trả danh sách chứ không
	ném ngay ở đây vì phần thuần không được chạm Frappe, và vì người dùng
	nên thấy hết mọi chỗ sai trong một lần chứ không phải sửa xong cái này
	mới lòi ra cái kia.
	"""
	ra = []
	p = phieu or {}
	if not p:
		return ["Không tìm thấy phiếu tặng quà nào mang mã đó."]

	if int(p.get("huy") or 0):
		ra.append("Phiếu tặng quà %s đã bị huỷ nên không xuất hoá đơn được."
			% (p.get("name") or ""))

	tt_dot = str(p.get("dot_trang_thai") or "").strip()
	if tt_dot != TT_DOT_CHAY:
		ra.append(
			"Đợt tặng quà %s đang ở trạng thái %s, không phải Đang chạy. "
			"Chỉ đợt Đang chạy mới được xuất quà."
			% (p.get("dot") or "", tt_dot or "để trống")
		)

	k_phieu = str(p.get("khach") or "").strip()
	k_don = str(khach_don or "").strip()
	if not k_phieu:
		ra.append(
			"Phiếu tặng quà %s chưa gắn khách trong hệ. Mở phiếu, chọn ô "
			"Khách trong hệ rồi lưu lại trước khi xuất hoá đơn."
			% (p.get("name") or "")
		)
	elif k_phieu != k_don:
		ra.append(
			"Hoá đơn đang lập cho khách %s nhưng phiếu tặng quà %s là của "
			"khách %s. Hai bên phải là một người."
			% (k_don or "để trống", p.get("name") or "", k_phieu)
		)

	tt = str(p.get("tt_tang") or "").strip()
	hd_cu = str(p.get("hoa_don") or "").strip()
	if tt == TT_DA_TANG or hd_cu:
		if hd_cu and hd_cu != str(hoa_don_dang_lam or "").strip():
			ra.append(
				"Phiếu tặng quà %s đã tặng rồi, đã xuất trên hoá đơn %s. "
				"Một phiếu chỉ nhận quà một lần."
				% (p.get("name") or "", hd_cu)
			)
		elif not hd_cu:
			ra.append(
				"Phiếu tặng quà %s đang ở trạng thái Đã tặng nên không xuất "
				"thêm hoá đơn được." % (p.get("name") or "")
			)
	elif tt and tt not in TT_CHO_TANG:
		ra.append("Phiếu tặng quà %s đang ở trạng thái %s, không xuất được."
			% (p.get("name") or "", tt))

	return ra


def loi_mon(dong_hoa_don, mon_duyet):
	"""Soi từng dòng hàng trên tờ so với danh sách quà đã duyệt. THUẦN.

	`dong_hoa_don` là [{ma, so_luong}], `mon_duyet` là {ma: so_luong}.

	Gộp theo mã trước khi so: một món có thể nằm hai dòng trên cùng tờ, so
	từng dòng riêng thì mỗi dòng đều lọt mà tổng lại vượt.
	"""
	ra = []
	duyet = {}
	for k, v in (mon_duyet or {}).items():
		duyet[str(k)] = duyet.get(str(k), 0) + float(v or 0)

	gom = {}
	for d in (dong_hoa_don or []):
		ma = str((d or {}).get("ma") or "").strip()
		if not ma:
			continue
		gom[ma] = gom.get(ma, 0) + float((d or {}).get("so_luong") or 0)

	if not gom:
		return ["Hoá đơn quà chưa có dòng hàng nào."]

	for ma in sorted(gom):
		if ma not in duyet:
			ra.append(
				"Món %s không có trong danh sách quà đã duyệt của phiếu. "
				"Hoá đơn quà chỉ được xuất đúng những món đã duyệt, muốn bán "
				"thêm thì lập một hoá đơn riêng." % ma
			)
		elif gom[ma] > duyet[ma] + 0.0001:
			ra.append(
				"Món %s xuất %s nhưng phiếu chỉ duyệt %s."
				% (ma, _so(gom[ma]), _so(duyet[ma]))
			)
	return ra


def _so(x):
	"""Số lượng in ra cho người đọc: bỏ đuôi .0 thừa."""
	f = float(x or 0)
	return str(int(f)) if abs(f - int(f)) < 0.0001 else ("%.3f" % f).rstrip("0")


def dong_but_toan(tk_chi_phi, tk_cong_no, khach, so_tien, hoa_don):
	"""Hai dòng bút toán gạt công nợ hoá đơn quà. THUẦN.

	Nợ chi phí biếu tặng, Có phải thu khách hàng, có trỏ ngược về số hoá
	đơn để ERPNext trừ đúng tờ đó chứ không trừ lung tung sang tờ khác của
	cùng khách.
	"""
	tien = round(float(so_tien or 0), 2)
	if tien <= 0:
		return []
	return [
		{
			"account": tk_chi_phi,
			"debit_in_account_currency": tien,
			"credit_in_account_currency": 0,
			"user_remark": "Hàng tặng không thu tiền, hoá đơn %s" % hoa_don,
		},
		{
			"account": tk_cong_no,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": tien,
			"party_type": "Customer",
			"party": khach,
			"reference_type": SI,
			"reference_name": hoa_don,
			"user_remark": "Gạt công nợ hàng tặng, hoá đơn %s" % hoa_don,
		},
	]


# ------------------------------------------------------------ phần chạm hệ

import frappe  # noqa: E402
from frappe.utils import cint, flt, today  # noqa: E402


TRUONG_MOI = {
	"Sales Invoice": [
		{
			"fieldname": "vgb_phieu_qua",
			"label": "Phiếu tặng quà VIP",
			"fieldtype": "Link",
			"options": DT_PHIEU,
			"insert_after": "vgb_noi_bo",
			"description": (
				"Gắn phiếu tặng quà đã duyệt thì hoá đơn này là hoá đơn hàng "
				"biếu tặng: giữ nguyên giá và thuế, khách trả 0 đồng."
			),
		},
		{
			"fieldname": "vgb_qua_tang",
			"label": "Hoá đơn hàng biếu tặng",
			"fieldtype": "Check",
			"insert_after": "vgb_phieu_qua",
			"read_only": 1,
			"description": (
				"Máy tự bật khi tờ này có gắn phiếu tặng quà. Kế toán lọc cột "
				"này để bóc riêng hàng biếu tặng khỏi doanh thu bán."
			),
		},
		{
			"fieldname": "vgb_but_toan_qua",
			"label": "Bút toán gạt công nợ quà",
			"fieldtype": "Link",
			"options": "Journal Entry",
			"insert_after": "vgb_qua_tang",
			"read_only": 1,
		},
	],
	"Vagabond Tang Qua VIP": [
		{
			"fieldname": "hoa_don",
			"label": "Hoá đơn đã xuất",
			"fieldtype": "Link",
			"options": SI,
			"insert_after": "ngay_tang",
			"read_only": 1,
			"description": "Máy tự điền khi hoá đơn quà được ghi sổ.",
		},
	],
	"Vagabond Settings": [
		{
			"fieldname": "sec_qua_tang",
			"label": "Hàng biếu tặng khách VIP",
			"fieldtype": "Section Break",
			"insert_after": "minvoice_mau_lien_ket",
		},
		{
			"fieldname": "tk_chi_phi_qua_tang",
			"label": "Tài khoản chi phí biếu tặng",
			"fieldtype": "Link",
			"options": "Account",
			"insert_after": "sec_qua_tang",
			"description": (
				"Nơi gạt công nợ của hoá đơn hàng tặng sang. Chưa chọn thì hệ "
				"không cho xuất hoá đơn quà, để không ai đoán hộ chỗ hạch toán."
			),
		},
	],
}


def _tk_chi_phi():
	"""Tài khoản chi phí biếu tặng đã cấu hình. Chưa có thì ném lỗi rõ ràng.

	KHÔNG đoán một tài khoản mặc định. Chọn hộ chỗ hạch toán là quyết định
	kế toán, mà bút toán sinh ra ở đây đi thẳng vào sổ cái.
	"""
	tk = ""
	try:
		from vagabond.lib import cfg

		tk = str((cfg() or {}).get("tk_chi_phi_qua_tang") or "").strip()
	except Exception:
		tk = ""
	if not tk:
		frappe.throw(
			"Chưa khai <b>Tài khoản chi phí biếu tặng</b> trong Cài đặt. "
			"Nhờ anh Việt và chị Dung chọn tài khoản chi phí cho hàng biếu "
			"tặng rồi mới xuất hoá đơn quà.",
			title="Thiếu tài khoản chi phí biếu tặng",
		)
	if not frappe.db.exists("Account", tk):
		frappe.throw("Không thấy tài khoản %s trong hệ thống tài khoản." % tk)
	if frappe.db.get_value("Account", tk, "is_group"):
		frappe.throw(
			"Tài khoản %s là tài khoản nhóm, không hạch toán thẳng vào được. "
			"Chọn một tài khoản con." % tk
		)
	return tk


def _nap_phieu(ma):
	"""Đọc phiếu tặng quà thành tự điển phần thuần đọc được. Không có thì None."""
	ma = str(ma or "").strip()
	if not ma:
		return None
	r = frappe.db.get_value(
		DT_PHIEU, ma,
		["name", "dot", "khach", "ten_khach", "tt_tang", "huy", "hoa_don"],
		as_dict=True,
	)
	if not r:
		return None
	r = dict(r)
	r["dot_trang_thai"] = (
		frappe.db.get_value(DT_DOT, r.get("dot"), "trang_thai_dot") or ""
	) if r.get("dot") else ""
	return r


def _mon_duyet(ma_phieu):
	"""Danh sách quà đã duyệt của phiếu, gộp theo mã món."""
	ds = frappe.get_all(
		"Vagabond Tang Qua VIP Mon",
		filters={"parent": ma_phieu, "parenttype": DT_PHIEU},
		fields=["mon", "so_luong"],
		limit_page_length=0,
	)
	ra = {}
	for d in ds:
		if not d.get("mon"):
			continue
		ra[d["mon"]] = ra.get(d["mon"], 0) + flt(d.get("so_luong") or 0)
	return ra


def _khach_tren_to(si):
	"""Khách NHẬN QUÀ trên tờ. Ưu tiên ô khách thân thiết như các mô đun khác.

	Khác với `_ben_cong_no` bên dưới, và khác có chủ ý. Ô `vgb_khach_no` là
	người thật sự được hưởng, ô `customer` là bên đứng tên trên sổ. Hai ô
	này lệch nhau khi quầy bán cho khách vãng lai nhưng ghi điểm cho một
	thành viên - xem ghi chú trong `ban_hang`.
	"""
	return (si.get("vgb_khach_no") or "").strip() or (si.get("customer") or "").strip()


def _ben_cong_no(si):
	"""Bên đứng tên trên sổ công nợ. LUÔN là `customer`.

	Bút toán gạt công nợ phải ghi đúng bên mà ERPNext đã ghi Nợ lúc lập hoá
	đơn. Lấy nhầm sang `vgb_khach_no` thì bút toán treo trên một khách khác
	và tờ hoá đơn không bao giờ hết công nợ.
	"""
	return (si.get("customer") or "").strip()


def _khop_khach(phieu, si):
	"""Phiếu quà có đúng người trên tờ này không.

	Nhận CẢ HAI ô: khách đứng tên và khách thân thiết. Một trong hai khớp là
	đủ, vì cả hai đều là cách hợp lệ để chỉ ra cùng một người.
	"""
	k = str((phieu or {}).get("khach") or "").strip()
	if not k:
		return False
	return k in {
		(si.get("customer") or "").strip(),
		(si.get("vgb_khach_no") or "").strip(),
	}


def truoc_khi_luu(doc, method=None):
	"""Hook validate của Sales Invoice: chốt chặn chống gian lận.

	Đặt ở validate chứ không ở before_submit vì anh Việt yêu cầu "văng lỗi
	chặn cứng không cho xuất". Chặn ngay lúc lưu thì nhân viên biết sai
	trong lúc còn đang gõ, chứ không phải gõ xong cả tờ mới bị đá ra.

	Ngoại lệ so với các hàng rào khác của tiệm: hàng rào này KHÔNG tha cho
	nhịp đồng bộ Pancake. Pancake không bao giờ tự điền ô phiếu quà, nên tờ
	nào có ô đó là do người gắn vào, và người gắn thì phải chịu soi.
	"""
	ma_phieu = (doc.get("vgb_phieu_qua") or "").strip()
	try:
		doc.vgb_qua_tang = 1 if ma_phieu else 0
	except Exception:
		pass
	if not ma_phieu:
		return
	if cint(doc.get("vgb_huy")):
		return

	khach = _khach_tren_to(doc)

	# Hạng nội bộ đi đường khác, hai luật ngược nhau không ở chung một tờ.
	try:
		from vagabond import noi_bo

		if noi_bo.la_noi_bo(khach):
			frappe.throw(
				"Khách %s đang ở hạng %s, tức là đơn tiêu dùng nội bộ. Đơn nội "
				"bộ giảm 100%% và không xuất hoá đơn điện tử, ngược hẳn với "
				"hàng biếu tặng. Bỏ ô phiếu tặng quà ra, hoặc đổi hạng khách "
				"trước." % (khach, noi_bo.HANG_NOI_BO),
				title="Khách hạng nội bộ không đi đường quà tặng",
			)
	except ImportError:
		pass

	p = _nap_phieu(ma_phieu)
	# Truyền vào ô khách nào KHỚP với phiếu, để câu lỗi chỉ nổ khi thật sự
	# lệch người chứ không nổ vì tờ dùng ô kia.
	khach_soi = str((p or {}).get("khach") or "") if _khop_khach(p, doc) else khach
	loi = loi_phieu(p, khach_soi, doc.get("name"))
	if not loi:
		dong = [
			{"ma": (d.get("item_code") or ""), "so_luong": flt(d.get("qty"))}
			for d in (doc.get("items") or [])
		]
		loi += loi_mon(dong, _mon_duyet(ma_phieu))

	if loi:
		frappe.throw(
			"<br>".join("- " + x for x in loi),
			title="Hoá đơn quà tặng không hợp lệ",
		)

	# Quà tặng ghi ĐỦ giá và thuế. Xoá mọi khoản giảm để không ai vô tình
	# kéo căn cứ tính thuế xuống.
	try:
		doc.additional_discount_percentage = 0
		doc.discount_amount = 0
		doc.vgb_giam_diem = 0
	except Exception:
		pass


def truoc_khi_ghi_so(doc, method=None):
	"""Hook before_submit: nối ghi chú hàng tặng vào từng dòng hàng.

	Đặt ở before_submit chứ không ở validate: bản nháp còn đang sửa thì mỗi
	lần lưu lại đụng vào diễn giải một lần, mà diễn giải là chỗ người dùng
	cũng gõ tay. Ghi sổ mới là lúc tờ chốt lại.
	"""
	if not (doc.get("vgb_phieu_qua") or "").strip():
		return
	if cint(doc.get("vgb_huy")):
		return
	for d in (doc.get("items") or []):
		try:
			d.description = them_ghi_chu(d.get("description"))
		except Exception:
			continue
	# Kiểm tài khoản NGAY BÂY GIỜ chứ không đợi tới lúc lập bút toán. Thiếu
	# tài khoản mà để tờ ghi sổ xong mới báo thì hoá đơn đã vào sổ, công nợ
	# treo trên đầu khách, và có khi đã bắn sang hoá đơn điện tử.
	_tk_chi_phi()


def sau_khi_ghi_so(doc, method=None):
	"""Hook on_submit: đóng dấu Đã tặng và gạt công nợ sang chi phí.

	Hai việc phải theo thứ tự này. Đóng dấu trước để chống nhận hai lần dù
	bút toán có hỏng, rồi mới lập bút toán.
	"""
	ma_phieu = (doc.get("vgb_phieu_qua") or "").strip()
	if not ma_phieu or cint(doc.get("vgb_huy")):
		return

	try:
		frappe.db.set_value(DT_PHIEU, ma_phieu, {
			"tt_tang": TT_DA_TANG,
			"ngay_tang": doc.get("posting_date") or today(),
			"hoa_don": doc.name,
		}, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "qua_tang_hoa_don: dong dau da tang")

	try:
		_gat_cong_no(doc)
	except frappe.ValidationError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "qua_tang_hoa_don: gat cong no")
		frappe.msgprint(
			"Hoá đơn quà %s đã ghi sổ nhưng bút toán gạt công nợ chưa lập "
			"được. Nhờ kế toán lập tay: Nợ chi phí biếu tặng, Có phải thu "
			"khách hàng, gắn đúng số hoá đơn này." % doc.name
		)


def _gat_cong_no(si):
	"""Lập và ghi sổ bút toán gạt công nợ của một tờ hoá đơn quà."""
	con_no = flt(si.get("outstanding_amount"))
	if con_no <= 0:
		return None
	tk_chi_phi = _tk_chi_phi()
	tk_cong_no = (si.get("debit_to") or "").strip()
	if not tk_cong_no:
		frappe.throw("Hoá đơn %s chưa có tài khoản phải thu." % si.name)

	dong = dong_but_toan(
		tk_chi_phi, tk_cong_no, _ben_cong_no(si), con_no, si.name
	)
	if not dong:
		return None

	je = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Journal Entry",
		"company": si.get("company"),
		"posting_date": si.get("posting_date") or today(),
		"user_remark": (
			"Gạt công nợ hàng biếu tặng, hoá đơn %s, phiếu quà %s. "
			"Hàng tặng không thu tiền."
			% (si.name, si.get("vgb_phieu_qua"))
		),
		"accounts": dong,
	})
	je.flags.ignore_permissions = True
	je.insert(ignore_permissions=True)
	je.submit()
	try:
		frappe.db.set_value(SI, si.name, "vgb_but_toan_qua", je.name,
			update_modified=False)
	except Exception:
		pass
	return je.name


def khi_huy(doc, method=None):
	"""Hook on_cancel: trả phiếu về Chưa tặng và huỷ bút toán gạt công nợ.

	Không trả lại thì huỷ một tờ hoá đơn quà xong là phiếu kẹt vĩnh viễn ở
	Đã tặng, khách không bao giờ nhận được quà mà bảng vẫn báo đã tặng.

	Huỷ bút toán chứ TUYỆT ĐỐI không xoá (QT-20): xoá là mất vết, mà đây là
	chứng từ đã vào sổ cái.
	"""
	ma_phieu = (doc.get("vgb_phieu_qua") or "").strip()
	if not ma_phieu:
		return

	je = (doc.get("vgb_but_toan_qua") or "").strip()
	if je:
		try:
			d = frappe.get_doc("Journal Entry", je)
			if cint(d.docstatus) == 1:
				d.flags.ignore_permissions = True
				d.cancel()
		except Exception:
			frappe.log_error(frappe.get_traceback(), "qua_tang_hoa_don: huy but toan")

	try:
		hd_tren_phieu = frappe.db.get_value(DT_PHIEU, ma_phieu, "hoa_don")
		if (hd_tren_phieu or "") == doc.name:
			frappe.db.set_value(DT_PHIEU, ma_phieu, {
				"tt_tang": TT_CHO_TANG[0],
				"ngay_tang": None,
				"hoa_don": None,
			}, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "qua_tang_hoa_don: tra phieu ve chua tang")


# ------------------------------------------------------------------ cửa ngõ


@frappe.whitelist()
def kiem_phieu(ma_phieu=None, khach=None):
	"""CHỈ ĐỌC: phiếu này xuất hoá đơn quà được chưa, và được xuất món gì.

	Màn app gọi trước khi mở form, để báo sai ngay trên màn chứ không đợi
	người dùng gõ xong cả tờ rồi mới bị đá ra.
	"""
	from vagabond import tang_qua

	tang_qua._kiem_quyen("xuất hoá đơn quà tặng")
	p = _nap_phieu(ma_phieu)
	if not p:
		return {"duoc": 0, "loi": ["Không tìm thấy phiếu tặng quà nào mang mã đó."]}
	loi = loi_phieu(p, (khach or p.get("khach")), None)
	mon = _mon_duyet(p["name"]) if p else {}
	return {
		"duoc": 0 if loi else 1,
		"loi": loi,
		"phieu": p,
		"mon": [{"ma": k, "so_luong": v} for k, v in sorted(mon.items())],
	}


@frappe.whitelist()
def xuat_hoa_don(ma_phieu=None, ngay=None, ghi_so=0):
	"""Lập hoá đơn hàng biếu tặng từ một phiếu tặng quà đã duyệt.

	Mặc định để NHÁP. Ghi sổ là lúc chạm sổ cái và có thể bắn hoá đơn điện
	tử, nên phải bấm rõ chứ không lặng lẽ chạy.
	"""
	from vagabond import tang_qua

	tang_qua._kiem_quyen("xuất hoá đơn quà tặng")

	p = _nap_phieu(ma_phieu)
	loi = loi_phieu(p, (p or {}).get("khach"), None)
	if loi:
		frappe.throw("<br>".join("- " + x for x in loi),
			title="Hoá đơn quà tặng không hợp lệ")

	mon = _mon_duyet(p["name"])
	if not mon:
		frappe.throw("Phiếu tặng quà %s chưa có món nào." % p["name"])

	_tk_chi_phi()

	si = frappe.new_doc(SI)
	si.customer = p["khach"]
	si.posting_date = ngay or today()
	si.due_date = si.posting_date
	si.vgb_phieu_qua = p["name"]
	si.remarks = "Hàng tặng khách VIP theo phiếu %s, đợt %s. %s" % (
		p["name"], p.get("dot") or "", GHI_CHU_QUA)
	for ma, sl in sorted(mon.items()):
		si.append("items", {"item_code": ma, "qty": sl})

	si.flags.ignore_permissions = True
	si.insert(ignore_permissions=True)
	if cint(ghi_so):
		si.submit()
	frappe.db.commit()

	return {
		"ok": 1,
		"ma": si.name,
		"tong": flt(si.grand_total),
		"da_ghi_so": 1 if cint(ghi_so) else 0,
		"loi_nhan": (
			"Đã lập hoá đơn quà %s, tổng %s đ kể cả thuế.%s"
			% (si.name, "{:,.0f}".format(flt(si.grand_total)),
			   " Đã ghi sổ và đã gạt công nợ, khách trả 0 đồng."
			   if cint(ghi_so)
			   else " Còn ở dạng nháp, soát xong bấm Ghi sổ.")
		),
	}

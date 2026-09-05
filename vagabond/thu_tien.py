# -*- coding: utf-8 -*-
"""Thu tiền hoá đơn bán: ghi chứng từ thật, và tính đúng số còn nợ.

VÌ SAO CÓ TỆP NÀY - đo trên số liệu thật ngày 04/09/2026
--------------------------------------------------------------------
Anh Việt chuyển phản ánh của bên Loan Anh: hoá đơn 92523 trị giá
43.978.500 đã chuyển khoản một nửa (21.989.250) mà màn công nợ vẫn ghi
khách nợ nguyên tờ; hoá đơn của Ms.Amber 21.000.000 đã thu đủ mà vẫn nằm
trong danh sách khách đang nợ.

Đo ra ba chỗ hỏng khác nhau, không phải một:

  1. `cong_no.ds_khach_no` cộng `grand_total` của mọi hoá đơn mang CỜ
     `vgb_pt_thanh_toan = "Công nợ"`. Cộng tổng tờ thì thu bao nhiêu cũng
     không trừ ra, và đọc cờ thì tờ nào cờ còn ghi Công nợ là còn nợ.
  2. Phiếu đòi nợ chuyển sang "Da thu du" mà KHÔNG sinh chứng từ thu tiền
     nào. Hoá đơn rơi khỏi phép loại "đang nằm trong phiếu chờ thu" (phép
     đó chỉ tính phiếu "Cho thu" và "Thu thieu") nên quay lại danh sách
     nợ. Đúng ca Ms.Amber: phiếu DNTT-26-09-00001 ghi đã thu 21.000.000,
     mà hoá đơn HDB-26-08-02800 vẫn `outstanding_amount` 21.000.000.
  3. Không có đường nào ghi "một phần đã thu, phần còn lại công nợ". Ô
     phương thức chỉ chứa một tên, chọn Công nợ là cả tờ thành nợ.

CON SỐ PHẢI BIẾT TRƯỚC KHI ĐỌC TIẾP
--------------------------------------------------------------------
Ngày 04/09/2026 hệ có 2.210 hoá đơn đã ghi sổ mang dư nợ, tổng
1.311.944.863 đồng. Chỉ 27 tờ (115.159.000) là công nợ thật. 2.183 tờ còn
lại là tiền ĐÃ THU (chuyển khoản 948 tờ, thẻ Shinhan 222 tờ, tiền mặt 111
tờ, Grab 344 tờ...) nhưng chưa bao giờ có chứng từ thu tiền, nên sổ cái
vẫn ghi khách nợ.

Nghĩa là KHÔNG ĐƯỢC đọc thẳng `outstanding_amount` làm số nợ: làm vậy màn
công nợ nhảy từ 115 triệu lên 1,31 tỷ trong một đêm và cả tiệm hoảng.

Anh Việt chốt 04/09/2026: chỉ làm cho tờ TỪ NAY, 2.183 tờ cũ liệt kê ra
cho chị Dung tự quyết, máy không đụng (điều 11).

LUẬT TÍNH SỐ NỢ - đọc kỹ trước khi sửa
--------------------------------------------------------------------
"Công nợ" KHÔNG phải một phương thức thanh toán thành công. Nó là tên gọi
của phần CHƯA THU. Nên:

    đã thu thật   = tổng các dòng thanh toán có phương thức KHÁC Công nợ
    còn nợ theo dòng = tổng đơn trừ đã thu thật
    còn nợ        = min(dư nợ sổ cái, còn nợ theo dòng)

Phép `min` là chỗ gánh cả ba ca cùng lúc:

  * Tờ MỚI có chứng từ thu tiền: hai vế bằng nhau, lấy cái nào cũng đúng.
  * Tờ 92523: sổ cái ghi 43.978.500, dòng ghi đã thu 21.989.250, ra
    21.989.250 - đúng số Loan Anh cần thấy.
  * 2.183 tờ CŨ đã thu bằng chuyển khoản mà chưa có chứng từ: không dòng
    nào, cờ không phải Công nợ, nên còn nợ theo dòng bằng 0, ra 0. Chúng
    không nhảy vào màn công nợ.

Sổ cái luôn được tôn trọng: đã ghi nhận thu rồi thì `min` kéo xuống ngay,
không bao giờ đòi khách số tiền họ đã trả.
"""

import frappe
from frappe.utils import flt, nowdate

SI = "Sales Invoice"

# "Công nợ" và "Chưa thu" là NHÃN CỦA PHẦN CHƯA TRẢ, không phải tiền vào.
# Cộng chúng vào phần đã thu là tự xoá sổ nợ của mình.
PT_KHONG_PHAI_THU = ("Công nợ", "Chưa thu", "Ghi nợ")

# Hàng tặng không phải một đường tiền vào, cũng không phải một khoản nợ.
# Tờ đã tất toán rồi, nhưng tất toán bằng CHI PHÍ biếu tặng chứ không bằng
# tiền: xem vagabond/hang_tang.py, nó có đường ghi sổ riêng vào 64181 và
# 64182. Sinh chứng từ thu cho nó là dựng ra một khoản tiền không ai trả.
#
# Nên nó nằm riêng khỏi PT_KHONG_PHAI_THU: vào danh sách đó thì nó lại bị
# tính thành nợ, và màn công nợ sẽ đi đòi khách một hộp bánh mình tặng.
PT_KHONG_SINH_PHIEU = ("Hàng tặng",)


def khong_sinh_phieu(pt):
	"""Phương thức đã tất toán tờ nhưng KHÔNG bằng tiền. THUẦN."""
	return (pt or "").strip() in PT_KHONG_SINH_PHIEU


# ------------------------------------------------------------ phần thuần


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def la_cong_no(pt):
	"""Tên phương thức này có phải là nhãn của phần chưa thu không. THUẦN."""
	return (pt or "").strip() in PT_KHONG_PHAI_THU


def da_thu_that(dong):
	"""Tiền THẬT SỰ đã vào, cộng từ các dòng thanh toán. THUẦN.

	Bỏ mọi dòng mang nhãn công nợ. Bỏ dòng số tiền âm hoặc bằng không:
	dòng âm là dấu hiệu gõ nhầm, cộng vào là tự giảm số phải đòi.
	"""
	t = 0.0
	for d in dong or []:
		if not isinstance(d, dict):
			continue
		if la_cong_no(d.get("pt")):
			continue
		so = _so(d.get("so_tien"))
		if so > 0:
			t += so
	return t


def da_thu_theo_pt(dong):
	"""Đã thu bao nhiêu theo TỪNG phương thức. THUẦN.

	Trả list cặp (phương thức, số tiền), giữ thứ tự gặp lần đầu. Màn hoá
	đơn phải bày được từng dòng chứ không chỉ một con số tổng, đó là yêu
	cầu anh Việt 04/09: *"Hiển thị minh bạch trên hóa đơn: tổng hóa đơn,
	đã thu theo từng phương thức, còn nợ, trạng thái thanh toán."*
	"""
	gom, thu_tu = {}, []
	for d in dong or []:
		if not isinstance(d, dict) or la_cong_no(d.get("pt")):
			continue
		so = _so(d.get("so_tien"))
		if so <= 0:
			continue
		pt = (d.get("pt") or "").strip() or "(chưa rõ)"
		if pt not in gom:
			gom[pt] = 0.0
			thu_tu.append(pt)
		gom[pt] += so
	return [(pt, gom[pt]) for pt in thu_tu]


def con_no_cua(tong_don, du_no_so_cai, dong, pt_chinh):
	"""Số tiền hoá đơn này THẬT SỰ còn phải đòi khách. THUẦN.

	`du_no_so_cai` là `outstanding_amount` của hoá đơn. Xem phần đầu tệp
	để biết vì sao không đọc thẳng ô đó.

	Không có dòng thanh toán nào thì quay về cách cũ: cờ ghi Công nợ mới
	tính là nợ. Đó là cửa giữ cho 2.183 tờ cũ nằm yên chỗ của chúng.
	"""
	tong = _so(tong_don)
	if tong <= 0:
		return 0.0
	co_dong = bool([d for d in (dong or []) if isinstance(d, dict) and _so(d.get("so_tien")) > 0])
	if co_dong:
		theo_dong = tong - da_thu_that(dong)
	else:
		theo_dong = tong if la_cong_no(pt_chinh) else 0.0
	if theo_dong <= 0:
		return 0.0
	so_cai = _so(du_no_so_cai)
	# Sổ cái đã ghi nhận thu tới đâu thì tôn trọng tới đó. Không bao giờ
	# đòi khách số tiền chứng từ đã ghi là họ trả rồi.
	return max(0.0, min(so_cai, theo_dong))


def trang_thai_thu(tong_don, con_no):
	"""Một chữ cho màn hình. THUẦN."""
	tong = _so(tong_don)
	no = _so(con_no)
	if no <= 0:
		return "Đã thanh toán"
	if no >= tong - 1:
		return "Chưa thu"
	return "Thu một phần"


def khoa_chong_trung(si_name, nguon):
	"""Khoá nhận diện một lần thu tiền, để không ghi hai lần cùng một khoản.

	Anh Việt 04/09/2026: *"Chống tạo Payment Entry trùng khi nhân viên bấm
	lại, reload trang hoặc webhook trả lại."* Khoá đi vào ô `reference_no`
	của chứng từ, nên phép chặn nằm ở DỮ LIỆU chứ không nằm ở nút bấm -
	bấm lại, tải lại trang hay webhook gọi lại đều đụng cùng một khoá.
	"""
	return ("THU:%s:%s" % ((si_name or "").strip(), (nguon or "").strip()))[:140]


# ------------------------------------------------------- phần cần Frappe


def dong_cua(si_name):
	"""Các dòng thanh toán của một hoá đơn."""
	from vagabond import thanh_toan_nhieu as ttn

	return ttn.dong_cua(si_name)


def bang_dong_cua(cac_si):
	"""Dòng thanh toán của nhiều hoá đơn, đọc một lượt."""
	from vagabond import thanh_toan_nhieu as ttn

	return ttn.bang_dong_cua(cac_si)


def si_co_dong_cong_no():
	"""Hoá đơn có ÍT NHẤT một dòng mang nhãn công nợ.

	Trước 04/09/2026 màn công nợ chỉ quét theo ô phương thức chính. Tờ trả
	hỗn hợp thì ô chính mang dòng LỚN NHẤT, nên tờ nào phần đã thu lớn hơn
	phần nợ là ô chính ghi "Chuyển khoản" và cả khoản nợ biến mất khỏi màn.
	Đây là đường thứ hai để tìm ra chúng.
	"""
	try:
		ds = frappe.get_all(
			"Vagabond Dong Thanh Toan",
			filters={"parenttype": SI, "pt": ["in", list(PT_KHONG_PHAI_THU)]},
			fields=["parent"], limit_page_length=0,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thu_tien: doc dong cong no")
		return set()
	return {r["parent"] for r in ds if r.get("parent")}


def tom_tat_thu(si_name):
	"""Tổng đơn, đã thu theo từng phương thức, còn nợ, trạng thái. CHỈ ĐỌC.

	Một chỗ tính duy nhất cho mọi màn cần bày con số này, để màn hoá đơn và
	màn công nợ không bao giờ nói hai số khác nhau về cùng một tờ.
	"""
	hd = frappe.db.get_value(
		SI, si_name,
		["name", "customer", "customer_name", "grand_total", "outstanding_amount",
			"vgb_pt_thanh_toan", "docstatus", "posting_date"],
		as_dict=True,
	)
	if not hd:
		return None
	dong = dong_cua(si_name)
	no = con_no_cua(hd.grand_total, hd.outstanding_amount, dong, hd.vgb_pt_thanh_toan)
	return {
		"name": hd.name,
		"khach": hd.customer or "",
		"ten_khach": hd.customer_name or "",
		"ngay": str(hd.posting_date or ""),
		"tong_don": flt(hd.grand_total),
		"da_thu": flt(hd.grand_total) - no,
		"theo_pt": [{"pt": p, "so_tien": flt(t)} for p, t in da_thu_theo_pt(dong)],
		"con_no": no,
		"trang_thai": trang_thai_thu(hd.grand_total, no),
		"du_no_so_cai": flt(hd.outstanding_amount),
		"co_dong": bool(dong),
	}


def tk_tien_thu(cong_ty, pt):
	"""Tiền thu bằng phương thức này VÀO tài khoản kế toán nào.

	CHỈ đọc tài khoản khai riêng cho chính phương thức đó. Không đoán, không
	lùi về tài khoản mặc định của công ty.

	VÌ SAO CHẶT ĐẾN THẾ - đo ngày 04/09/2026
	--------------------------------------------------------------------
	Cả 18 hình thức thanh toán trong hệ ĐỀU chưa khai tài khoản mặc định.
	Phép tra của luồng CHI (`tra_tien_app.tk_tien_chi`) có bốn đường lùi,
	đường cuối là tài khoản ngân hàng mặc định của công ty. Dùng nó cho
	luồng thu thì tiền mặt trong két cũng chạy vào tài khoản MB Bank, và
	sổ quỹ tiền mặt vĩnh viễn không khớp với két thật.

	Thà KHÔNG sinh chứng từ còn hơn sinh một chứng từ ghi sai chỗ tiền
	nằm: chưa ghi thì còn nhìn thấy mà đi ghi, ghi sai thì phải đi tìm.

	Trả cặp (tài khoản, Bank Account). Chưa khai thì trả cặp rỗng.
	"""
	cong_ty = (cong_ty or "").strip()
	pt = (pt or "").strip()
	if not (cong_ty and pt):
		return None, None
	if not frappe.db.exists("Mode of Payment", pt):
		return None, None
	tk = frappe.db.get_value(
		"Mode of Payment Account", {"parent": pt, "company": cong_ty}, "default_account"
	)
	if not tk:
		return None, None
	ba = frappe.db.get_value(
		"Bank Account", {"account": tk, "company": cong_ty, "is_company_account": 1}, "name"
	)
	return tk, ba


def loi_chua_khai_tk(pt):
	"""Câu báo khi chưa khai tài khoản cho một hình thức thanh toán.

	Anh Việt 04/09/2026: *"Mọi lỗi chặn thao tác phải nói rõ nguyên nhân và
	cách xử lý tiếp theo."* Nên câu này nói đúng ba điều: hỏng ở đâu, phải
	khai gì, và trong lúc chưa khai thì tờ hoá đơn ra sao.
	"""
	return (
		"Hình thức thanh toán \"%s\" chưa khai tài khoản tiền, nên chưa ghi "
		"nhận thanh toán vào sổ được. Nhờ kế toán mở Hình thức thanh toán "
		"\"%s\", thêm dòng công ty và chọn tài khoản tiền tương ứng (tiền mặt "
		"vào tài khoản quỹ, chuyển khoản vào tài khoản ngân hàng). Trong lúc "
		"chờ, hoá đơn vẫn đúng số tiền, chỉ là sổ cái còn ghi khách nợ." % (pt, pt)
	)


@frappe.whitelist()
def soat_hinh_thuc_chua_khai():
	"""CHỈ ĐỌC: hình thức thanh toán nào chưa khai tài khoản tiền.

	Đo ngày 04/09/2026: cả 18 hình thức đều chưa khai. Chưa khai xong thì
	luồng thu tiền mới không ghi được đồng nào vào sổ, nên đây là việc phải
	làm TRƯỚC khi nghiệm thu.
	"""
	if not ({"Accounts Manager", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Bảng này dành cho kế toán trưởng và quản lý hệ thống.")
	cty = frappe.db.get_single_value("Global Defaults", "default_company")
	ra = []
	for m in frappe.get_all("Mode of Payment", fields=["name", "enabled"], limit_page_length=0):
		if la_cong_no(m["name"]):
			continue
		tk, _ba = tk_tien_thu(cty, m["name"])
		if not tk:
			ra.append({"pt": m["name"], "dang_dung": bool(m.get("enabled"))})
	return {"cong_ty": cty, "chua_khai": ra, "so": len(ra)}


def _da_ghi_roi(khoa):
	"""Khoản thu mang khoá này đã có chứng từ chưa. Chặn ghi hai lần."""
	return bool(frappe.db.exists("Payment Entry", {"reference_no": khoa, "docstatus": ["<", 2]}))


def ghi_thu_tien(si_name, dong, nguon, ngay=None, ghi_chu=""):
	"""Sinh chứng từ thu tiền cho phần ĐÃ THU THẬT của một hoá đơn.

	`dong` là list dict {pt, so_tien}. Dòng mang nhãn công nợ bị bỏ qua -
	đó là phần chưa thu, ghi vào là tự xoá nợ của mình.

	Mỗi phương thức một chứng từ riêng, vì tiền vào những tài khoản khác
	nhau: tiền mặt vào két, chuyển khoản vào ngân hàng, quẹt thẻ vào tài
	khoản trung gian. Gộp một chứng từ là mất dấu ngay chỗ cần nhất.

	Trả về list tên chứng từ đã sinh. Đã sinh rồi thì trả list rỗng, không
	ném lỗi: người bấm hai lần không đáng bị một câu báo đỏ.
	"""
	hd = frappe.db.get_value(
		SI, si_name,
		["name", "company", "customer", "grand_total", "outstanding_amount",
			"due_date", "docstatus"],
		as_dict=True,
	)
	if not hd:
		frappe.throw("Không có hoá đơn %s." % si_name)
	if int(hd.docstatus or 0) != 1:
		frappe.throw("Hoá đơn %s chưa ghi sổ nên chưa ghi thu tiền được." % si_name)

	ngay = ngay or nowdate()
	ra = []
	con = flt(hd.outstanding_amount)
	for pt, so_tien in da_thu_theo_pt(dong):
		if con <= 0:
			break
		if khong_sinh_phieu(pt):
			# Hàng tặng: tờ đã tất toán bằng chi phí biếu tặng, không có
			# đồng nào vào két để mà lập phiếu thu.
			continue
		khoa = khoa_chong_trung(si_name, "%s|%s" % (nguon or "", pt))
		if _da_ghi_roi(khoa):
			continue
		phan_bo = min(flt(so_tien), con)
		if phan_bo <= 0:
			continue
		tk, ba = tk_tien_thu(hd.company, pt)
		if not tk:
			frappe.throw(loi_chua_khai_tk(pt))
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.company = hd.company
		pe.posting_date = ngay
		pe.party_type = "Customer"
		pe.party = hd.customer
		pe.paid_amount = phan_bo
		pe.received_amount = phan_bo
		pe.reference_no = khoa
		pe.reference_date = ngay
		if frappe.db.exists("Mode of Payment", pt):
			pe.mode_of_payment = pt
		pe.paid_to = tk
		if ba:
			pe.bank_account = ba
		pe.append("references", {
			"reference_doctype": SI,
			"reference_name": si_name,
			"total_amount": flt(hd.grand_total),
			"outstanding_amount": con,
			"allocated_amount": phan_bo,
			"due_date": hd.due_date,
		})
		pe.remarks = ("Thu tiền hoá đơn %s bằng %s, số tiền %s đ.%s" % (
			si_name, pt, "{:,.0f}".format(phan_bo),
			(" " + ghi_chu) if ghi_chu else ""))[:1000]
		pe.setup_party_account_field()
		pe.set_missing_values()
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		pe.submit()
		ra.append(pe.name)
		con -= phan_bo
	return ra


@frappe.whitelist()
def tom_tat(si=None):
	"""Cho màn hình: tờ này tổng bao nhiêu, đã thu gì, còn nợ bao nhiêu.

	Anh Việt 04/09/2026: *"Không bắt nhân viên tự suy ra trạng thái kế toán
	từ màn hình."* Một lần gọi ra đủ bốn con số, không ai phải cộng tay.
	"""
	si = (si or "").strip()
	if not si:
		return None
	if not frappe.has_permission(SI, "read", doc=si):
		frappe.throw("Không có quyền xem hoá đơn này.")
	return tom_tat_thu(si)


@frappe.whitelist()
def soat_thieu_chung_tu(gioi_han=500):
	"""CHỈ ĐỌC: những tờ đã thu tiền mà sổ cái vẫn ghi khách nợ.

	Đây là bảng anh Việt bảo liệt kê ra ngày 04/09/2026 thay vì để máy tự
	sửa. Đo hôm đó: 2.183 tờ, gần 1,2 tỷ, phần lớn là chuyển khoản và quẹt
	thẻ đã vào tài khoản từ lâu.

	KHÔNG sinh chứng từ, KHÔNG đụng một tờ nào - điều 11. Chị Dung đọc bảng
	này rồi quyết làm gì với chúng.
	"""
	if not ({"Accounts Manager", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Bảng này dành cho kế toán trưởng và quản lý hệ thống.")
	rows = frappe.get_all(
		SI,
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "posting_date", "customer_name", "grand_total",
			"outstanding_amount", "vgb_pt_thanh_toan"],
		order_by="posting_date asc", limit_page_length=0,
	)
	theo_pt, tong = {}, 0.0
	ra = []
	for r in rows:
		pt = (r.get("vgb_pt_thanh_toan") or "").strip()
		# To mang co Cong no la no THAT, khong nam trong bang nay.
		if la_cong_no(pt):
			continue
		o = theo_pt.setdefault(pt or "(chưa ghi phương thức)", {"so": 0, "tien": 0.0})
		o["so"] += 1
		o["tien"] += flt(r.outstanding_amount)
		tong += flt(r.outstanding_amount)
		if len(ra) < int(gioi_han or 500):
			ra.append(r)
	return {
		"so_to": sum(v["so"] for v in theo_pt.values()),
		"tong": tong,
		"theo_pt": [{"pt": k, "so": v["so"], "tien": v["tien"]}
			for k, v in sorted(theo_pt.items(), key=lambda x: -x[1]["tien"])],
		"hoa_don": ra,
	}

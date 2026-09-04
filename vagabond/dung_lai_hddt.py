# -*- coding: utf-8 -*-
"""Dựng lại hoá đơn mua theo đúng bản hoá đơn điện tử gốc.

Ca thật ngày 26/08/2026, hoá đơn HDM-26-08-00012 của Thanh An Eggpack
------------------------------------------------------------------------
Bản đồng bộ về ĐÚNG: trứng gà 1.500 quả, đơn giá 2.190,48, tiền hàng
3.285.720, tổng 3.450.000. Khớp từng đồng với tờ giấy.

Ngày 17/08 có người bấm nút "Nối phiếu nhập kho" của ERPNext trên Desk.
Nút đó KHÔNG nối, nó CHÉP dòng hàng từ phiếu nhập đè lên dòng hàng của hoá
đơn. Phiếu nhập ghi giá đặt hàng 2.100, nên tiền hàng tụt xuống 3.150.000
và tổng còn 3.314.280. Mất 135.720 đồng, không ai được báo gì.

Đây là chỗ khác nhau giữa hai nút trông giống nhau:

  * Nút "Nối phiếu nhập kho" của ERPNext trên Desk: chép dòng hàng của
    phiếu nhập sang, GHI ĐÈ số lượng và đơn giá của hoá đơn.
  * Màn "Đối chiếu hoá đơn mua" trong app: chỉ gắn dòng hoá đơn vào dòng
    phiếu nhập, KHÔNG đụng tới số lượng hay đơn giá.

Cửa chặn ghi sổ đã có sẵn (`mua_dich_vu.chan_lech_tong`) nên tờ sai không
vào được sổ cái. Nhưng chặn ở phút chót thì người ta đã gõ xong xuôi mới
biết, mà lại không có đường nào để dựng lại số cũ ngoài gõ tay.

Tệp này bù hai chỗ đó, và từ v319 đi xa hơn theo lệnh của anh Việt cùng
ngày: "phải đồng bộ giữa cả app và cả desktop về tất cả các nút tính năng".
Bản v318 mới chỉ CẢNH BÁO lúc lưu rồi dặn người ta đừng bấm nút bên màn
quản trị - vá bằng lời dặn, không phải vá hệ thống. Nay luật nằm ở hook
`dong_bo_luc_luu`, chạy trên MỌI lần lưu bất kể bấm từ đâu: dòng hàng lệch
khỏi bản gốc là máy dựng lại và giữ liên kết phiếu nhập. Hai nơi bấm, một
bản chất.

Đếm ngày 26/08/2026: 3.077 hoá đơn mua sinh từ hoá đơn điện tử, 338 tờ còn
nháp đang lệch tổng, và 3 tờ ĐÃ GHI SỔ mà lệch. Anh Việt cấp toàn quyền xử
cả hai nhóm trong cùng ngày - `dung_lai_tat_ca` cho tờ nháp,
`sua_to_da_ghi_so` cho tờ đã vào sổ.
"""

import json

import frappe
from frappe.utils import cint, flt

from vagabond import mua_dich_vu

DT_HD = "MInvoice Invoice"
PI = "Purchase Invoice"

QUYEN = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"Purchase Manager",
	"Purchase User",
}

# Cùng ngưỡng với cửa chặn ghi sổ, để người dùng chỉ phải nhớ MỘT con số.
NGUONG = mua_dich_vu.NGUONG_LECH


# ----------------------------------------------------------------- thuần


def huong_lech(tong_erp, tong_hddt):
	"""Phiếu đang thiếu hay thừa so với hoá đơn điện tử. THUẦN.

	Trả ("khop", 0) | ("thieu", x) | ("thua", x), x luôn dương.
	"""
	a, b = flt(tong_erp), flt(tong_hddt)
	if not mua_dich_vu.lech_qua_nguong(a, b, NGUONG):
		return "khop", 0.0
	return ("thieu", b - a) if a < b else ("thua", a - b)


def cau_canh_bao(ten, tong_erp, tong_hddt):
	"""Câu báo cho người đang lưu phiếu. THUẦN, không chạm Frappe."""
	viec, so = huong_lech(tong_erp, tong_hddt)
	if viec == "khop":
		return ""
	return (
		"Hoá đơn %s đang %s %s đồng so với bản hoá đơn điện tử của nhà cung cấp "
		"(phiếu %s đồng, hoá đơn điện tử %s đồng). Số trên hoá đơn điện tử là số "
		"đã gửi cơ quan thuế nên không ghi sổ được khi còn lệch. "
		'Bấm "Dựng lại theo hoá đơn điện tử" ở màn Đối chiếu để lấy lại số gốc. '
		'Lưu ý nút "Nối phiếu nhập kho" bên màn quản trị sẽ chép đè giá của '
		"phiếu nhập lên hoá đơn, đó thường là nguyên nhân."
		% (ten, "thiếu" if viec == "thieu" else "thừa", _so(so), _so(tong_erp), _so(tong_hddt))
	)


def _so(x):
	"""Số tiền có dấu chấm ngăn nghìn, không phần thập phân. THUẦN."""
	try:
		n = int(round(float(x or 0)))
	except (TypeError, ValueError):
		return "0"
	dau = "-" if n < 0 else ""
	s = str(abs(n))
	cum = []
	while s:
		cum.insert(0, s[-3:])
		s = s[:-3]
	return dau + ".".join(cum)


def doc_chi_tiet(chi_tiet):
	"""Danh sách dòng hàng thô của một hoá đơn điện tử. THUẦN.

	Chuỗi hỏng thì trả danh sách rỗng chứ không nổ: một tờ hỏng không được
	làm chết cả nhịp.
	"""
	if isinstance(chi_tiet, (list, tuple)):
		return list(chi_tiet)
	try:
		ds = json.loads(chi_tiet or "[]")
	except (ValueError, TypeError):
		return []
	return ds if isinstance(ds, list) else []


def tien_dong_may_ghi(sl, gia, dp_gia, dp_tien, dp_sl=None):
	"""Số tiền một dòng SAU KHI máy làm tròn. THUẦN.

	VÌ SAO PHẢI TÍNH TRƯỚC PHẦN LÀM TRÒN - ca thật 27/08/2026
	--------------------------------------------------------------------
	Sau v322 còn 11 tờ lệch từ 1 tới 10 đồng. Ví dụ ACC-PINV-2026-01427:
	hoá đơn ghi 420 đơn vị, đơn giá 5.136,683, thành tiền 2.157.407. ERPNext
	chỉ giữ đơn giá tới hai số lẻ nên ghi 5.136,68, nhân ra 2.157.405,6, hụt
	1,4 đồng. Phép nắn cũ tính trên đơn giá GỐC nên thấy khớp và không nắn
	gì, phần hụt chỉ sinh ra sau khi máy lưu.

	Nên phải cân theo con số máy SẼ ghi, chứ không theo con số hoá đơn đọc
	lên. Một đồng cũng phải đúng: cửa chặn ghi sổ lấy ngưỡng một đồng, hụt
	một đồng là tờ đó nằm lại mãi.

	Ô SỐ LƯỢNG cũng bị cắt y như ô đơn giá. Ca thật HDM-2026-00398: hoá đơn
	ghi 2,762431 đơn vị, máy chỉ giữ ba số lẻ nên ghi 2,762, hụt 9,36 đồng.
	Bản đầu của hàm này chỉ cắt đơn giá nên còn sót đúng loại đó.
	"""
	return flt(flt(sl, dp_sl) * flt(gia, dp_gia), dp_tien)


def ten_dong_bu(so_tien):
	"""Tên dòng bù cho phần chênh. THUẦN.

	Chênh vài đồng là do làm tròn, gọi đúng tên để kế toán khỏi đi tìm.
	"""
	return ("Chênh lệch làm tròn theo hoá đơn điện tử"
		if abs(flt(so_tien)) < 100 else "Phí khác theo hoá đơn")


def khoa_ten(ten):
	"""Khoá so khớp một tên hàng nhà cung cấp ghi. THUẦN.

	Bỏ khoảng trắng thừa và hạ chữ thường. KHÔNG bỏ dấu, vì "Trân châu
	khoai (ô long)" và "Trân châu khoai (khoai môn)" là hai món khác nhau
	và nhập nhèm hai cái đó là gắn nhầm mã hàng.
	"""
	return " ".join(str(ten or "").strip().lower().split())


def ten_ncc_cua_dong(d):
	"""Tên hàng nhà cung cấp ghi, đọc từ một dòng chứng từ. THUẦN.

	Ô `ten_hang_ncc` là chỗ tin được: ERPNext thay `item_name` bằng tên Món
	của mình ngay khi dòng được gắn mã hàng, nên đọc `item_name` không thôi
	là mất dấu.
	"""
	lay = d.get if hasattr(d, "get") else (lambda k, v=None: getattr(d, k, v))
	for o in ("ten_hang_ncc", "item_name"):
		v = str(lay(o) or "").strip()
		if v:
			return v
	return ""


def nen_nan_don_vi(uom_hien, hs_hien, uom_dung, hs_dung):
	"""Có nên nắn đơn vị của một dòng về (uom_dung, hs_dung) không. THUẦN.

	CHỈ nắn khi dòng đang mang đơn vị máy hạ tạm, tức hệ số đúng bằng 1,
	mà phép tra ra được một hệ số thật khác 1. Người đã tự khai đơn vị thì
	hệ số của họ khác 1, và của họ thì để yên - máy không đè lên khai báo
	của người.
	"""
	if not uom_dung:
		return False
	if str(uom_hien or "").strip() == str(uom_dung or "").strip():
		return False
	return abs(flt(hs_hien) - 1.0) < 1e-9 and abs(flt(hs_dung) - 1.0) > 1e-9


def xep_ma_theo_dong_goc(ma_tren_to, khoa_goc, so_dong_to):
	"""Mã hàng đang có trên tờ, xếp về đúng vị trí dòng của bản gốc. THUẦN.

	`ma_tren_to` là list (khoá tên của dòng, mã hàng) theo thứ tự dòng trên
	chứng từ; `khoa_goc` là list khoá tên của các dòng bản gốc.

	Ghép bằng TÊN trước, vì tên là thứ nhà cung cấp ghi và không đổi. Tên
	nào xuất hiện hai lần trong bản gốc thì bỏ qua, không đoán.

	Chỉ khi dòng trên tờ không còn tên nào để so mới ghép theo VỊ TRÍ, và
	chỉ khi số dòng của tờ bằng số dòng bản gốc hoặc hơn đúng một dòng
	(dòng bù chênh lệch). Lệch hơn thế là tờ đã bị xáo, đoán vị trí lúc đó
	là gắn nhầm mã hàng cho nhau.
	"""
	dem = {}
	for i, k in enumerate(khoa_goc):
		dem.setdefault(k, []).append(i)
	duy_nhat = {k: v[0] for k, v in dem.items() if len(v) == 1 and k}

	ra = {}
	con_lai = []
	for vi_tri, (khoa, ma) in enumerate(ma_tren_to):
		if not ma:
			continue
		if khoa and khoa in duy_nhat:
			ra.setdefault(duy_nhat[khoa], ma)
		elif not khoa:
			con_lai.append((vi_tri, ma))

	xep_duoc = so_dong_to in (len(khoa_goc), len(khoa_goc) + 1)
	if xep_duoc:
		for vi_tri, ma in con_lai:
			if vi_tri < len(khoa_goc):
				ra.setdefault(vi_tri, ma)
	return ra


# ------------------------------------------------------- phan can Frappe


def _kiem_quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Việc này dành cho kế toán và thu mua.")


def _goc(ma_minvoice):
	"""Bản hoá đơn điện tử gốc của một phiếu. None nếu phiếu không từ đó ra."""
	ma = (ma_minvoice or "").strip()
	if not ma:
		return None
	return frappe.db.get_value(
		DT_HD, ma,
		["name", "so_hd", "ky_hieu", "ngay_lap", "tong_tien", "tien_truoc_thue",
			"tien_thue", "mst_doi_tac", "nguoi_mua_ban", "chi_tiet"],
		as_dict=True,
	)


def muc_tieu_truoc_thue(g):
	"""Tiền hàng trước thuế mà tờ chứng từ PHẢI ra bằng. THUẦN.

	VÌ SAO KHÔNG DÙNG THẲNG Ô `tien_truoc_thue` - sự cố 27/08/2026
	--------------------------------------------------------------------
	Bản v319 neo vào ô đó và làm hỏng 5 tờ thật ngay trong lượt chạy đầu:

	  * HDM-26-08-00096 Nhà Sen: bản gốc ghi tổng 3.650.000 nhưng ô
	    `tien_truoc_thue` để 0 (nhà cung cấp không khai tách). Máy hiểu là
	    dòng hàng THỪA 3.650.000 nên đặt giảm giá đúng bằng cả tờ, tổng về
	    0 đồng. Bốn tờ bị về 0 đều đúng kiểu này.
	  * HDM-26-08-00124 Avanti: ô đó ghi 26.953.500 nhưng dòng hàng dựng ra
	    tổng 31.453.500, lệch 4.500.000, thành ra tờ phình lên.

	Con số ĐÁNG TIN duy nhất là `tong_tien`: đó là số nhà cung cấp đã gửi cơ
	quan thuế, và cũng chính là số mà cửa chặn ghi sổ soi. Nên lấy tổng trừ
	thuế ra tiền hàng, chỉ khi tổng không có mới đành quay về ô cũ.
	"""
	tong = flt(g.get("tong_tien"))
	if tong:
		return tong - flt(g.get("tien_thue"))
	return flt(g.get("tien_truoc_thue"))


def _quyen_manh():
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw("Việc này chỉ dành cho kế toán trưởng và quản lý hệ thống.")


def _dung_dong_tai_cho(doc, g):
	"""Dựng lại bảng dòng hàng NGAY TRÊN doc theo hoá đơn điện tử. Không lưu.

	Đây là MỘT đường dựng duy nhất, dùng chung cho nút trên app, cho hook
	chạy lúc lưu từ màn quản trị, cho lượt sửa hàng loạt và cho việc sửa tờ
	đã ghi sổ. Anh Việt chốt 26/08/2026: một cái nút mà hai nơi bấm ra hai
	bản chất là cấm, nên bản chất phải nằm ở đây, tầng dưới cùng, không nằm
	trong từng nút.

	Dựng đủ danh sách dòng mới TRƯỚC rồi mới thay vào doc, để lỡ giữa chừng
	có lỗi thì doc còn nguyên, không bao giờ lưu một tờ cụt dòng.

	NEO VÀO ĐÂU: xem `muc_tieu_truoc_thue`. Bản v319 neo vào ô
	`tien_truoc_thue` và việc đó đã làm hỏng 5 tờ thật, đọc mục đó trước khi
	định đổi lại.
	"""
	dong_goc = doc_chi_tiet(g.get("chi_tiet"))
	if not dong_goc:
		frappe.throw(
			"Bản hoá đơn điện tử %s không còn dòng hàng nào để dựng lại."
			% (g.get("so_hd") or "")
		)
	from vagabond import minvoice_chung_tu as mc

	goc_mst = (g.get("mst_doi_tac") or "").split("-")[0]
	tk = None
	for d in doc.get("items") or []:
		if d.get("expense_account"):
			tk = d.expense_account
			break
	# MÃ HÀNG NGƯỜI VỪA GẮN PHẢI SỐNG SÓT QUA LƯỢT DỰNG LẠI.
	#
	# Ca thật HDM-26-08-00149 Green Ball, ngày 04/09/2026, Uyên báo:
	# *"em đã gắn mã ánh xạ, lưu xong mất cái mã em gắn và hiện ra thông
	# báo, không nhảy qua chỗ kế toán duyệt."*
	#
	# Chuỗi sự việc: gắn mã hàng vào một dòng thì ERPNext lấy lại đơn giá
	# theo Bảng giá nhập của Món, tiền dòng đổi (69.000 thành 74.556), tổng
	# tờ lệch khỏi hoá đơn điện tử, hook lưu thấy lệch nên dựng lại cả bảng
	# dòng hàng - mà đường dựng chỉ lấy mã hàng từ BẢNG ÁNH XẠ, không bao
	# giờ nhìn cái người vừa gõ. Nên công gõ bay mất.
	#
	# Hậu quả kéo theo đúng như Uyên tả: dòng không còn mã hàng thì nối
	# phiếu nhập kho từ chối, không nối được thì không ghi sổ được, không
	# ghi sổ thì tờ không sang bước kế toán duyệt. Một lỗi, ba triệu chứng.
	#
	# Nay: bảng ánh xạ tra không ra thì lấy mã hàng ĐANG CÓ TRÊN TỜ.
	giu = _ma_dang_gan(doc, dong_goc)
	moi = []
	for vi_tri, it in enumerate(dong_goc):
		x = mc.dong_tu_hoa_don(it)
		ma, uom, he_so = mc._tra_ma_hang(x, goc_mst, doc.supplier)
		if not ma and giu.get(vi_tri):
			ma = giu[vi_tri]
			uom, he_so = mc.don_vi_theo_ma(ma, x.get("dvt"))
		moi.append(mc._dong_pi(x, tk, ma, uom, he_so))
	dp_gia, dp_tien, dp_sl = _do_chinh_xac()
	tong_dong = sum(
		tien_dong_may_ghi(d.get("qty"), d.get("rate"), dp_gia, dp_tien, dp_sl)
		for d in moi
	)
	viec, so_tien = mc.can_theo_truoc_thue(tong_dong, muc_tieu_truoc_thue(g))
	if viec == "phi":
		moi.append(mc._dong_pi({
			"ma": "", "ten": ten_dong_bu(so_tien), "dvt": None,
			"sl": 1, "gia": so_tien, "tien": so_tien,
		}, tk))
	doc.set("items", [])
	tt = doc.get("cost_center")
	for d in moi:
		if tt:
			d["cost_center"] = tt
		doc.append("items", d)
	doc.apply_discount_on = "Net Total"
	doc.discount_amount = so_tien if viec == "giam" else 0
	_dung_thue_tai_cho(doc, g)
	mc.bo_mau_thue_mat_hang(doc)
	return len(doc.get("items"))


def _khoa_goc(dong_goc):
	"""Khoá tên của từng dòng bản gốc, đúng thứ tự."""
	from vagabond import minvoice_chung_tu as mc

	return [khoa_ten(mc.dong_tu_hoa_don(it).get("ten")) for it in dong_goc]


def _ma_dang_gan(doc, dong_goc):
	"""Mã hàng đang có trên tờ, xếp về đúng vị trí dòng của bản gốc."""
	tren_to = [
		(khoa_ten(ten_ncc_cua_dong(d)), str(d.get("item_code") or "").strip())
		for d in (doc.get("items") or [])
	]
	return xep_ma_theo_dong_goc(tren_to, _khoa_goc(dong_goc), len(tren_to))


def ghim_lai_theo_goc(doc, g):
	"""Kéo số lượng và đơn giá từng dòng về đúng bản gốc, GIỮ NGUYÊN mã hàng.

	Đây là bước NHẸ, chạy trước khi tính tới chuyện dựng lại cả bảng dòng
	hàng. Dựng lại thì đúng số nhưng thay mới toàn bộ các dòng, kéo theo
	việc phải nối lại phiếu nhập và làm người dùng thấy tờ của mình bị thay
	sau lưng. Kéo tại chỗ thì chỉ đụng đúng hai ô làm sai số tiền.

	Chỉ đụng dòng nào ghép được với một dòng bản gốc BẰNG TÊN. Dòng bù
	chênh lệch do máy tự thêm không có tên trong bản gốc nên không bị đụng.

	Trả về số dòng đã kéo lại.
	"""
	dong_goc = doc_chi_tiet(g.get("chi_tiet"))
	if not dong_goc:
		return 0
	from vagabond import minvoice_chung_tu as mc

	theo_khoa = {}
	dem = {}
	for it in dong_goc:
		x = mc.dong_tu_hoa_don(it)
		k = khoa_ten(x.get("ten"))
		if not k:
			continue
		dem[k] = dem.get(k, 0) + 1
		theo_khoa[k] = x
	# Tên trùng nhau trong cùng một tờ thì không đoán dòng nào là dòng nào.
	for k, n in dem.items():
		if n > 1:
			theo_khoa.pop(k, None)

	da = 0
	for d in doc.get("items") or []:
		x = theo_khoa.get(khoa_ten(ten_ncc_cua_dong(d)))
		if not x:
			continue
		sua = False
		if flt(d.get("qty")) != flt(x.get("sl")):
			d.qty = x.get("sl")
			sua = True
		if flt(d.get("rate")) != flt(x.get("gia")):
			d.rate = x.get("gia")
			sua = True
		if sua:
			# Ghim luôn giá bảng, không thì ERPNext lại lấy giá Bảng giá nhập
			# điền đè lên ngay trong chính lượt lưu này.
			d.price_list_rate = x.get("gia")
			d.discount_percentage = 0
			d.discount_amount = 0
			d.margin_rate_or_amount = 0
			da += 1
		ma = str(d.get("item_code") or "").strip()
		if not ma:
			continue
		uom, he_so = mc.don_vi_theo_ma(ma, x.get("dvt"))
		if nen_nan_don_vi(d.get("uom"), d.get("conversion_factor"), uom, he_so):
			d.uom = uom
			d.conversion_factor = he_so
	return da


def hoc_ma_hang(doc, g):
	"""Ghi nhớ mã hàng người gõ tay vào bảng ánh xạ. Trả số dòng đã nhớ.

	VÌ SAO PHẢI HỌC Ở ĐÂY (04/09/2026)
	--------------------------------------------------------------------
	Màn Đối chiếu trong app đã có nút "Gắn mã hàng" và nút đó có ghi nhớ.
	Nhưng người gõ thẳng trên màn quản trị thì không đi qua nút đó, nên
	công gõ chỉ nằm trên đúng một tờ và tờ sau của cùng nhà cung cấp lại
	phải gõ lại từ đầu. Anh Việt chốt 26/08/2026: một việc mà hai nơi bấm
	ra hai bản chất là cấm. Nên phép ghi nhớ phải nằm ở tầng lưu chứng từ,
	không nằm trong một cái nút.

	CHỈ ghi khi ô nhớ còn TRỐNG. Đổi một ánh xạ đã có là quyết định phân
	loại kế toán của người, điều 11 không cho máy tự làm.

	Chỉ học từ dòng có tên KHỚP một dòng của bản gốc, để không bao giờ học
	nhầm từ dòng bù chênh lệch do chính máy thêm vào.
	"""
	mst = (g.get("mst_doi_tac") or "").split("-")[0]
	if not mst:
		return 0
	# GHI VÀO Ô NHỚ BẰNG ĐÚNG CHỮ CỦA BẢN GỐC, không phải chữ đang nằm trên
	# chứng từ. Phép tra ánh xạ ở `_tra_ma_hang` so khớp CHÍNH XÁC với tên
	# trên hoá đơn điện tử, nên lệch một chữ hoa hay một khoảng trắng là
	# ghi nhớ xong vẫn không ai đọc ra.
	from vagabond import minvoice_chung_tu as mc

	ten_goc = {}
	for it in doc_chi_tiet(g.get("chi_tiet")):
		t = str(mc.dong_tu_hoa_don(it).get("ten") or "").strip()
		if t:
			ten_goc.setdefault(khoa_ten(t), t[:140])
	if not ten_goc:
		return 0
	da = 0
	for d in doc.get("items") or []:
		ma = str(d.get("item_code") or "").strip()
		ten = ten_goc.get(khoa_ten(ten_ncc_cua_dong(d)))
		if not (ma and ten):
			continue
		cu = frappe.db.get_value(
			"MInvoice NCC Map", {"supplier_mst": mst, "ten_ncc": ten}, "name"
		)
		if cu:
			if (frappe.db.get_value("MInvoice NCC Map", cu, "item_code") or "").strip():
				continue
			frappe.db.set_value("MInvoice NCC Map", cu, "item_code", ma)
		else:
			m = frappe.get_doc({
				"doctype": "MInvoice NCC Map",
				"supplier_mst": mst,
				"ten_ncc": ten,
				"item_code": ma,
			})
			m.flags.ignore_permissions = True
			m.insert(ignore_permissions=True)
		da += 1
	return da


def _tong_thue_tren_phieu(doc):
	return sum(flt(t.get("tax_amount")) for t in doc.get("taxes") or [])


def _do_chinh_xac():
	"""(số lẻ ô đơn giá, số lẻ ô thành tiền, số lẻ ô số lượng) máy đang dùng."""
	try:
		gia = cint(frappe.get_precision(PI + " Item", "rate"))
		tien = cint(frappe.get_precision(PI + " Item", "amount"))
		sl = cint(frappe.get_precision(PI + " Item", "qty"))
	except Exception:
		gia, tien, sl = 0, 0, 0
	return (gia or 2), (tien or 2), (sl or 3)


def _tk_thue_vao(doc):
	"""Tài khoản thuế GTGT được khấu trừ của công ty. None nếu không có."""
	for t in doc.get("taxes") or []:
		tk = (t.get("account_head") or "").strip()
		if tk.startswith("1331"):
			return tk
	try:
		return frappe.db.get_value(
			"Account", {"company": doc.get("company"), "name": ["like", "1331 -%"]}, "name"
		)
	except Exception:
		return None


def _dung_thue_tai_cho(doc, g):
	"""Dựng lại bảng thuế theo đúng bản hoá đơn điện tử. Không lưu.

	VÌ SAO PHẢI DỰNG CẢ THUẾ - ca thật 27/08/2026
	--------------------------------------------------------------------
	Nhóm hoá đơn LARAFARM đều lệch đúng 51.200 đồng. Bản gốc ghi thuế 0,
	dòng hàng dựng ra đúng 790.000, nhưng trên chứng từ còn sót hai dòng
	thuế "On Net Total" 1331 và 33311, mỗi dòng 25.600, do mẫu thuế của
	danh mục Món áp vào lúc tờ được sinh ra trước bản v315. Dựng lại mỗi
	dòng hàng thì tổng vẫn lệch, vì phần lệch nằm ở bảng thuế.

	Số thuế trên hoá đơn điện tử là số nhà cung cấp đã gửi cơ quan thuế.
	Dựng lại theo hoá đơn điện tử thì phải dựng cả phần đó, nếu không thì
	chỉ dựng được một nửa tờ.
	"""
	tien_thue = flt(g.get("tien_thue"))
	tk = _tk_thue_vao(doc)
	tt = doc.get("cost_center")
	doc.set("taxes", [])
	if tk and tien_thue:
		doc.append("taxes", {
			"charge_type": "Actual", "account_head": tk,
			"description": "Thuế GTGT được khấu trừ",
			"tax_amount": tien_thue,
			"category": "Total", "add_deduct_tax": "Add",
			"cost_center": tt,
		})
	doc.taxes_and_charges = None
	return tien_thue


def du_kien_tong(doc, g):
	"""Tổng tiền tờ này SẼ thành bao nhiêu nếu dựng lại. Không đụng doc.

	Tính trước rồi mới quyết có dựng hay không. Nhờ vậy không bao giờ có
	chuyện dựng dở rồi lưu ra một tờ tệ hơn lúc chưa dựng.
	"""
	dong_goc = doc_chi_tiet(g.get("chi_tiet"))
	if not dong_goc:
		return None
	try:
		from vagabond import minvoice_chung_tu as mc

		goc_mst = (g.get("mst_doi_tac") or "").split("-")[0]
		dp_gia, dp_tien, dp_sl = _do_chinh_xac()
		tong_dong = 0.0
		for it in dong_goc:
			x = mc.dong_tu_hoa_don(it)
			tong_dong += tien_dong_may_ghi(
				x.get("sl"), x.get("gia"), dp_gia, dp_tien, dp_sl)
		viec, so_tien = mc.can_theo_truoc_thue(tong_dong, muc_tieu_truoc_thue(g))
		net = tong_dong + (so_tien if viec == "phi" else 0) - (so_tien if viec == "giam" else 0)
		# Thuế lấy theo BẢN GỐC, không lấy theo bảng thuế đang có trên phiếu:
		# `_dung_thue_tai_cho` sẽ dựng lại bảng đó theo đúng bản gốc.
		return net + flt(g.get("tien_thue"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: du kien tong")
		return None


def dung_lai_co_loi_khong(doc, g):
	"""Dựng lại tờ này có làm nó ĐÚNG HƠN không. Trả (nen_dung, ly_do).

	Đây là chốt chặn quan trọng nhất của tệp, thêm sau sự cố 27/08/2026 do
	chính bản v319 gây ra: đừng bao giờ ghi đè một tờ bằng thứ mình chưa
	kiểm là đúng.
	"""
	goc = flt(g.get("tong_tien"))
	if not goc:
		return False, "bản hoá đơn điện tử không ghi tổng tiền"
	du_kien = du_kien_tong(doc, g)
	if du_kien is None:
		return False, "không dựng thử được dòng hàng từ bản gốc"
	if mua_dich_vu.lech_qua_nguong(du_kien, goc, NGUONG):
		return False, (
			"dựng lại sẽ ra %s đồng, vẫn chưa khớp bản gốc %s đồng"
			% (_so(du_kien), _so(goc))
		)
	return True, ""


def _phieu_da_noi(doc):
	return sorted({
		(d.get("purchase_receipt") or "").strip()
		for d in doc.get("items") or []
	} - {""})


def _noi_lai(doc, phieu):
	"""Gắn lại các phiếu nhập đã nối trước đó, tốt nhất có thể.

	Gắn không được thì thôi chứ không chặn: số tiền đúng quan trọng hơn
	liên kết, và liên kết luôn nối lại tay được ở màn Đối chiếu.
	"""
	if not phieu:
		return []
	try:
		from vagabond import doi_chieu_mua

		return doi_chieu_mua._noi(doc, list(phieu))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: noi lai phieu nhap")
		return ["Chưa gắn lại được phiếu nhập, vào màn Đối chiếu nối tay."]


def _tong_dong_hien_tai(doc):
	"""Tiền hàng trước thuế theo dòng đang có trên doc, trừ giảm giá."""
	tong = 0.0
	for d in doc.get("items") or []:
		tong += flt(d.get("qty")) * flt(d.get("rate"))
	return tong - flt(doc.get("discount_amount"))


def dong_bo_luc_luu(doc, method=None):
	"""Hook chạy MỌI lần lưu hoá đơn mua, bất kể lưu từ nút nào, màn nào.

	Anh Việt 26/08/2026: hai nút cùng tên mà hai bản chất là quá nguy hiểm,
	không được xử lý bằng lời dặn "chỉ bấm bên app". Nên luật đặt ở đây,
	tầng dưới cùng của việc lưu chứng từ: tờ sinh từ hoá đơn điện tử mà
	dòng hàng bị đè lệch đi - dù do nút "Nối phiếu nhập kho" bên màn quản
	trị, nút "Lấy mặt hàng từ", hay tay ai gõ - thì máy dựng lại đúng bản
	gốc ngay trong lần lưu đó và GIỮ LẠI liên kết phiếu nhập vừa chọn.
	Từ giờ bấm ở đâu cũng ra một kết quả.

	Đặt ở before_validate chứ không validate: ERPNext tính lại tổng tiền
	SAU before_validate, đổi dòng ở validate là tổng không được tính lại -
	cùng lý do với hook gom dòng của hoá đơn dịch vụ ngay phía trên.

	Mọi lỗi ở đây chỉ được ghi nhật ký, không bao giờ làm rớt việc lưu.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		g = _goc(doc.get("custom_minvoice_id"))
		if not g:
			return
		# HỌC TRƯỚC, DỰNG SAU. Ghi nhớ mã hàng người vừa gõ vào bảng ánh xạ
		# ngay đầu lượt lưu, để nếu bên dưới có phải dựng lại cả bảng dòng
		# hàng thì phép tra ánh xạ đã thấy mã đó và tự gắn lại. Hai lớp giữ
		# cùng một thứ, hỏng một lớp vẫn còn lớp kia.
		try:
			hoc_ma_hang(doc, g)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: hoc ma hang")
		muc_tieu = muc_tieu_truoc_thue(g)
		if not muc_tieu:
			return
		if not mua_dich_vu.lech_qua_nguong(_tong_dong_hien_tai(doc), muc_tieu, NGUONG):
			return
		# BƯỚC NHẸ TRƯỚC KHI TÍNH TỚI DỰNG LẠI. Kéo số lượng và đơn giá của
		# từng dòng về đúng bản gốc mà không thay dòng nào. Đủ để chữa ca
		# hay gặp nhất - gắn mã hàng xong ERPNext lấy giá bảng điền đè - mà
		# không đụng tới mã hàng, đơn vị hay liên kết phiếu nhập của người.
		da_ghim = ghim_lai_theo_goc(doc, g)
		if da_ghim and not mua_dich_vu.lech_qua_nguong(
			_tong_dong_hien_tai(doc), muc_tieu, NGUONG
		):
			frappe.msgprint(
				"Số lượng và đơn giá vừa bị đổi lệch khỏi hoá đơn điện tử %s/%s, "
				"là số nhà cung cấp đã gửi cơ quan thuế, nên hệ thống kéo lại "
				"đúng bản gốc trong lần lưu này. Mã hàng và phiếu nhập đã nối "
				"trên tờ vẫn giữ nguyên."
				% (g.get("ky_hieu") or "", g.get("so_hd") or ""),
				title="Giữ đúng số hoá đơn điện tử", indicator="orange",
			)
			return
		nen, vi_sao = dung_lai_co_loi_khong(doc, g)
		if not nen:
			# KHÔNG ĐỤNG VÀO TỜ. Bài học 27/08/2026: bản v319 cứ dựng bừa rồi
			# lưu, làm bốn tờ về 0 đồng và một tờ phình thêm 4,5 triệu. Chưa
			# chắc đúng thì để yên và nói cho người ta biết.
			frappe.msgprint(
				"Tờ này đang lệch với hoá đơn điện tử %s/%s và hệ thống chưa dựng "
				"lại được: %s. %s Nhờ kế toán đối chiếu tay và đừng ghi sổ khi "
				"còn lệch."
				% (
					g.get("ky_hieu") or "", g.get("so_hd") or "", vi_sao,
					(
						"Hệ thống đã kéo %d dòng về đúng số lượng và đơn giá của "
						"bản gốc, phần còn lại giữ nguyên như đang có." % da_ghim
					) if da_ghim else
					"Hệ thống giữ nguyên tờ như đang có.",
				),
				title="Lệch so với hoá đơn điện tử", indicator="red",
			)
			return
		phieu = _phieu_da_noi(doc)
		_dung_dong_tai_cho(doc, g)
		loi = _noi_lai(doc, phieu)
		cau = (
			"Dòng hàng của tờ này vừa bị sửa lệch khỏi hoá đơn điện tử %s/%s, "
			"là số nhà cung cấp đã gửi cơ quan thuế, nên hệ thống dựng lại "
			"đúng bản gốc trong lần lưu này."
			% (g.get("ky_hieu") or "", g.get("so_hd") or "")
		)
		if phieu and not loi:
			cau += " Phiếu nhập %s vẫn được nối như vừa chọn." % ", ".join(phieu)
		elif loi:
			cau += " Riêng phần nối phiếu nhập chưa xong: " + " ".join(loi)
		frappe.msgprint(cau, title="Giữ đúng số hoá đơn điện tử", indicator="orange")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: dong bo luc luu")


def tk_theo_mon(doc, method=None):
	"""Hook validate: tờ máy dựng thì tài khoản chi phí đi theo khai báo Món.

	Ca thật 26/08/2026: 12 dòng hoá đơn tiếp khách Avanti rơi cả vào 632
	giá vốn hàng bán, trong khi chị Dung chốt tiếp khách ăn uống đi 64183.
	Khai tài khoản một lần trên danh mục Món, mọi tờ sau tự vào đúng chỗ.

	Chỉ đụng dòng DỊCH VỤ (món không quản kho) và chưa nối phiếu nhập, để
	không dẫm lên luật tài khoản chờ 3311 của hàng nhập kho - vụ 21/08 chết
	nhập kho vẫn còn đó, đọc đầu tệp ke_toan_mua.py trước khi nới rộng.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		if not (doc.get("custom_minvoice_id") or "").strip():
			return
		for d in doc.get("items") or []:
			ma = (d.get("item_code") or "").strip()
			if not ma or (d.get("purchase_receipt") or "").strip():
				continue
			if cint(frappe.db.get_value("Item", ma, "is_stock_item")):
				continue
			tk = frappe.db.get_value(
				"Item Default", {"parent": ma, "company": doc.company}, "expense_account"
			)
			if tk and d.get("expense_account") != tk:
				d.expense_account = tk
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: tk theo mon")


@frappe.whitelist()
def soat(gioi_han=300):
	"""CHỈ ĐỌC: những hoá đơn mua sinh từ hoá đơn điện tử đang lệch tổng.

	Tách riêng phần ĐÃ GHI SỔ: mấy tờ đó không tự sửa được nữa, chỉ liệt kê
	cho anh Việt xem (điều 11, không đề xuất sửa dữ liệu quá khứ).
	"""
	_kiem_quyen()
	ds = frappe.get_all(
		PI,
		filters={"custom_minvoice_id": ["is", "set"], "docstatus": ["<", 2]},
		fields=["name", "supplier_name", "posting_date", "bill_no", "docstatus",
			"base_grand_total", "custom_minvoice_id"],
		order_by="posting_date desc",
		limit_page_length=0,
	)
	if not ds:
		return {"nhap": [], "da_ghi_so": [], "so_nhap": 0, "so_da_ghi_so": 0}
	goc = {
		r["name"]: r
		for r in frappe.get_all(
			DT_HD,
			filters={"name": ["in", [x["custom_minvoice_id"] for x in ds]]},
			fields=["name", "tong_tien", "so_hd", "ky_hieu"],
			limit_page_length=0,
		)
	}
	nhap, xong = [], []
	for r in ds:
		g = goc.get(r["custom_minvoice_id"])
		if not g or not flt(g["tong_tien"]):
			continue
		viec, so = huong_lech(r["base_grand_total"], g["tong_tien"])
		if viec == "khop":
			continue
		mot = {
			"name": r["name"],
			"ncc": r["supplier_name"],
			"ngay": str(r["posting_date"] or ""),
			"so_hddt": "%s/%s" % (g.get("ky_hieu") or "", g.get("so_hd") or ""),
			"tong_erp": flt(r["base_grand_total"]),
			"tong_hddt": flt(g["tong_tien"]),
			"viec": viec,
			"lech": so,
		}
		(xong if cint(r["docstatus"]) == 1 else nhap).append(mot)
	nhap.sort(key=lambda x: -x["lech"])
	xong.sort(key=lambda x: -x["lech"])
	# Dem luon so to sai DON VI. Tien dung ma don vi sai van la sai, va
	# nguoi mo man ra phai thay ca hai con so cung mot luc chu khong phai
	# tim o hai cho (27/08/2026).
	try:
		dv = soat_don_vi(gioi_han=1)
		so_lech_dvt, so_dong_lech_dvt = dv.get("so_to", 0), dv.get("so_dong", 0)
		so_to_dv = dv.get("so_to_dich_vu", 0)
	except Exception:
		so_lech_dvt, so_dong_lech_dvt, so_to_dv = 0, 0, 0
	return {
		"nhap": nhap[: max(1, cint(gioi_han) or 300)],
		"da_ghi_so": xong,
		"so_nhap": len(nhap),
		"so_da_ghi_so": len(xong),
		"so_lech_don_vi": so_lech_dvt,
		"so_dong_lech_don_vi": so_dong_lech_dvt,
		# Dem rieng, KHONG cong vao con so canh bao phia tren: day la dong
		# dich vu chua anh xa vao Mon, khong phai lech don vi.
		"so_to_dich_vu_chua_anh_xa": so_to_dv,
		"nguong": NGUONG,
	}


@frappe.whitelist()
def soat_don_vi(gioi_han=300):
	"""CHI DOC: to nao TIEN DUNG ma DON VI sai, nhip ra cu khong thay.

	VI SAO PHAI CO, ca that 27/08/2026
	--------------------------------------------------------------------
	HDM-26-08-00115: nha cung cap ghi "Gói", Mon chua khai nen may lang le
	ha ve Gram he so 1. Tong to van dung 1.575.000 nen `soat` phia tren -
	no chi so TIEN - bao la khop va bo qua. Nhung so luong la 4,5 gram
	trong khi hang ve kho la 4.500 gram. Noi vao la hong gia von.

	Nghia la mot to co the "khop tien" ma van sai mot nghin lan. Tien khong
	phai la toan bo su that, don vi cung phai soi.

	Doc dau van tay ngay tren dong chung tu chu khong mo lai tung ban hoa
	don goc: `_dong_pi` da ghi don vi cua nha cung cap vao phan mo ta, va
	`dvt_mua.dvt_tren_hoa_don` doc lai duoc. Nho vay quet 3.000 to van nhe.
	"""
	_kiem_quyen()
	from vagabond import dvt_mua
	from vagabond import minvoice_chung_tu as mc

	# frappe.db.get_all chu khong frappe.get_all: doc thang bang con thi lop
	# kiem quyen cua get_all doi them tham so `parent`, ma tham so do chi co
	# o tang API chu khong co trong DatabaseQuery. Ban v328 truyen tham so do
	# vao nen nem TypeError ngay lan goi dau tren site that (27/08/2026).
	# Quyen da kiem o `_kiem_quyen` phia tren roi.
	dong = frappe.db.get_all(
		PI + " Item",
		filters={"docstatus": ["<", 2]},
		fields=["parent", "idx", "item_code", "item_name", "qty", "uom",
			"conversion_factor", "stock_uom", "description"],
		order_by="parent desc",
		limit_page_length=0,
	)
	if not dong:
		return {"dong": [], "so_dong": 0, "so_to": 0, "so_dong_dich_vu": 0, "so_to_dich_vu": 0, "dong_dich_vu": []}
	nghi = []
	for d in dong:
		dvt_ncc = dvt_mua.dvt_tren_hoa_don(d.get("description"))
		if not mc.don_vi_chua_khai(dvt_ncc, d.get("uom"), d.get("conversion_factor")):
			continue
		nghi.append(d)
	if not nghi:
		return {"dong": [], "so_dong": 0, "so_to": 0, "so_dong_dich_vu": 0, "so_to_dich_vu": 0, "dong_dich_vu": []}

	ten_to = sorted({d["parent"] for d in nghi})
	to = {
		r["name"]: r
		for r in frappe.get_all(
			PI,
			filters={"name": ["in", ten_to], "custom_minvoice_id": ["is", "set"]},
			fields=["name", "supplier_name", "posting_date", "bill_no", "docstatus"],
			limit_page_length=0,
		)
	}
	ra = []
	for d in nghi:
		t = to.get(d["parent"])
		if not t:
			continue
		ra.append({
			"name": d["parent"],
			"ncc": t["supplier_name"],
			"ngay": str(t["posting_date"] or ""),
			"so_hd": t["bill_no"],
			"da_ghi_so": cint(t["docstatus"]) == 1,
			"idx": d["idx"],
			"item_code": d["item_code"],
			"item_name": d["item_name"],
			"sl": flt(d["qty"]),
			"dvt_dang_dung": d.get("uom") or "",
			"dvt_ncc": dvt_mua.dvt_tren_hoa_don(d.get("description")),
			"dvt_kho": d.get("stock_uom") or "",
		})
	ra.sort(key=lambda x: (0 if not x["da_ghi_so"] else 1, x["name"]))

	# TACH HAI LOAI. Dong khong tra ra ma hang la dong dich vu ("Chuyen",
	# "Phieu", "Dich vu chiu thue"...). Chung khong co don vi kho de doi
	# chieu nen khong phai lech that, dem chung vao la thoi phong con so.
	#
	# Ngay 27/08/2026 con so dua ra man hinh la 1.185 to trong khi lech
	# that chi 505 to. Anh Viet noi dung: canh bao nhieu nhu vay thi vai
	# hom la khong ai nhin nua. Nen `so_to` va `so_dong` tu day CHI dem
	# dong co ma hang. Phan dich vu van tra ve nhung dem rieng.
	that = [x for x in ra if not dvt_mua.dong_dich_vu(x.get("item_code"))]
	dich_vu = [x for x in ra if dvt_mua.dong_dich_vu(x.get("item_code"))]
	return {
		"dong": that[: max(1, cint(gioi_han) or 300)],
		"so_dong": len(that),
		"so_to": len({x["name"] for x in that}),
		"so_dong_dich_vu": len(dich_vu),
		"so_to_dich_vu": len({x["name"] for x in dich_vu}),
		"dong_dich_vu": dich_vu[: max(1, cint(gioi_han) or 300)],
	}


@frappe.whitelist()
def dung_lai(name):
	"""Dựng lại dòng hàng của một hoá đơn NHÁP theo hoá đơn điện tử gốc.

	Chỉ đụng bảng dòng hàng. Nhà cung cấp, ngày, số hoá đơn, dòng thuế đều
	giữ nguyên - chúng vốn đã lấy từ hoá đơn điện tử.

	Phiếu đã ghi sổ thì TỪ CHỐI - tờ đã vào sổ đi đường `sua_to_da_ghi_so`,
	có kiểm phiếu chi và đi qua đủ cửa khoá sổ.

    Tệp này gọi các hàm nội bộ của `minvoice_chung_tu` để tra mã hàng và
    dựng dòng, cốt để hai đường dựng chứng từ không bao giờ ra hai kết quả
    khác nhau. Đổi chữ ký các hàm đó thì ca kiểm `thu_dung_lai_hddt` đỏ
    ngay, đừng bỏ qua.
	"""
	_kiem_quyen()
	doc = frappe.get_doc(PI, name)
	if cint(doc.docstatus) != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ rồi, không dựng lại kiểu này được. Tờ đã "
			"ghi sổ mà lệch thì báo anh Việt và chị Dung." % name
		)
	g = _goc(doc.get("custom_minvoice_id"))
	if not g:
		frappe.throw(
			"Hoá đơn %s không phải sinh từ hoá đơn điện tử nên không có bản gốc "
			"để dựng lại." % name
		)
	nen, vi_sao = dung_lai_co_loi_khong(doc, g)
	if not nen:
		frappe.throw(
			"Chưa dựng lại được tờ %s: %s. Hệ thống không ghi đè khi chưa chắc "
			"ra đúng số. Nhờ kế toán đối chiếu tay với bản hoá đơn điện tử."
			% (name, vi_sao)
		)
	phieu = _phieu_da_noi(doc)
	truoc = flt(doc.base_grand_total)
	_dung_dong_tai_cho(doc, g)
	loi_noi = _noi_lai(doc, phieu)
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	sau = flt(doc.base_grand_total)
	con_lech, _ = huong_lech(sau, g.get("tong_tien"))
	loi_nhan = (
		"Đã dựng lại %d dòng theo hoá đơn điện tử. Tổng %s đồng, khớp bản gốc."
		% (len(doc.items), _so(sau))
		if con_lech == "khop"
		else "Đã dựng lại %d dòng nhưng tổng %s đồng vẫn chưa khớp bản gốc %s đồng. "
		"Nhờ kế toán xem lại, đừng ghi sổ." % (len(doc.items), _so(sau), _so(g.get("tong_tien")))
	)
	if loi_noi:
		loi_nhan += " Phần nối phiếu nhập chưa xong: " + " ".join(loi_noi)
	return {
		"name": doc.name,
		"truoc": truoc,
		"sau": sau,
		"goc": flt(g.get("tong_tien")),
		"so_dong": len(doc.items),
		"khop": 1 if con_lech == "khop" else 0,
		"loi_nhan": loi_nhan,
	}


@frappe.whitelist()
def dung_lai_tat_ca(gioi_han=40):
	"""Dựng lại HÀNG LOẠT các tờ nháp đang lệch với hoá đơn điện tử gốc.

	Anh Việt cấp quyền 26/08/2026: 338 tờ nháp lệch là hậu quả của lỗi hệ
	thống, không được bắt Uyên ngồi bấm 338 lần. Chạy theo lô nhỏ, mỗi tờ
	tự chịu lỗi của mình - một tờ hỏng không được chặn các tờ còn lại.
	"""
	_quyen_manh()
	kq = soat(gioi_han=100000)
	ds = kq["nhap"][: max(1, cint(gioi_han) or 40)]
	khop, bo_qua, hong = [], [], []
	for r in ds:
		try:
			doc = frappe.get_doc(PI, r["name"])
			g = _goc(doc.get("custom_minvoice_id"))
			if not g:
				hong.append({"name": r["name"], "vi_sao": "mất bản hoá đơn điện tử gốc"})
				continue
			# Dựng thử TRƯỚC. Không chắc ra đúng thì bỏ qua, tuyệt đối không
			# ghi đè - đây là chốt thêm sau sự cố 27/08/2026 do bản v319 gây.
			nen, vi_sao = dung_lai_co_loi_khong(doc, g)
			if not nen:
				bo_qua.append({"name": r["name"], "vi_sao": vi_sao})
				continue
			phieu = _phieu_da_noi(doc)
			_dung_dong_tai_cho(doc, g)
			_noi_lai(doc, phieu)
			doc.flags.ignore_permissions = True
			doc.save()
			viec, _lech = huong_lech(doc.base_grand_total, g.get("tong_tien"))
			if viec != "khop":
				# Lưu xong mà vẫn lệch thì trả tờ về nguyên trạng.
				frappe.db.rollback()
				bo_qua.append({"name": r["name"], "vi_sao": "lưu xong vẫn lệch, đã trả về nguyên trạng"})
				continue
			frappe.db.commit()
			khop.append(doc.name)
		except Exception as e:
			frappe.db.rollback()
			hong.append({"name": r["name"], "vi_sao": str(e)[:160]})
	con_lai = max(0, kq["so_nhap"] - len(ds))
	return {
		"khop": len(khop),
		"bo_qua": bo_qua,
		"hong": hong,
		"con_lai": con_lai,
		"loi_nhan": "Dựng lại %d tờ khớp bản gốc, %d tờ để nguyên vì chưa chắc đúng, "
			"%d tờ lỗi, còn %d tờ chưa chạy."
			% (len(khop), len(bo_qua), len(hong), con_lai),
	}


@frappe.whitelist()
def dung_lai_lech_don_vi(gioi_han=40):
	"""Dung lai HANG LOAT cac to NHAP dang lech DON VI (tien van dung).

	Khac `dung_lai_tat_ca`: ham kia lay danh sach tu `soat` - tuc la nhung
	to lech TIEN. Nhom 505 to nay tien dung tuyet doi nen ham kia khong
	bao gio dung toi. Phai co duong rieng.

	Anh Viet cho phep 27/08/2026: toan bo la to nhap, khong cham so sach,
	khong cham hoa don da gui co quan thue.

	KHONG SUA TAY SO LUONG. Chi dung lai dong hang tu ban hoa don dien tu
	goc. Neu Mon da khai don vi cua nha cung cap thi lan dung lai nay tra
	ra dung don vi va dung he so; neu Mon chua khai thi ket qua khong doi
	gi ca - to do van nam lai trong danh sach cho Uyen khai don vi. Chay
	lai bao nhieu lan cung ra mot ket qua.

	Hang rao giu nguyen nhu ham anh em: dung thu truoc, luu xong ma tong
	lech la tra to ve nguyen trang.
	"""
	_quyen_manh()
	dv = soat_don_vi(gioi_han=100000)
	ten_to = []
	for d in dv.get("dong") or []:
		if d.get("da_ghi_so"):
			continue
		if d["name"] not in ten_to:
			ten_to.append(d["name"])
	ds = ten_to[: max(1, cint(gioi_han) or 40)]

	sua, khong_doi, bo_qua, hong = [], [], [], []
	for ten in ds:
		try:
			doc = frappe.get_doc(PI, ten)
			if cint(doc.docstatus) != 0:
				bo_qua.append({"name": ten, "vi_sao": "đã ghi sổ"})
				continue
			g = _goc(doc.get("custom_minvoice_id"))
			if not g:
				hong.append({"name": ten, "vi_sao": "mất bản hoá đơn điện tử gốc"})
				continue
			nen, vi_sao = dung_lai_co_loi_khong(doc, g)
			if not nen:
				bo_qua.append({"name": ten, "vi_sao": vi_sao})
				continue
			truoc = _van_tay_don_vi(doc)
			tong_truoc = flt(doc.base_grand_total)
			phieu = _phieu_da_noi(doc)
			_dung_dong_tai_cho(doc, g)
			_noi_lai(doc, phieu)
			doc.flags.ignore_permissions = True
			doc.save()
			viec, _l = huong_lech(doc.base_grand_total, g.get("tong_tien"))
			if viec != "khop":
				frappe.db.rollback()
				bo_qua.append({
					"name": ten,
					"vi_sao": "dựng lại xong tổng lại lệch, đã trả về nguyên trạng",
				})
				continue
			sau = _van_tay_don_vi(doc)
			frappe.db.commit()
			mot = {
				"name": ten,
				"ncc": doc.get("supplier_name") or doc.get("supplier"),
				"ngay": str(doc.get("posting_date") or ""),
				"so_hd": doc.get("bill_no") or "",
				"tong": tong_truoc,
				"truoc": truoc,
				"sau": sau,
			}
			(sua if sau != truoc else khong_doi).append(mot)
		except Exception as e:
			frappe.db.rollback()
			hong.append({"name": ten, "vi_sao": str(e)[:160]})

	con_lai = max(0, len(ten_to) - len(ds))
	return {
		"so_sua": len(sua),
		"so_khong_doi": len(khong_doi),
		"sua": sua,
		"khong_doi": khong_doi,
		"bo_qua": bo_qua,
		"hong": hong,
		"con_lai": con_lai,
		"loi_nhan": "Dựng lại %d tờ đổi được đơn vị, %d tờ dựng lại nhưng chưa đổi "
			"được vì món chưa khai đơn vị, %d tờ để nguyên, %d tờ lỗi, còn %d tờ "
			"chưa chạy."
			% (len(sua), len(khong_doi), len(bo_qua), len(hong), con_lai),
	}


def _van_tay_don_vi(doc):
	"""Dau van tay don vi cua ca to, de so truoc va sau khi dung lai."""
	return " | ".join(
		"%s:%g%s*%g" % (
			r.get("item_code") or "",
			flt(r.get("qty")),
			r.get("uom") or "",
			flt(r.get("conversion_factor")) or 1,
		)
		for r in (doc.get("items") or [])
	)


@frappe.whitelist()
def soat_do_tam(nguong=None):
	"""CHI DOC: mon nao dang bi dung lam cho do tam cho nhieu thu khac nhau.

	Ca that 27/08/2026 (anh Viet xac nhan): mon NVLT00231 "Nuoc, ml" von la
	nuoc may de san xuat, khong theo doi ton kho, chi co don vi ml. Vay ma
	bang anh xa dang tro 18 ten hang cua nha cung cap vao no: nuoc da bao,
	nuoc suoi chai, nuoc sparkling, nuoc mam chay, ca "Che troi nuoc" va
	"nuoc tra bi dao" tren hoa don nha hang. Khop chi vi cung co chu "nuoc".

	Hau qua kep: gia von mon nuoc thanh vo nghia, va cac khoan tiep khach
	bi nhet vao nguyen vat lieu.

	Chi LIET KE, khong tu go anh xa nao - do la quyet dinh phan loai ke
	toan, dieu 11 khong cho tu sua du lieu cu.
	"""
	_kiem_quyen()
	from vagabond import dvt_mua

	ds = frappe.get_all(
		"MInvoice NCC Map",
		filters={"item_code": ["is", "set"]},
		fields=["name", "supplier_mst", "ma_ncc", "ten_ncc", "item_code"],
		limit_page_length=0,
	)
	theo_mon = {}
	for r in ds:
		theo_mon.setdefault(r["item_code"], []).append(r)

	nguong = cint(nguong) or dvt_mua.NGUONG_DO_TAM
	ra = []
	for ma, rows in theo_mon.items():
		ten_khac_nhau = {str(r.get("ten_ncc") or "").strip().lower() for r in rows}
		ten_khac_nhau.discard("")
		if not dvt_mua.dang_do_tam(ma, len(ten_khac_nhau), nguong):
			continue
		mon = frappe.db.get_value(
			"Item", ma, ["item_name", "stock_uom", "is_stock_item"], as_dict=True
		) or {}
		ra.append({
			"item_code": ma,
			"item_name": mon.get("item_name") or "",
			"dvt_kho": mon.get("stock_uom") or "",
			"theo_doi_ton": cint(mon.get("is_stock_item")) == 1,
			"so_ten_ncc": len(ten_khac_nhau),
			"ten_ncc": sorted(
				{str(r.get("ten_ncc") or "").strip() for r in rows if r.get("ten_ncc")}
			),
		})
	ra.sort(key=lambda x: -x["so_ten_ncc"])
	return {"mon": ra, "so_mon": len(ra), "nguong": nguong}


@frappe.whitelist()
def sua_to_da_ghi_so(name):
	"""Sửa một tờ ĐÃ GHI SỔ đang lệch: huỷ, lập bản sửa đổi đúng theo hoá
	đơn điện tử, ghi sổ lại.

	Anh Việt cấp toàn quyền 26/08/2026 cho các tờ đã ghi sổ mà lệch. Vẫn
	giữ hai chốt, cố ý:

	  * Tờ đã có phiếu chi trỏ vào thì TỪ CHỐI, kể tên phiếu chi ra. Tự gỡ
	    phiếu chi là đụng vào tiền đã trả, việc đó của kế toán.
	  * Mọi cửa khoá sổ vẫn chạy như thường. Kỳ đã khoá thì lệnh này tự
	    thất bại chứ không lách.
	"""
	_quyen_manh()
	doc = frappe.get_doc(PI, name)
	if cint(doc.docstatus) != 1:
		frappe.throw("Tờ %s không ở trạng thái đã ghi sổ." % name)
	g = _goc(doc.get("custom_minvoice_id"))
	if not g:
		frappe.throw("Tờ %s không sinh từ hoá đơn điện tử nên không có bản gốc." % name)
	tien = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": PI, "reference_name": name, "docstatus": 1},
		fields=["parent"],
		limit_page_length=20,
	)
	if tien:
		frappe.throw(
			"Tờ %s đã có phiếu chi %s trỏ vào. Phải gỡ phiếu chi trước rồi mới "
			"sửa được, việc đó để kế toán quyết."
			% (name, ", ".join(sorted({t["parent"] for t in tien})))
		)
	nen, vi_sao = dung_lai_co_loi_khong(doc, g)
	if not nen:
		frappe.throw(
			"Chưa sửa được tờ %s: %s. Không huỷ một tờ đã ghi sổ khi chưa chắc "
			"dựng lại ra đúng số." % (name, vi_sao)
		)
	truoc = flt(doc.base_grand_total)
	doc.flags.ignore_permissions = True
	doc.cancel()

	moi = frappe.copy_doc(doc)
	moi.amended_from = name
	moi.docstatus = 0
	_dung_dong_tai_cho(moi, g)
	moi.flags.ignore_permissions = True
	moi.insert(ignore_permissions=True)
	moi.submit()
	frappe.db.commit()
	return {
		"cu": name,
		"moi": moi.name,
		"truoc": truoc,
		"sau": flt(moi.base_grand_total),
		"goc": flt(g.get("tong_tien")),
		"loi_nhan": "Đã huỷ %s, ghi sổ bản sửa %s, tổng %s đồng khớp hoá đơn điện tử."
			% (name, moi.name, _so(moi.base_grand_total)),
	}

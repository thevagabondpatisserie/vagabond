# -*- coding: utf-8 -*-
"""Hoá đơn điện tử thành chứng từ trong sổ: soi chỗ sót và dựng lại cho đúng.

Bài anh Việt giao 26/08/2026, sau khi bên Uyên báo: "ngày 4/8 Ngon Cổ Điển
xuất 3 HĐ, next lấy về có 2 HĐ thôi ạ".

Đúng là sót. Tờ giữa, số 50845, 6.868.800 đ, nằm nguyên trong bảng hoá đơn
điện tử nhưng không bao giờ thành Hoá đơn mua hàng.

QUÉT RỘNG RA THÌ KHÔNG PHẢI MỘT TỜ
-----------------------------------
Đếm ngày 26/08/2026 trên site thật, từ 25/07 tới 25/08:

    Nhóm A  22 hoá đơn ĐẦU VÀO    126.427.733 đ
            "Item Wise Tax Details do not match with Taxes and Charges"
    Nhóm B 103 hoá đơn ĐẦU RA      31.176.592 đ
            mã hàng trên hoá đơn không có trong danh mục Món

    Tổng   125 hoá đơn            157.604.325 đ

Cả 125 tờ đều đã bị đóng dấu `da_tao_chung_tu = 1`, tức là hệ tự nhận
"xong rồi", trong khi không có chứng từ nào được dựng. Lý do có ghi vào ô
`ly_do_bo_qua`, nhưng không có màn nào hiện ô đó ra, nên không ai đọc.

BA CÁI SAI, VÀ CẢ BA ĐỀU NẰM Ở CHỖ KHÁC NHAU
---------------------------------------------
1. SAI VỀ THUẾ (nhóm A).

   Tờ hoá đơn điện tử ghi MỘT con số thuế tổng, và đó là con số đã gửi cơ
   quan thuế. Khi dựng Hoá đơn mua hàng, ERPNext lại đi hỏi từng mã hàng
   xem "Mẫu thuế mặt hàng" của mày là bao nhiêu, cộng lại, rồi so với con
   số tổng kia. Lệch một đồng là nó ném lỗi và bỏ cả tờ.

   Mà lệch là chuyện đương nhiên: mẫu thuế trên danh mục Món là dự đoán
   cho tương lai, còn con số trên hoá đơn là sự thật đã xảy ra. Hàng mua
   tháng này 8% mà danh mục ghi 10% thì không bao giờ khớp.

   Cách gỡ: XOÁ mẫu thuế mặt hàng khỏi từng dòng của chứng từ sinh ra, để
   con số thuế của hoá đơn điện tử là nguồn sự thật duy nhất. Đã dò mã
   nguồn ERPNext v16 (`controllers/taxes_and_totals.py`): phép kiểm đó bỏ
   qua dòng thuế dạng "Actual" khi thuế suất từng dòng bằng 0, nên xoá
   mẫu thuế là đủ, không phải vá gì thêm.

2. SAI VỀ CÁCH BỎ CUỘC (cả hai nhóm).

   Dựng hỏng thì hệ vẫn đóng dấu `da_tao_chung_tu = 1`. Đóng dấu là lời
   hứa "cái này xong rồi", mà lời hứa đó sai. Tờ hỏng biến mất khỏi mọi
   danh sách, và chỉ lộ ra khi có người ngồi dò tay như bên Uyên vừa làm.

   Cách gỡ: hỏng thì KHÔNG đóng dấu. Ghi lý do, đếm số lần đã thử, và để
   nguyên trạng thái chưa xong. Hàng đợi xếp theo số lần thử tăng dần nên
   tờ hỏng đi xuống cuối, không chiếm chỗ của tờ mới, nhưng vẫn nằm trong
   danh sách và vẫn đếm được.

3. KHÔNG CÓ CHỖ NÀO NHÌN THẤY (cả hai nhóm).

   Cửa `con_sot` ở dưới liệt kê thẳng những tờ chưa thành chứng từ, gom
   theo lý do, kèm tổng tiền. Chỉ đọc.

HOÁ ĐƠN ĐẦU RA KHÔNG PHẢI VIỆC CỦA MÔ ĐUN NÀY
----------------------------------------------
Anh Việt chốt 26/08/2026: "Nhóm B không đụng vào nữa, cái đó bên Fabi đang
xuất hoá đơn."

Nhóm B là 103 tờ đầu ra bán lẻ, mã hàng là mã của máy bán hàng ngoài quầy
(BAEN00012 "Bánh Khúc"...), không có trong danh mục Món của hệ. Chúng do
Fabi xuất, sổ sách bên đó đã ghi.

Nên hoá đơn đầu ra nào KHÔNG có chứng từ trong hệ thì đánh dấu BỎ QUA HỢP
LỆ kèm lý do, chứ không nằm mãi trong danh sách còn sót. Để chúng trong
danh sách là 103 dòng báo động giả, mà một danh sách kêu oan thì y hệt một
danh sách không ai đọc: đúng cái bẫy đã làm 22 tờ đầu vào nằm im cả tháng.

Hoá đơn đầu ra do CHÍNH HỆ xuất thì khác: chúng đã có `custom_minvoice_id`
trỏ về, nên `_da_co_chung_tu` nhận ra và không rơi vào nhánh này.

BA HÀNG RÀO NỮA, ĐỂ KHÔNG BAO GIỜ LẶP LẠI
------------------------------------------
1. DỰNG XONG PHẢI ĐỐI CHIẾU TỔNG. Chứng từ sinh ra mà tổng tiền lệch hoá
   đơn điện tử quá một đồng thì HUỶ CẢ LƯỢT GHI của tờ đó và ghi lý do.
   Sai lặng lẽ còn tệ hơn không dựng: không dựng thì còn đếm được.

2. KHÔNG BÓ HẸP CỬA SỔ NGÀY. Bản cũ chỉ quét 60 ngày gần nhất, tờ cũ hơn
   thì vĩnh viễn không ai dựng. Nay mặc định quét từ đầu, và xếp hàng đợi
   theo số lần thử nên tờ hỏng vẫn không chiếm chỗ.

3. CHẶN TRÙNG THEO SỐ HOÁ ĐƠN. Kế toán có thể đã gõ tay một tờ mà không
   gắn mã hoá đơn điện tử. Dựng thêm là hai chứng từ cho một tờ hoá đơn.
   Gặp thì DỪNG và báo, không tự gắn vào chứng từ của người khác.
"""

import json
import unicodedata

# ------------------------------------------------------------ phần thuần
#
# Đặt trên `import frappe` để bộ kiểm thử tầng khung chạy được ở CI mà
# không cần site. Ca kiểm ở khung/kiem_thu/thu_minvoice_chung_tu.py.

DT_HD = "MInvoice Invoice"
PI = "Purchase Invoice"
SI = "Sales Invoice"

LOAI_VAO = "Đầu vào"
LOAI_RA = "Đầu ra"

# Trạng thái mà hoá đơn KHÔNG cần thành chứng từ nữa.
TT_KHOI_DUNG = ("Bị thay thế", "Đã huỷ")

# Chuông báo tắc nhịp gửi về hộp thư kế toán, vì việc phải làm khi nghe
# chuông là việc của kế toán chứ không phải của người viết mã.
EMAIL_KE_TOAN = "account@thevagabondpatisserie.com"

# Chênh DƯỚI bao nhiêu đồng thì coi như khớp, khỏi nắn.
#
# Đọc kỹ chữ DƯỚI. Ngưỡng này là ngưỡng HỞ: chênh đúng một đồng là PHẢI
# nắn, chỉ phần lẻ nhỏ hơn một đồng mới được bỏ qua.
#
# Vì sao khác `mua_dich_vu.NGUONG_LECH`, cũng 1.0 nhưng là ngưỡng ĐÓNG
# (lệch một đồng vẫn cho qua): hai chỗ làm hai việc khác nhau.
#
#   * Cổng chặn ghi sổ soi một tờ ĐÃ CÓ, có thể do người gõ tay hoặc có
#     từ đời nào, nên nới một đồng để đừng chặn oan.
#   * Chỗ này thì đang TỰ DỰNG tờ ra, và hai vế đem so đều đã là số nguyên
#     đồng máy sẽ ghi (xem `tien_dong_may_ghi`). Chênh một đồng ở đây không
#     bao giờ là nhiễu, nó là một đồng thiếu thật và nắn được.
#
# Ca thật ALOIN số 1144 ngày 16/09/2026: 260 x 1.576,92, máy ghi 409.999,
# hoá đơn ghi 410.000. Ngưỡng cũ là ngưỡng đóng nên phép nắn bảo "khớp",
# và HDM-26-09-00040 vào sổ thiếu đúng một đồng.
NGUONG_KHOP = 1.0


def tinh_chat_dong(d):
	"""#227: tchat=3 là khoản giảm, 4 là ghi chú, không phải mặt hàng.

	Một số nguồn chỉ giữ nhãn tiếng Việt thay mã số. Chỉ nhận nhãn rõ
	ràng, không dò chữ 'giảm' trong tên món để đoán chiết khấu.
	"""
	tc = str(d.get("tchat") or "").strip()
	if tc:
		return tc[:-2] if tc.endswith(".0") else tc
	ten = " ".join(str(d.get("ten") or "").lower().split())
	ten = "".join(c for c in unicodedata.normalize("NFD", ten) if unicodedata.category(c) != "Mn")
	if ten == "chiet khau" or ten.startswith("chiet khau thuong mai"):
		return "3"
	return tc


def dong_hang_hoa(ds):
	"""Dùng chung cho lần kéo đầu, dựng lại, ghim số và học ánh xạ."""
	return [d for d in ds if tinh_chat_dong(d) not in ("3", "4")]


def nan_dau_dong(sl, gia, thtien=None):
	"""Dua mot dong ve dang ERPNext nhan duoc: don gia KHONG AM. THUAN.

	Hoa don dieu chinh giam va hoa don thay the ghi so am. Nghi dinh
	70/2025 cho phep ghi dau tru, va nha phat hanh moi noi ghi mot kieu:
	co noi de so luong am va don gia duong, co noi de CA HAI cung am.

	Ca hai cung am la cai bay: am nhan am ra duong, nen mot to hoan tien
	56 trieu di vao so thanh mot to MUA 56 trieu, tien di nguoc chieu ma
	khong lop nao keu. Da gap dung ca nay voi to hoan tien cua Grab.

	Quy uoc cua ERPNext cho chung tu tra hang: don gia luon duong, dau am
	nam o SO LUONG. Nen o day gom het dau ve mot cho:

	    dau lay theo thanh tien khi co, khong thi lay theo tich so luong
	    nhan don gia; don gia tra ve luon la tri tuyet doi.

	Tra ve cap (so luong, don gia).
	"""
	try:
		sl = float(sl or 0)
	except (TypeError, ValueError):
		sl = 0.0
	try:
		gia = float(gia or 0)
	except (TypeError, ValueError):
		gia = 0.0
	try:
		tt = float(thtien) if thtien not in (None, "") else None
	except (TypeError, ValueError):
		tt = None

	if tt is not None and tt != 0:
		am = tt < 0
	else:
		am = (sl * gia) < 0 or (sl * gia == 0 and (sl < 0 or gia < 0))

	gia = abs(gia)
	sl = -abs(sl) if am else abs(sl)
	return (sl, gia)


def dong_tu_hoa_don(it, dau_to=1):
	"""Một dòng hàng của hoá đơn điện tử thành số liệu dùng được. THUẦN.

	Ô đơn giá TRỐNG là chuyện thật: hoá đơn tiền điện, tiền nước, phí dịch
	vụ đều chỉ có thành tiền. Gặp thì đặt số lượng về 1 và lấy thành tiền
	làm đơn giá, như vậy tổng luôn khớp tuyệt đối.

	Bản cũ giữ nguyên số lượng rồi vẫn lấy thành tiền làm đơn giá, nên
	thành tiền bị nhân lên bằng số lượng lần. Một hoá đơn điện 53 triệu
	từng thành 814 tỷ vì lỗi này.

	Ô đơn giá ghi SỐ KHÔNG cũng phải xử như trống - ca thật 27/08/2026
	--------------------------------------------------------------------
	Hoá đơn tiếp khách Avanti C26TAV/5019 có dòng "Phí phục vụ" ghi
	sluong 0, dgia 0, thtien 1.283.500. Bản cũ chỉ bắt trường hợp dgia là
	None nên dòng đó vào chứng từ với đơn giá 0. Mà đơn giá 0 thì ERPNext
	tự điền lại theo Bảng giá nhập của mặt hàng, ở đây là 4.500.000, làm tờ
	hoá đơn phình thêm đúng 4,5 triệu.

	Nên: đơn giá trống HOẶC bằng không, mà có thành tiền, thì lấy thành
	tiền làm đơn giá và đặt số lượng về 1. Không bao giờ để một dòng đi vào
	chứng từ với đơn giá 0 trong khi hoá đơn có tiền.

	`dau_to` là dấu của cả tờ, lấy từ tổng tiền. Tờ dương thì giữ nguyên
	mọi thứ như cũ, kể cả dòng chiết khấu ghi số âm. Tờ ÂM thì gom hết dấu
	về ô số lượng, xem `nan_dau_dong`.
	"""
	d = it or {}
	sl = d.get("sluong") or 1
	gia = d.get("dgia")
	if not gia and d.get("thtien"):
		gia = d.get("thtien")
		sl = 1
	elif gia is None:
		gia = 0
	if int(dau_to or 1) < 0:
		sl, gia = nan_dau_dong(sl, gia, d.get("thtien"))
		# Dòng KHÔNG TIỀN trên tờ âm (mô tả không qty, hàng tặng giá 0 dù
		# nguồn ghi qty âm hay DƯƠNG) phải mang qty âm: ERPNext chặn phiếu trả
		# hàng có dòng qty dương ("số lượng phải là số âm"). Tiền dòng vẫn 0
		# nên tổng tờ không đổi. Không đảo dòng CÓ tiền (tiền dương hỗn hợp
		# giữ nguyên dấu theo nan_dau_dong). Claude #352: bản trước chỉ bắt
		# dòng không qty, dòng quà qty dương giá 0 vẫn dương và tờ hỏng.
		if not gia and not d.get("thtien"):
			sl = -abs(sl)
	return {
		"ma": str(d.get("mhhdvu") or "").strip(),
		"ten": str(d.get("ten") or "").strip(),
		"dvt": d.get("dvtinh"),
		"sl": sl,
		"gia": gia,
		"tien": (sl or 0) * (gia or 0),
	}


def dau_cua_to(tong_tien):
	"""To nay la to am hay to duong. THUAN. Tra ve -1 hoac 1."""
	try:
		return -1 if float(tong_tien or 0) < 0 else 1
	except (TypeError, ValueError):
		return 1


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

	HÀM NÀY DỌN VỀ ĐÂY NGÀY 16/09/2026. Trước đó nó chỉ nằm ở
	`dung_lai_hddt`, nên đường DỰNG LẠI một tờ thì tính đúng phần làm tròn
	còn đường DỰNG MỚI ở `dung_hoa_don_mua` vẫn nhân thẳng `qty * rate`.
	Hai đường cùng một việc mà hai cách tính là cái bẫy đã đẻ ra tờ
	HDM-26-09-00040 thiếu một đồng. Nay chỉ còn MỘT nguồn.
	"""
	return flt(flt(sl, dp_sl) * flt(gia, dp_gia), dp_tien)


def ten_dong_bu(so_tien):
	"""Tên dòng bù cho phần chênh. THUẦN.

	Chênh vài đồng là do làm tròn, gọi đúng tên để kế toán khỏi đi tìm.
	"""
	return ("Chênh lệch làm tròn theo hoá đơn điện tử"
		if abs(flt(so_tien)) < 100 else "Phí khác theo hoá đơn")


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

	HÀM NÀY DỌN VỀ ĐÂY NGÀY 16/09/2026, cùng lý do với `tien_dong_may_ghi`:
	đường dựng mới vẫn neo thẳng vào `tien_truoc_thue` nên vẫn giữ nguyên
	cái bẫy mà đường dựng lại đã gỡ từ 27/08.
	"""
	tong = flt(g.get("tong_tien"))
	if tong:
		return tong - flt(g.get("tien_thue"))
	return flt(g.get("tien_truoc_thue"))


def do_chinh_xac(doc=None, g=None):
	"""Số lẻ (đơn giá, thành tiền, số lượng) mà TỜ NÀY sẽ thật sự dùng.

	HỎI ĐÚNG CHỖ MÁY SẼ HỎI - phát hiện của Codex trên PR #337
	--------------------------------------------------------------------
	Bản đầu của v502 lấy số lẻ chung của Hoá đơn mua (2, 0, 3). Sai, vì
	hook `do_chinh_xac_mua.truoc_khi_tinh` chạy ngay trong `insert` và
	nâng số lẻ của CHÍNH tờ đó lên đơn giá 9, số lượng 9, tiền lấy theo số
	lẻ của bản gốc. Đoán một đằng máy ghi một nẻo thì phép nắn tính ra một
	con số không có thật.

	Ca thật HĐ11595: 1000 x 925,9259, tiền hàng 925.926. Máy dùng đơn giá
	9 số lẻ nên ghi 925.926, đúng. Nhưng nếu đoán đơn giá 2 số lẻ thì ra
	925.930, phép nắn tưởng THỪA 4 đồng và đặt giảm giá 4 đồng, tờ thành
	hụt 4 đồng và hàng rào cuối chặn luôn, không dựng được tờ nào.

	Nên cả đường dựng mới lẫn đường dựng lại đều đi qua đây, và đây hỏi
	đúng `do_chinh_xac_mua.quy_uoc` - cùng một hàm mà hook sẽ hỏi. `doc`
	có thể chỉ là một dict mô tả tờ SẮP dựng, vì `quy_uoc` chỉ đọc
	`doctype` và `currency`.
	"""
	if doc is not None:
		from vagabond.do_chinh_xac_mua import quy_uoc

		qc = quy_uoc(doc, g)
		if qc:
			return qc["gia"], qc["tien"], qc["sl"]
	return do_chinh_xac_pi()


def do_chinh_xac_pi():
	"""Số lẻ CHUNG của Hoá đơn mua, khi tờ không có quy ước riêng."""
	try:
		gia = cint(frappe.get_precision(PI + " Item", "rate"))
		tien = cint(frappe.get_precision(PI + " Item", "amount"))
		sl = cint(frappe.get_precision(PI + " Item", "qty"))
	except Exception:
		gia, tien, sl = 0, 0, 0
	return (gia or 2), (tien or 2), (sl or 3)


def can_theo_truoc_thue(tong_dong, truoc_thue):
	"""So tổng dòng hàng với tiền trước thuế của hoá đơn. THUẦN.

	Trả về (viec, so_tien):
	    ("khop", 0)   không phải nắn gì
	    ("giam", x)   dòng hàng THỪA x đồng, ghi x vào ô Giảm giá
	    ("phi", x)    dòng hàng THIẾU x đồng, thêm một dòng phí x đồng

	Ba nguồn làm lệch: chiết khấu, giảm thuế theo nghị quyết, và các khoản
	phí (vé máy bay, phí dịch vụ) không nằm trong dòng hàng khi lên XML.

	NGƯỠNG LÀ NGƯỠNG HỞ - ca thật ALOIN số 1144 ngày 16/09/2026
	--------------------------------------------------------------------
	Trước bản này phép so là `> NGUONG_KHOP`, tức chênh đúng một đồng vẫn
	được gọi là khớp. Mà hai vế đem so ở đây đều đã là số nguyên đồng máy
	sẽ ghi, nên chênh một đồng không bao giờ là nhiễu làm tròn, nó là một
	đồng thiếu thật.

	Tờ C26TAA số 1144: 260 x 1.576,92. Máy chỉ giữ đơn giá hai số lẻ nên
	thành tiền ghi 409.999, hoá đơn ghi 410.000, chênh đúng -1,0. Phép nắn
	cũ bỏ qua, hàng rào cuối cũng bỏ qua, và HDM-26-09-00040 nằm trong sổ
	thiếu một đồng mà không lớp nào kêu.

	Nay `abs(chenh) < NGUONG_KHOP` mới là khớp. Phần lẻ nhỏ hơn một đồng
	vẫn được bỏ qua như cũ, vì đồng bạc không chia nhỏ hơn thế.
	"""
	chenh = float(tong_dong or 0) - float(truoc_thue or 0)
	if abs(chenh) < NGUONG_KHOP:
		return ("khop", 0)
	if chenh > 0:
		return ("giam", chenh)
	return ("phi", -chenh)


def cap_trung(hang):
	"""Gom những chứng từ cùng trỏ về MỘT tờ hoá đơn điện tử. THUẦN.

	`hang` là list dict có `ma_hddt` và `ten`. Trả list nhóm từ 2 tờ trở lên,
	tờ cũ nhất đứng đầu.

	VÌ SAO ĐẾM CÁI NÀY (31/08/2026)
	-------------------------------
	Hôm đó 31 tờ hoá đơn mua bị dựng hai lần vì hai lượt chạy chồng nhau.
	Khoá ở `_chay` chặn nguyên nhân đó rồi, nhưng chặn một nguyên nhân đã
	biết không bằng NHÌN THẤY được khi có nguyên nhân mới.

	Không ai phát hiện ra bằng máy cả: anh Việt nhìn màn danh sách thấy
	dòng nào cũng có một dòng y hệt bên dưới. Một cái đếm đơn giản như hàm
	này thì lượt quét đầu tiên đã kêu.
	"""
	theo_ma = {}
	for h in hang or []:
		ma = str((h or {}).get("ma_hddt") or "").strip()
		if not ma:
			continue
		theo_ma.setdefault(ma, []).append(h)
	ra = []
	for ma, ds in theo_ma.items():
		if len(ds) < 2:
			continue
		ra.append({
			"ma_hddt": ma,
			"so_to": len(ds),
			"ten": [str((x or {}).get("ten") or "") for x in ds],
		})
	ra.sort(key=lambda x: (-x["so_to"], x["ma_hddt"]))
	return ra


def khoi_dung_duoc(trang_thai):
	"""Tờ này khỏi cần dựng chứng từ nữa. THUẦN."""
	return str(trang_thai or "").strip() in TT_KHOI_DUNG


def rut_gon_loi(loi):
	"""Câu lỗi rút gọn để cất vào ô lý do. THUẦN.

	Cắt thẻ HTML và xuống dòng: ô này hiện trong bảng, để nguyên thẻ br thì
	người đọc thấy chữ "<br>" giữa câu.
	"""
	s = str(loi or "").replace("<br>", " ").replace("\n", " ")
	while "  " in s:
		s = s.replace("  ", " ")
	return s.strip()[:400] or "Không dựng được chứng từ, chưa rõ nguyên nhân"


def gom_theo_ly_do(hang):
	"""Gom danh sách tờ sót theo lý do, đếm số tờ và cộng tiền. THUẦN."""
	bang = {}
	for h in hang or []:
		k = str((h or {}).get("ly_do") or "").strip() or "(không ghi lý do)"
		o = bang.setdefault(k, {"ly_do": k, "so_to": 0, "tien": 0.0, "loai": set()})
		o["so_to"] += 1
		o["tien"] += abs(float((h or {}).get("tong_tien") or 0))
		if h.get("loai"):
			o["loai"].add(h["loai"])
	ra = []
	for o in bang.values():
		o["loai"] = sorted(o["loai"])
		ra.append(o)
	return sorted(ra, key=lambda o: -o["tien"])


def dich_vu_khong_ghi_don_vi(dvt_ncc, la_hang_kho):
	"""Dòng DỊCH VỤ mà nhà cung cấp để trống đơn vị thì lấy đơn vị của Món,
	hệ số 1. THUẦN.

	Ca thật 22/09/2026: hoá đơn cước Mobifone (Món DVTI00002) không ghi đơn
	vị, và dựng phiếu mua bị chặn "chưa xác định được quy đổi đơn vị nhà
	cung cấp '(trống)'". Khai trong bảng quy đổi của Món cũng không được vì
	không có tên đơn vị nào để khai. Anh Việt duyệt 22/09/2026: dịch vụ
	không ghi đơn vị thì tính theo đơn vị của Món.

	CHỈ mở cho món KHÔNG quản lý tồn kho. Hàng tồn kho mà trống đơn vị vẫn
	bị chặn như cũ, vì đoán hệ số 1 ở đó là đổi một hộp thành một gram.
	Đơn vị ghi KHÁC trống (vd 'Lần') vẫn phải khai quy đổi như cũ."""
	return not str(dvt_ncc or "").strip() and not int(la_hang_kho or 0)


# Nhóm việc cho một tờ đầu vào chưa thành phiếu mua, theo thứ tự ưu tiên
# khi đọc lý do. Mỗi nhóm nói luôn ai làm gì.
NHOM_CHO_DUNG = (
	("thieu_nguon", "Chờ M-Invoice trả đủ nội dung"),
	("quy_cach", "Cần khai quy cách mua"),
	("trung", "Nghi trùng với phiếu đã có"),
	("dong_dau", "Đã đóng dấu xong mà chưa có phiếu"),
	("cho_luot", "Chờ lượt dựng"),
	("khac", "Cần xem lý do"),
)


def nhom_cho_dung(so_hd, ly_do, da_tao):
	"""Tờ đầu vào chưa thành phiếu mua đang cần xử lý kiểu gì. THUẦN.

	Trả (mã nhóm, tên nhóm). Đọc theo SỰ THẬT của bản ghi, không đoán."""
	ten = dict(NHOM_CHO_DUNG)
	ld = str(ly_do or "").lower()
	if not str(so_hd or "").strip():
		k = "thieu_nguon"
	elif "quy đổi đơn vị" in ld or "quy cách" in ld:
		k = "quy_cach"
	elif "cùng số hoá đơn" in ld or "cùng số hóa đơn" in ld or "trùng" in ld:
		k = "trung"
	elif not ld:
		k = "dong_dau" if int(da_tao or 0) else "cho_luot"
	else:
		k = "khac"
	return k, ten[k]


# ------------------------------------------------------- phần chạm hệ

import frappe  # noqa: E402
from frappe.utils import cint, flt, nowdate  # noqa: E402

from contextlib import ExitStack  # noqa: E402

# KHOA TEP, cung khuon voi ban_hang.py. May chu khong co thi lui ve khoa
# rong chu khong chan nghiep vu: mot lan dung to con hon ca ngay khong dung
# duoc to nao.
try:  # pragma: no cover
	from frappe.utils.synchronization import LockTimeoutError, filelock  # noqa: E402
except Exception:  # pragma: no cover
	import contextlib

	class LockTimeoutError(Exception):
		pass

	@contextlib.contextmanager
	def filelock(ten, timeout=30, **kw):
		yield

QUYEN = {"System Manager", "Accounts Manager", "Accounts User"}

# Tên khoá của lượt dựng chứng từ.
#
# VÌ SAO PHẢI CÓ KHOÁ (ca thật 31/08/2026, mất 31 tờ trùng)
# ----------------------------------------------------------
# Ngày 31/08 chạy bù hai lượt chồng lên nhau: một lượt gọi trước còn đang
# chạy dở ở máy chủ, một lượt nữa gọi vào. Cả hai đều đọc hàng đợi bằng
# `da_tao_chung_tu = 0`, đều thấy CÙNG một tờ, `_da_co_chung_tu` của cả hai
# đều trả về rỗng vì chưa bên nào kịp ghi, rồi cả hai cùng dựng.
#
# Kết quả: 31 cặp Hoá đơn mua hàng y hệt nhau, cách nhau ba mươi mốt phần
# nghìn giây, 81.136.219 đ mua vào đếm hai lần. Chưa tờ nào ghi sổ nên chưa
# vào sổ cái, nhưng nếu kế toán ghi sổ trước khi ai kịp nhìn thì đó là một
# tháng số liệu mua vào sai gấp đôi.
#
# Phép kiểm "đã có chứng từ chưa" KHÔNG BAO GIỜ tự nó đủ, vì giữa lúc kiểm
# và lúc ghi luôn có một khe hở. Chỉ có khoá mới đóng được khe đó.
#
# Từ bản này nguy cơ còn cao hơn trước chứ không thấp đi: nhịp tự động 15
# phút vừa được khai lại, và nút "Đồng bộ M-Invoice" cho phép người ta bấm
# tay bất cứ lúc nào. Hai đường đó gặp nhau là chuyện sớm muộn.
KHOA_DUNG = "vagabond_minvoice_dung_chung_tu"

# Mỗi lượt dựng tối đa bao nhiêu tờ. Cao hơn thì một lượt chạy quá dài và
# Frappe cắt ngang giữa chừng.
MOI_LUOT = 200

# Mốc sớm nhất còn đi dựng chứng từ. Trước mốc này là sổ của năm cũ, đã
# khoá, không tự đụng vào (Điều 11).
NGAY_BAT_DAU = "2026-01-01"

TRUONG_MOI = {
	DT_HD: [
		{
			"fieldname": "so_lan_thu",
			"label": "Số lần đã thử dựng chứng từ",
			"fieldtype": "Int",
			"insert_after": "da_tao_chung_tu",
			"read_only": 1,
			"description": (
				"Máy tự đếm. Tờ thử nhiều lần mà vẫn hỏng thì xuống cuối hàng "
				"đợi, nhưng KHÔNG bị đánh dấu là đã xong."
			),
		},
	],
}


def _kiem_quyen(viec="xem hoá đơn điện tử chưa thành chứng từ"):
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw(
			"Tài khoản của bạn không có quyền %s. Nhờ chị Dung hoặc anh Việt "
			"chạy giúp." % viec
		)


def _da_co_chung_tu(ma):
	"""Tờ này đã có chứng từ thật trong sổ chưa. Trả tên chứng từ hoặc rỗng."""
	for dt in (PI, SI):
		ten = frappe.db.get_value(dt, {"custom_minvoice_id": ma}, "name")
		if ten:
			return ten
	return ""


def _trung_theo_so_hoa_don(r):
	"""Đã có chứng từ khác cùng nhà cung cấp và cùng số hoá đơn chưa.

	Kế toán có thể đã gõ tay một tờ mà không gắn mã hoá đơn điện tử. Dựng
	thêm là hai chứng từ cho một tờ hoá đơn, và số liệu mua vào nhân đôi.

	Tìm được thì DỪNG và báo, KHÔNG tự gắn mã vào chứng từ của người khác:
	gắn nhầm còn khó gỡ hơn là để hai bên tự nhìn nhau.
	"""
	so = str(r.get("so_hd") or "").strip()
	if not so:
		return ""
	mst = (r.get("mst_doi_tac") or "").strip()
	ncc = None
	if mst:
		ncc = frappe.db.get_value("Supplier", {"tax_id": mst}, "name")
	if not ncc and r.get("nguoi_mua_ban"):
		ncc = frappe.db.get_value(
			"Supplier", {"supplier_name": r["nguoi_mua_ban"].strip()}, "name")
	if not ncc:
		return ""
	return frappe.db.get_value(PI, {
		"supplier": ncc, "bill_no": so, "docstatus": ["<", 2],
		"custom_minvoice_id": ["in", ["", None]],
	}, "name") or ""


def _ghi_hong(ma, loi):
	"""Ghi lý do hỏng và tăng số lần thử. TUYỆT ĐỐI không đóng dấu đã xong.

	Đây là chỗ bản cũ sai nặng nhất: nó đóng dấu `da_tao_chung_tu = 1` ngay
	cả khi không dựng được gì, nên tờ hỏng biến mất khỏi mọi danh sách.
	"""
	try:
		lan = cint(frappe.db.get_value(DT_HD, ma, "so_lan_thu"))
		frappe.db.set_value(DT_HD, ma, {
			"ly_do_bo_qua": rut_gon_loi(loi),
			"so_lan_thu": lan + 1,
			"da_tao_chung_tu": 0,
		}, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_chung_tu: ghi hong")


def _ghi_xong(ma, ghi_chu=""):
	"""Đóng dấu đã xong. CHỈ gọi khi thật sự có chứng từ."""
	frappe.db.set_value(DT_HD, ma, {
		"da_tao_chung_tu": 1,
		"ly_do_bo_qua": ghi_chu or "",
	}, update_modified=False)


def bo_mau_thue_mat_hang(doc):
	"""Xoá mẫu thuế mặt hàng khỏi mọi dòng của chứng từ vừa dựng.

	ĐÂY LÀ PHÉP SỬA CHÍNH của bản này. Xem mục 1 ở đầu tệp.

	Con số thuế trên hoá đơn điện tử là con số đã gửi cơ quan thuế. Mẫu
	thuế trên danh mục Món là dự đoán. Để cả hai cùng nói thì ERPNext bắt
	chúng khớp nhau, mà chúng không có lý do gì phải khớp.

	Xoá xong thì thuế suất từng dòng bằng 0, và ERPNext bỏ qua phép đối
	chiếu với dòng thuế dạng "Actual" (đã dò mã nguồn v16,
	`controllers/taxes_and_totals.py`).
	"""
	for d in doc.get("items") or []:
		try:
			# CHUỖI RỖNG, KHÔNG PHẢI None. Đây là chỗ bản đầu sai và tưởng đã
			# xong: deploy v315 xong chạy thử vẫn hỏng nguyên si.
			#
			# `accounts_controller.set_missing_item_details` chép giá trị từ
			# danh mục Món vào ô nào đang là None:
			#
			#     if item.get(fieldname) is None or fieldname in force_item_fields:
			#         item.set(fieldname, value)
			#
			# `item_tax_template` KHÔNG nằm trong `force_item_fields`, nên đặt
			# chuỗi rỗng là ERPNext để yên, còn đặt None là nó điền lại mẫu
			# thuế của mã hàng ngay trong lúc validate, và mọi công xoá ở đây
			# thành công cốc.
			d.item_tax_template = ""
			d.item_tax_rate = "{}"
		except Exception:
			continue
	return doc


def _dong_pi(x, tk_chi_phi, mapped=None, uom=None, he_so=1):
	"""Một dòng Hoá đơn mua hàng từ một dòng hoá đơn điện tử.

	Ghim luôn `price_list_rate` bằng đúng đơn giá trên hoá đơn. Bảng giá
	nhập trong máy chỉ là giá tham khảo của mình, còn đơn giá trên hoá đơn
	điện tử là số nhà cung cấp đã gửi cơ quan thuế. Không ghim thì ERPNext
	lấy giá bảng điền vào những dòng đơn giá 0, và ngày 27/08/2026 việc đó
	đã làm tờ tiếp khách Avanti phình thêm 4,5 triệu.
	"""
	dong = {
		"qty": x["sl"],
		"rate": x["gia"],
		"price_list_rate": x["gia"],
		"discount_percentage": 0,
		"discount_amount": 0,
		"margin_rate_or_amount": 0,
		"conversion_factor": he_so or 1,
		"description": x["ten"] + ((" (%s)" % x["dvt"]) if x["dvt"] else ""),
	}
	if mapped:
		dong["item_code"] = mapped
		dong["uom"] = uom
	else:
		dong["item_name"] = (x["ten"] or "Hàng hoá/dịch vụ")[:140]
		dong["uom"] = uom or "Nos"
		dong["stock_uom"] = uom or "Nos"
	# TEN NHA CUNG CAP GHI PHAI CON LAI TREN MOI DONG, ke ca dong da co ma
	# hang. Truoc 04/09/2026 o nay chi ghi cho dong CHUA co ma, nen mot khi
	# dong duoc gan ma thi ERPNext thay `item_name` bang ten Mon cua minh va
	# ten goc bien mat. Mat ten goc la mat cai khoa duy nhat de:
	#   - dung lai to ma van giu duoc ma hang nguoi vua gan,
	#   - ghi nho ma do vao bang anh xa cho lan sau.
	# Ca that HDM-26-08-00149 Green Ball ngay 04/09/2026, xem `dung_lai_hddt`.
	dong["ten_hang_ncc"] = (x["ten"] or "")[:140]
	if tk_chi_phi:
		dong["expense_account"] = tk_chi_phi
	return dong


@frappe.whitelist()
def con_sot(tu_ngay=None, den_ngay=None, gioi_han=2000):
	"""CHỈ ĐỌC: hoá đơn điện tử chưa thành chứng từ, gom theo lý do.

	Đây là màn mà lẽ ra phải có từ đầu. Không có nó thì 125 tờ nằm im một
	tháng mà không ai biết, và chỉ lộ khi có người ngồi dò tay.

	Soi bằng SỰ THẬT chứ không bằng lời hứa: tờ nào không có chứng từ nào
	trỏ về là còn sót, bất kể ô `da_tao_chung_tu` đang ghi gì.
	"""
	_kiem_quyen()
	den_ngay = den_ngay or nowdate()
	tu_ngay = tu_ngay or frappe.utils.add_days(den_ngay, -180)

	ds = frappe.get_all(
		DT_HD,
		filters={"ngay_lap": ["between", [tu_ngay, den_ngay]]},
		fields=["name", "loai", "ky_hieu", "so_hd", "ngay_lap",
			"nguoi_mua_ban", "tong_tien", "trang_thai", "ly_do_bo_qua",
			"da_tao_chung_tu"],
		order_by="ngay_lap desc",
		limit_page_length=cint(gioi_han) or 2000,
	)

	hang = []
	so_dau_ra_fabi = 0
	for h in ds:
		if khoi_dung_duoc(h.get("trang_thai")):
			continue
		if _da_co_chung_tu(h["name"]):
			continue
		if (h.get("loai") or "") == LOAI_RA:
			# Đầu ra bán lẻ do Fabi xuất, không phải việc của hệ (anh Việt
			# chốt 26/08/2026). Vẫn ĐẾM để có người nhìn thấy con số, nhưng
			# không đổ vào danh sách việc phải làm.
			so_dau_ra_fabi += 1
			continue
		hang.append({
			"ma": h["name"],
			"loai": h.get("loai"),
			"ky_hieu": h.get("ky_hieu"),
			"so_hd": h.get("so_hd"),
			"ngay_lap": str(h.get("ngay_lap") or ""),
			"doi_tac": (h.get("nguoi_mua_ban") or "")[:60],
			"tong_tien": flt(h.get("tong_tien")),
			"ly_do": rut_gon_loi(h.get("ly_do_bo_qua")) if h.get("ly_do_bo_qua")
				else ("Đã đóng dấu xong nhưng không có chứng từ nào"
					if cint(h.get("da_tao_chung_tu")) else "Chưa tới lượt dựng"),
		})

	return {
		"tu_ngay": str(tu_ngay), "den_ngay": str(den_ngay),
		"trung": _dem_trung(),
		"so_to": len(hang),
		"tong_tien": sum(abs(h["tong_tien"]) for h in hang),
		"theo_ly_do": gom_theo_ly_do(hang),
		"dau_ra_fabi": so_dau_ra_fabi,
		"vo_ruot": _dem_vo_ruot(),
		"ds": hang[:500],
	}


@frappe.whitelist()
def cho_dung_phieu_mua(so_ngay=180, gioi_han=300):
	"""CHỈ ĐỌC: hoá đơn ĐẦU VÀO đã nhận mà chưa thành phiếu mua.

	Codex #352 (22/09/2026): lỗi dựng phiếu chỉ hiện trong hộp kết quả lúc
	bấm đồng bộ, đóng hộp là mất; không màn nghiệp vụ nào cho kế toán thấy
	thường trực tờ nào đang chờ, vì sao, và mở bản nguồn ở đâu. Cửa này nuôi
	thanh báo trên màn Hoá đơn mua hàng.

	Nhẹ hơn `con_sot`: chỉ đầu vào, và dò chứng từ đã có bằng MỘT truy vấn
	cho cả lô thay vì từng tờ, vì thanh báo chạy mỗi lần mở danh sách."""
	_kiem_quyen()
	den = nowdate()
	tu = frappe.utils.add_days(den, -(cint(so_ngay) or 180))
	ds = frappe.get_all(
		DT_HD,
		filters={"loai": LOAI_VAO, "ngay_lap": ["between", [tu, den]],
			"trang_thai": ["not in", list(TT_KHOI_DUNG)]},
		fields=["name", "ky_hieu", "so_hd", "ngay_lap", "nguoi_mua_ban", "tong_tien",
			"ly_do_bo_qua", "da_tao_chung_tu", "so_lan_thu"],
		order_by="ngay_lap desc",
		limit_page_length=0,
	)
	ma = [h["name"] for h in ds]
	co = set()
	if ma:
		co = set(frappe.get_all(PI, filters={"custom_minvoice_id": ["in", ma]}, pluck="custom_minvoice_id"))
	hang = []
	for h in ds:
		if h["name"] in co:
			continue
		k, ten = nhom_cho_dung(h.get("so_hd"), h.get("ly_do_bo_qua"), h.get("da_tao_chung_tu"))
		hang.append({
			"ma": h["name"], "ky_hieu": h.get("ky_hieu") or "", "so_hd": h.get("so_hd") or "",
			"ngay_lap": str(h.get("ngay_lap") or ""), "ncc": (h.get("nguoi_mua_ban") or "")[:80],
			"tong_tien": flt(h.get("tong_tien")), "nhom": k, "ten_nhom": ten,
			"ly_do": rut_gon_loi(h.get("ly_do_bo_qua")) if h.get("ly_do_bo_qua") else "",
			"so_lan_thu": cint(h.get("so_lan_thu")),
		})
	dem = {}
	for h in hang:
		o = dem.setdefault(h["nhom"], {"nhom": h["nhom"], "ten": h["ten_nhom"], "so_to": 0, "tien": 0.0})
		o["so_to"] += 1
		o["tien"] += abs(h["tong_tien"])
	thu_tu = [k for k, _ in NHOM_CHO_DUNG]
	return {
		"so_to": len(hang), "tong_tien": sum(abs(h["tong_tien"]) for h in hang),
		"theo_nhom": sorted(dem.values(), key=lambda o: thu_tu.index(o["nhom"])),
		"ds": hang[:cint(gioi_han) or 300], "tu_ngay": str(tu), "den_ngay": str(den),
	}


def _dem_trung():
	"""Chứng từ nào đang trùng: nhiều tờ cùng trỏ về một hoá đơn điện tử.

	Chỉ đếm tờ CÒN SỐNG: bỏ tờ đã huỷ ở ERPNext và tờ đã tick "Đã huỷ" của
	mình, vì gỡ trùng bằng cách đánh dấu huỷ là cách gỡ hợp lệ.
	"""
	# GOM Ở TẦNG CƠ SỞ DỮ LIỆU, KHÔNG KÉO CẢ BẢNG LÊN PYTHON
	#
	# Bản đầu của hàm này (31/08/2026) kéo TOÀN BỘ hoá đơn mua và hoá đơn
	# bán có mã hoá đơn điện tử về rồi mới gom. Bảng hoá đơn bán có hàng
	# chục nghìn dòng, nên màn Còn sót trả về 504 ngay lần mở đầu tiên -
	# tức là phép đếm dựng ra để canh chứng từ trùng lại làm hỏng đúng cái
	# màn dùng để soi chứng từ trùng.
	#
	# Câu SQL dưới chỉ trả về những mã ĐÃ trùng, thường là không dòng nào.
	# Phép gom vẫn đi qua `cap_trung` để một chỗ tính, một chỗ kiểm (QT-19).
	try:
		hang = []
		for dt in (PI, SI):
			try:
				dong = frappe.db.sql(
					"""select custom_minvoice_id as ma, group_concat(name) as ten
					from `tab%s`
					where docstatus < 2
					and ifnull(custom_minvoice_id, '') != ''
					and ifnull(vgb_huy, 0) = 0
					group by custom_minvoice_id
					having count(*) > 1""" % dt, as_dict=True)
			except Exception:
				# Bang nao chua co o vgb_huy thi bo qua bang do, dung de ca
				# phep dem chet theo.
				continue
			for r in dong:
				for ten in str(r.get("ten") or "").split(","):
					if ten.strip():
						hang.append({"ma_hddt": r.get("ma"), "ten": ten.strip()})
		nhom = cap_trung(hang)
		return {
			"so_nhom": len(nhom),
			"so_to_thua": sum(n["so_to"] - 1 for n in nhom),
			"ds": nhom[:50],
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "minvoice_chung_tu: dem trung")
		return {"so_nhom": 0, "so_to_thua": 0, "ds": []}


def _dem_vo_ruot():
	"""Đếm bản ghi VỎ RUỘT: có mã hoá đơn nhưng chưa có ruột.

	Vỏ ruột sinh ra khi M-Invoice trả về một tờ mà chưa kịp đổ dữ liệu vào:
	số hoá đơn trống, ngày trống, tiền bằng 0. Lượt kéo sau lẽ ra lành lại,
	`minvoice_dong_bo.vo_ruot` lo việc đó.

	Nhưng đếm ngày 26/08/2026 thì có 112 vỏ ruột ĐẦU VÀO, cái cũ nhất từ
	22/07, tức là hơn một tháng chưa lành. Nhịp quét đêm chỉ lùi 30 ngày nên
	không với tới cái cũ, còn cái mới thì M-Invoice vẫn chưa trả số.

	Mỗi vỏ ruột đầu vào là một hoá đơn mua có thể đang thiếu. Nên phải ĐẾM
	và cho người nhìn thấy, chứ không để nó nằm im như 22 tờ vừa rồi.
	"""
	try:
		return {
			"vao": frappe.db.count(DT_HD, {
				"so_hd": ["in", ["", None, "0"]], "loai": LOAI_VAO}),
			"ra": frappe.db.count(DT_HD, {
				"so_hd": ["in", ["", None, "0"]], "loai": LOAI_RA}),
			"cu_nhat": frappe.db.get_value(
				DT_HD, {"so_hd": ["in", ["", None, "0"]], "loai": LOAI_VAO},
				"creation", order_by="creation asc"),
		}
	except Exception:
		return {"vao": 0, "ra": 0, "cu_nhat": None}


@frappe.whitelist()
def lanh_vo_ruot(so_ngay=60):
	"""Kéo lại một khoảng rộng để lành các bản ghi vỏ ruột.

	Không dựng chứng từ nào, chỉ đổ ruột vào những tờ còn trống. Nhịp quét
	đêm chỉ lùi 30 ngày, nên tờ cũ hơn phải gọi tay ở đây.

	Chạy xong mà vẫn còn vỏ ruột thì nghĩa là chính M-Invoice chưa có số cho
	tờ đó, không phải lỗi bên mình. Lúc đó là câu hỏi cho nhà cung cấp phần
	mềm hoá đơn, đừng ngồi dò tay tiếp.
	"""
	_kiem_quyen("kéo lại hoá đơn điện tử")
	from vagabond import minvoice_dong_bo

	truoc = _dem_vo_ruot()
	kq = minvoice_dong_bo._keo(so_ngay=cint(so_ngay) or 60)
	sau = _dem_vo_ruot()
	return {
		"ok": 1, "keo": kq, "truoc": truoc, "sau": sau,
		"da_lanh": max(0, cint(truoc.get("vao")) - cint(sau.get("vao"))),
		"loi_nhan": (
			"Vỏ ruột đầu vào: trước %s tờ, sau %s tờ. Còn lại là những tờ "
			"M-Invoice vẫn chưa trả số, hỏi bên họ chứ đừng dò tay."
			% (truoc.get("vao"), sau.get("vao"))
		),
	}


@frappe.whitelist()
def mo_lai(ma=None, tat_ca_hong=0):
	"""Mở lại tờ đã bị đóng dấu nhầm, để lượt chạy sau thử lại. CHỈ ĐỔI CỜ.

	Không dựng chứng từ nào ở đây, không đụng tới số liệu. Chỉ gỡ cái dấu
	"xong rồi" đang sai.
	"""
	_kiem_quyen("mở lại hoá đơn điện tử đã bị bỏ qua")
	if cint(tat_ca_hong):
		kq = con_sot()
		ds = [h["ma"] for h in (kq.get("ds") or [])]
	else:
		ds = [x for x in [(ma or "").strip()] if x]
	if not ds:
		frappe.throw("Chưa chỉ ra tờ nào.")
	for x in ds:
		frappe.db.set_value(DT_HD, x, {
			"da_tao_chung_tu": 0, "so_lan_thu": 0,
		}, update_modified=False)
	frappe.db.commit()
	return {"ok": 1, "mo_lai": len(ds),
		"loi_nhan": "Đã mở lại %s tờ, lượt dựng sau sẽ thử lại." % len(ds)}


# ------------------------------------------------- dựng chứng từ đầu vào


def _cty():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _tim_ncc(mst, ten):
	"""Nhà cung cấp theo mã số thuế, rồi tới tên. Không có thì dựng mới."""
	mst = (mst or "").strip()
	goc = mst.split("-")[0] if mst else ""
	sup = None
	if mst:
		sup = frappe.db.get_value("Supplier", {"tax_id": mst}, "name")
		if not sup and goc != mst:
			sup = frappe.db.get_value("Supplier", {"tax_id": goc}, "name")
		if not sup:
			sup = frappe.db.get_value("Supplier", {"tax_id": ["like", goc + "%"]}, "name")
	if not sup and ten:
		sup = frappe.db.get_value("Supplier", {"supplier_name": ten.strip()}, "name")
	# TÊN ĐÃ BỊ CẮT CÒN 140 (ca thật 31/08/2026)
	#
	# Ô `supplier_name` chỉ chứa 140 ký tự, mà tên trên hoá đơn điện tử thì
	# dài hơn: "CHI NHÁNH CÔNG TY TNHH LUCA..." bị cắt cụt lúc dựng lần đầu.
	# Lượt sau tra bằng tên ĐẦY ĐỦ nên không thấy, hệ đi dựng nhà cung cấp
	# mới, và cơ sở dữ liệu ném Duplicate entry vì khoá chính trùng.
	#
	# Tra thêm một nhịp bằng đúng cái tên đã cắt trước khi kết luận là chưa
	# có. Cùng một nhà cung cấp mà đẻ ra hai bản ghi còn tệ hơn báo lỗi.
	ten_cat = (ten or ("NCC " + mst))[:140].strip()
	if not sup and ten_cat:
		sup = frappe.db.get_value("Supplier", {"supplier_name": ten_cat}, "name")
	if not sup and ten_cat and frappe.db.exists("Supplier", ten_cat):
		sup = ten_cat
	if sup:
		return sup, goc
	s = frappe.get_doc({
		"doctype": "Supplier",
		"supplier_name": ten_cat,
		"supplier_group": "Công ty (NCC)",
		"supplier_type": "Company",
		"country": "Vietnam",
	})
	if mst:
		s.tax_id = mst
	try:
		s.insert(ignore_permissions=True)
	except Exception:
		# Vẫn trùng thì nghĩa là có sẵn một bản ghi mang đúng tên đó, chỉ là
		# ba nhịp tra ở trên không soi ra (khác dấu cách, khác hoa thường).
		# Lùi lại lấy bản ghi có sẵn chứ đừng làm chết cả tờ hoá đơn.
		frappe.db.rollback()
		sup = frappe.db.get_value("Supplier", {"supplier_name": ten_cat}, "name")
		if not sup:
			raise
		return sup, goc
	return s.name, goc


def _tra_ma_hang(x, goc_mst, ncc):
	"""Mã hàng của hệ ứng với dòng này. Không tra ra thì trả (None, dvt)."""
	uom = x.get("dvt")  # Giữ tên NCC để tra alias trước khi xét UOM tồn tại.
	mapped = None
	if goc_mst:
		from vagabond.quy_cach_ncc import tim_mon
		mapped = tim_mon(goc_mst, x.get("ma"), x.get("ten"))
	if not mapped and x["ten"]:
		mapped = frappe.db.get_value("Anh Xa Mat Hang NCC", {
			"nha_cung_cap": ncc, "ten_hang_ncc": x["ten"]}, "ma_hang")
	# #332: ánh xạ lịch sử có thể trỏ món vừa ngừng dùng. Giữ dòng nguồn
	# chưa gán mã để thu mua chọn lại, không lấy giá/quy cách mã khác và
	# không làm cả hóa đơn biến mất vì resolver UOM ném lỗi.
	if mapped and frappe.db.get_value("Item", mapped, "disabled"):
		mapped = None
	if not mapped:
		return None, uom if uom and frappe.db.exists("UOM", uom) else None, 1

	dung_uom, he_so = don_vi_theo_ma(mapped, uom, goc_mst, x.get("ten"))
	return mapped, dung_uom, he_so


def don_vi_theo_ma(mapped, uom, mst=None, ten_ncc=None):
	"""(don vi dung, he so quy doi) cua mon `mapped` ung voi don vi NCC ghi.

	Tach ra khoi `_tra_ma_hang` ngay 04/09/2026 de duong DUNG LAI dung
	chung dung mot phep nan don vi voi duong dung chung tu lan dau. Truoc
	do phep nay nam lut trong `_tra_ma_hang`, nen cho nao muon nan don vi
	cho mot ma hang NGUOI VUA GAN deu phai chep lai - ma chep lai thi som
	muon cung lech nhau (QT-19).
	"""
	# ERPNext v16.28.0: erpnext/controllers/buying_controller.py,
	# BuyingController.set_qty_as_per_stock_uom:
	# if not d.conversion_factor and d.item_code: frappe.throw(...)
	# d.stock_qty = flt(d.qty) * flt(d.conversion_factor)
	# Core chỉ kiểm có hệ số, không kiểm nó khớp quy cách danh mục.
	# Không nhận diện được quy cách thì không được đổi UOM về kho và giữ qty:
	# đó là biến một hộp thành một gram. Bản MInvoice gốc vẫn được giữ để xử lý.
	if not mapped:
		return uom, 1
	from vagabond import dvt_mua as dv
	import math
	dvt_kho = frappe.db.get_value("Item", mapped, "stock_uom")
	from vagabond.quy_cach_ncc import lay
	don_vi_da_duyet = lay(mapped, mst, ten_ncc) if mst and ten_ncc else None
	nguon = str(don_vi_da_duyet or uom or "").strip()
	ds = frappe.get_all("UOM Conversion Detail", filters={"parent": mapped, "parenttype": "Item"},
		fields=["uom", "conversion_factor"])
	if dich_vu_khong_ghi_don_vi(nguon, frappe.db.get_value("Item", mapped, "is_stock_item")):
		return dvt_kho, 1
	ung_vien = [nguon, dv.goi_y_don_vi(nguon)]
	for ten in ung_vien:
		if not ten:
			continue
		if dv.cung_don_vi(ten, dvt_kho):
			return dvt_kho, 1
		khop = [r for r in ds if dv.cung_don_vi(r.uom, ten)]
		if len(khop) == 1 and math.isfinite(flt(khop[0].conversion_factor)) and flt(khop[0].conversion_factor) > 0:
			return khop[0].uom, khop[0].conversion_factor
	frappe.throw("Món %s: chưa xác định được quy đổi đơn vị nhà cung cấp '%s' sang %s. "
		"Mở Món, khai đúng đơn vị và hệ số trong bảng quy đổi rồi tạo lại hoá đơn từ bản gốc. "
		"Hệ thống không tự lấy hệ số 1 hoặc đổi số lượng để khớp tiền."
		% (mapped, nguon or "(trống)", dvt_kho), title="Cần khai quy cách mua")


def don_vi_chua_khai(dvt_ncc, dvt_dang_dung, he_so_dang_dung):
	"""Dong nay co dang mang don vi bia ra khong.

	Ruot da chuyen sang `dvt_mua.don_vi_chua_khai` ngay 31/08/2026 de giu
	dung mot cho tinh (QT-19). Giu lai ten o day vi `dung_lai_hddt` va man
	Soat don vi dang goi qua duong nay.
	"""
	from vagabond import dvt_mua

	return dvt_mua.don_vi_chua_khai(dvt_ncc, dvt_dang_dung, he_so_dang_dung)

def dung_hoa_don_mua(r):
	"""Dựng một Hoá đơn mua hàng từ một tờ hoá đơn điện tử đầu vào.

	Trả về tên chứng từ. Ném lỗi thì người gọi ghi lý do, KHÔNG đóng dấu.
	"""
	cty = _cty()
	tk_chi_phi = frappe.db.get_value("Company", cty, "default_expense_account")
	tt_chi_phi = frappe.db.get_value("Company", cty, "cost_center")
	tk_thue_vao = frappe.db.get_value(
		"Account", {"company": cty, "name": ["like", "1331 -%"]}, "name")

	ncc, goc_mst = _tim_ncc(r.get("mst_doi_tac"), r.get("nguoi_mua_ban"))

	# Dấu của cả tờ. Tờ âm là hoá đơn điều chỉnh giảm hoặc hoá đơn thay thế
	# ghi số âm, Nghị định 70/2025 cho phép. Xem `nan_dau_dong`.
	dau = dau_cua_to(r.get("tong_tien"))
	dong_goc = [dong_tu_hoa_don(it, dau)
		for it in dong_hang_hoa(json.loads(r.get("chi_tiet") or "[]"))]

	dong = []
	for x in dong_goc:
		ma, uom, he_so = _tra_ma_hang(x, goc_mst, ncc)
		dong.append(_dong_pi(x, tk_chi_phi, ma, uom, he_so))

	if not dong:
		# Neo vao `muc_tieu_truoc_thue` chu khong vao o `tien_truoc_thue`:
		# nha cung cap khong khai tach thi o do bang 0 va dong duy nhat cua
		# to se mang don gia 0. Xem su co 27/08/2026 trong ham do.
		dong = [_dong_pi({
			"ma": "", "ten": "Hàng hoá/dịch vụ theo hoá đơn", "dvt": None,
			"sl": dau, "gia": abs(muc_tieu_truoc_thue(r)), "tien": 0,
		}, tk_chi_phi)]

	# Cân theo TRỊ TUYỆT ĐỐI rồi mới gắn dấu lại, để tờ âm và tờ dương đi
	# chung một đường. Nhân `dau` vào cả hai vế là phép nhân cùng chiều nên
	# tờ dương ra đúng kết quả cũ, không đổi gì.
	# Can theo con so MAY SE GHI chu khong theo con so doc len tu hoa don.
	# Truoc 16/09/2026 cho nay nhan thang `qty * rate` nen khong nhin thay
	# phan bi cat o o don gia, va to ALOIN so 1144 (260 x 1.576,92) vao so
	# thieu dung mot dong. Duong dung lai da tinh dung tu 27/08, duong dung
	# moi thi chua, nay hai duong dung chung mot ham.
	dp_gia, dp_tien, dp_sl = do_chinh_xac(
		{"doctype": PI, "currency": "VND"}, r)
	tong_dong = sum(
		tien_dong_may_ghi(d.get("qty"), d.get("rate"), dp_gia, dp_tien, dp_sl)
		for d in dong
	)
	viec, so_tien = can_theo_truoc_thue(
		dau * tong_dong, dau * muc_tieu_truoc_thue(r))
	giam_gia = (dau * so_tien) if viec == "giam" else 0
	if viec == "phi":
		dong.append(_dong_pi({
			"ma": "", "ten": ten_dong_bu(so_tien), "dvt": None,
			"sl": dau, "gia": so_tien, "tien": so_tien,
		}, tk_chi_phi))

	pi = frappe.get_doc({
		"doctype": PI, "company": cty, "supplier": ncc,
		"set_posting_time": 1, "posting_date": str(r.get("ngay_lap")),
		"currency": "VND", "update_stock": 0,
		"is_return": 1 if flt(r.get("tong_tien")) < 0 else 0,
		"apply_discount_on": "Net Total", "discount_amount": giam_gia,
		"bill_no": str(r.get("so_hd") or ""), "bill_date": str(r.get("ngay_lap")),
		"custom_minvoice_id": r.get("name"),
		"custom_trang_thai_hddt": r.get("trang_thai") or "",
		"remarks": "m-invoice %s so %s%s" % (
			r.get("ky_hieu") or "", r.get("so_hd"),
			(" | Tra cuu: " + r["ma_tra_cuu"]) if r.get("ma_tra_cuu") else ""),
		"items": dong,
	})
	# Tờ âm thì tiền thuế cũng âm, nên phải xét KHÁC KHÔNG chứ không phải
	# lớn hơn không. Xét lớn hơn không là bỏ luôn dòng thuế của tờ âm, và
	# tổng chứng từ lệch đúng bằng tiền thuế.
	if tk_thue_vao and flt(r.get("tien_thue")) != 0:
		pi.append("taxes", {
			"charge_type": "Actual", "account_head": tk_thue_vao,
			"description": "Thuế GTGT được khấu trừ",
			"tax_amount": flt(r.get("tien_thue")),
			"category": "Total", "add_deduct_tax": "Add",
		})

	# PHÉP SỬA CHÍNH. Phải chạy TRƯỚC insert, vì ERPNext tính thuế từng dòng
	# ngay trong validate của insert.
	bo_mau_thue_mat_hang(pi)

	pi.cost_center = tt_chi_phi
	for d in pi.items:
		if not d.cost_center:
			d.cost_center = tt_chi_phi
	for t in pi.taxes:
		if not t.cost_center:
			t.cost_center = tt_chi_phi

	pi.insert(ignore_permissions=True)

	# HÀNG RÀO CUỐI: tổng của chứng từ vừa dựng phải bằng tổng trên hoá đơn
	# điện tử. Lệch thì ném lỗi, và người gọi sẽ huỷ cả lượt ghi của tờ này.
	#
	# Sai lặng lẽ còn tệ hơn không dựng: không dựng thì còn đếm được bằng
	# `con_sot`, còn dựng sai thì nó nằm trong sổ như một con số thật.
	#
	# Ngưỡng ở đây HỞ, giống phép nắn: từ MỘT đồng trở lên là không nhận.
	# Trước 16/09/2026 chỗ này so bằng `>` nên tờ lệch đúng một đồng lọt
	# qua và vào sổ. Nay tờ như vậy nằm lại `con_sot`, nơi có người nhìn.
	lech = flt(pi.grand_total) - flt(r.get("tong_tien"))
	if abs(lech) >= NGUONG_KHOP:
		frappe.throw(
			"Chứng từ dựng ra tổng %s đ, hoá đơn điện tử ghi %s đ, lệch %s đ. "
			"Không nhận." % (
				"{:,.0f}".format(flt(pi.grand_total)),
				"{:,.0f}".format(flt(r.get("tong_tien"))),
				"{:,.0f}".format(lech)),
		)
	return pi.name


def _mot_to(r):
	"""Xử một tờ. Lỗi nghiệp vụ trả lý do; rollback lỗi phải dừng cả lượt."""
	# Frappe utils/response.py gửi message_log về Desk dù exception đã bắt.
	# Giữ thông báo của caller, chỉ bỏ thông báo tờ lỗi đã chuyển vào báo cáo.
	thong_bao_truoc = list(frappe.local.message_log or [])
	ma = r.get("name")
	try:
		if khoi_dung_duoc(r.get("trang_thai")):
			_ghi_xong(ma, "Hoá đơn %s nên không cần chứng từ."
				% (r.get("trang_thai") or "").lower())
			return (0, "khoi_dung")
		cu = _da_co_chung_tu(ma)
		if cu:
			_ghi_xong(ma, "Đã có chứng từ %s." % cu)
			return (0, "da_co")
		if (r.get("loai") or "") == LOAI_RA:
			# Anh Việt chốt 26/08/2026: đầu ra bán lẻ do Fabi xuất. Xem mục
			# "Hoá đơn đầu ra không phải việc của mô đun này" ở đầu tệp.
			_ghi_xong(ma, "Hoá đơn đầu ra do Fabi xuất, hệ không dựng chứng từ.")
			return (0, "dau_ra_fabi")
		trung = _trung_theo_so_hoa_don(r)
		if trung:
			_ghi_hong(ma, "Đã có chứng từ %s cùng nhà cung cấp và cùng số hoá "
				"đơn nhưng chưa gắn mã hoá đơn điện tử. Nhờ kế toán soi rồi "
				"gắn tay, hệ không tự gắn vào chứng từ có sẵn." % trung)
			return (0, "trung_so_hoa_don")
		ten = dung_hoa_don_mua(r)
		_ghi_xong(ma, "")
		return (1, ten)
	except Exception as e:
		# Huỷ mọi thứ tờ này vừa ghi dở, kể cả chứng từ đã insert mà đối
		# chiếu tổng không đạt. Rollback chỉ lùi tới lần commit gần nhất, mà
		# `_chay` commit sau TỪNG tờ, nên không đụng tới tờ trước.
		frappe.db.rollback()
		frappe.local.message_log = thong_bao_truoc
		_ghi_hong(ma, e)
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: to %s" % ma)
		return (0, rut_gon_loi(e))


# Lý do bỏ qua được coi là HỢP LỆ, không phải hỏng. Tách hẳn ra hằng số vì
# ngày 31/08/2026 lượt chạy tay báo "173 con_hong" trong khi cả 173 tờ đều
# là đầu ra Fabi, tức là không có gì hỏng cả. Con số báo động sai còn nguy
# hơn không báo: nhìn quen rồi thì tới lúc hỏng thật cũng không ai giật mình.
LY_DO_BO_QUA_HOP_LE = ("khoi_dung", "da_co", "dau_ra_fabi")

# Mỗi lượt đóng dấu tối đa bao nhiêu tờ đầu ra. Đóng dấu chỉ là một câu
# UPDATE nên nhẹ hơn dựng chứng từ rất nhiều, cho phép nhiều hơn MOI_LUOT.
DAU_RA_MOI_LUOT = 2000


def _dong_dau_ra(gioi_han=None):
	"""Đóng dấu hàng loạt hoá đơn ĐẦU RA, chúng không cần chứng từ.

	VÌ SAO PHẢI TÁCH RA MỘT ĐƯỜNG RIÊNG (31/08/2026)
	------------------------------------------------
	Đầu ra bán lẻ do Fabi xuất, hệ không dựng chứng từ cho chúng (anh Việt
	chốt 26/08/2026). Nhưng bản trước vẫn thả chúng vào CÙNG hàng đợi với
	đầu vào, mỗi tờ ăn một chỗ trong 200 chỗ của một lượt.

	Ngày 31/08/2026 đếm được 3.907 tờ đầu ra đứng xếp hàng. Với nhịp 200 tờ
	một lượt thì một hoá đơn MUA mới về phải chờ gần hai mươi lượt mới tới
	lượt mình, trong khi việc duy nhất cần làm với 3.907 tờ kia là đặt một
	con số 1 vào một ô.

	Nên: quét chúng bằng một đường riêng, đóng dấu hàng loạt, và hàng đợi
	dựng chứng từ ở dưới chỉ còn ĐẦU VÀO. Hai việc khác hẳn nhau về giá,
	gộp chung một hàng đợi là để việc rẻ chặn đường việc đắt.
	"""
	ds = frappe.get_all(
		DT_HD,
		filters={"da_tao_chung_tu": 0, "loai": LOAI_RA},
		pluck="name",
		limit_page_length=cint(gioi_han) or DAU_RA_MOI_LUOT,
	)
	for ma in ds:
		_ghi_xong(ma, "Hoá đơn đầu ra do Fabi xuất, hệ không dựng chứng từ.")
	if ds:
		frappe.db.commit()
	return len(ds)


def _chay(tu_ngay=None, den_ngay=None, gioi_han=None):
	"""Dựng chứng từ cho các tờ chưa xong. MỘT LƯỢT MỘT LÚC. Trả về số đếm.

	Khoá bọc CẢ lượt chứ không bọc từng tờ. Bọc từng tờ vẫn hở: hai lượt
	đọc hàng đợi cùng lúc thì cả hai đã cầm sẵn cùng một danh sách, khoá
	bên trong chỉ làm chúng dựng nối đuôi nhau chứ không ngăn được tờ thứ
	hai. Phải chặn từ lúc đọc hàng đợi.

	Xin không được khoá thì BỎ LƯỢT chứ không chạy. Bỏ một lượt là mười lăm
	phút sau dựng, không mất gì; chạy chồng là sinh chứng từ trùng, mà gỡ
	chứng từ trùng thì phải có người ngồi dò từng cặp.
	"""
	try:
		pila = ExitStack()
		pila.enter_context(filelock(KHOA_DUNG, timeout=5))
	except LockTimeoutError:
		return {
			"quet": 0, "da_dung": 0, "bo_qua_hop_le": 0, "dau_ra_dong_dau": 0,
			"con_hong": 0, "vi_du_hong": [], "dang_chay_do": 1,
			"tu_ngay": str(tu_ngay or ""), "den_ngay": str(den_ngay or ""),
			"loi_nhan": (
				"Máy đang dựng chứng từ dở từ lượt trước. Anh chị chờ một phút "
				"rồi bấm lại, đừng bấm thêm lần nữa kẻo sinh chứng từ trùng."
			),
		}
	except Exception:
		# Khong lay duoc khoa vi ly do khac thi ghi nhat ky roi chay tiep:
		# khong duoc vi mot cai khoa hong ma ca day chuyen dung lai.
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: khong lay duoc khoa dung")
		pila = ExitStack()
	try:
		return _chay_trong_khoa(tu_ngay, den_ngay, gioi_han)
	finally:
		pila.close()


def _mo_lai_dau_sai(tu_ngay, den_ngay, gioi_han, cac_ma=None):
	"""#227: ba tờ Ngon có lỗi thuế nhưng bị đóng dấu xong, không có PI.

	Kéo60ngày không chữa được cờ này. Kiểm chứng từ thật trước khi mở lại;
	giữ cả chứng từ đã hủy để không tự tạo lại nghiệp vụ kế toán đã hủy.
	Chỉ sửa cờ hàng đợi, giữ lý do và số lần thử để không xóa dấu lỗi cũ.
	Gọi trong khóa dựng chung và khóa từng dòng nguồn trước khi cập nhật.
	"""
	loc_ma = ' and h.name in %(ma)s' if cac_ma else ''
	ds = frappe.db.sql('''select h.name from `tabMInvoice Invoice` h
		where h.loai=%(loai)s and h.ngay_lap between %(tu)s and %(den)s
		and h.da_tao_chung_tu=1
		and trim(coalesce(h.trang_thai, '')) not in %(bo)s
		and not exists (select 1 from `tabPurchase Invoice` p where p.custom_minvoice_id=h.name)
		and not exists (select 1 from `tabSales Invoice` s where s.custom_minvoice_id=h.name)
		''' + loc_ma + ''' order by h.ngay_lap, h.name limit %(so)s for update''',
		{'loai': LOAI_VAO, 'tu': tu_ngay, 'den': den_ngay, 'bo': TT_KHOI_DUNG,
		 'so': max(1, cint(gioi_han) or MOI_LUOT), 'ma': tuple(cac_ma or ())}, as_dict=True)
	for dong in ds:
		frappe.db.set_value(DT_HD, dong.name, 'da_tao_chung_tu', 0, update_modified=False)
	return len(ds)


def _chay_trong_khoa(tu_ngay=None, den_ngay=None, gioi_han=None):
	"""Ruột của một lượt dựng. CHỈ gọi từ `_chay`, nơi đã cầm khoá."""
	den_ngay = den_ngay or nowdate()
	# KHÔNG bó hẹp cửa sổ ngày. Bản cũ chỉ ngó 60 ngày gần nhất, tờ cũ hơn
	# thì vĩnh viễn không ai dựng và cũng không ai đếm. Hàng đợi đã xếp theo
	# số lần thử nên tờ hỏng không chiếm chỗ, mở rộng ra là an toàn.
	tu_ngay = tu_ngay or NGAY_BAT_DAU
	mo_lai_dau_sai = _mo_lai_dau_sai(tu_ngay, den_ngay, gioi_han)
	dau_ra = _dong_dau_ra()
	ds = frappe.get_all(
		DT_HD,
		filters={
			"ngay_lap": ["between", [tu_ngay, den_ngay]],
			"da_tao_chung_tu": 0,
			# CHỈ ĐẦU VÀO. Xem `_dong_dau_ra` ở trên để biết vì sao đầu ra
			# không được đứng chung hàng đợi này.
			"loai": LOAI_VAO,
		},
		fields=["name", "loai", "so_hd", "ky_hieu", "ngay_lap",
			"nguoi_mua_ban", "mst_doi_tac", "tien_truoc_thue", "tien_thue",
			"tong_tien", "ma_tra_cuu", "chi_tiet", "trang_thai"],
		# Tờ thử nhiều lần xuống cuối, để tờ mới không bao giờ bị tờ hỏng
		# chiếm hết chỗ trong một lượt.
		order_by="so_lan_thu asc, ngay_lap asc, so_hd asc",
		limit_page_length=cint(gioi_han) or MOI_LUOT,
	)
	dung, bo, hong = 0, 0, []
	for r in ds:
		ok, ghi_chu = _mot_to(r)
		if ok:
			dung += 1
		elif ghi_chu in LY_DO_BO_QUA_HOP_LE:
			bo += 1
		else:
			hong.append([r.get("loai"), r.get("so_hd"), ghi_chu])
		frappe.db.commit()
	return {"quet": len(ds), "da_dung": dung, "bo_qua_hop_le": bo,
		"mo_lai_dau_sai": mo_lai_dau_sai,
		"dau_ra_dong_dau": dau_ra,
		"con_hong": len(hong), "vi_du_hong": hong[:8],
		"tu_ngay": str(tu_ngay), "den_ngay": str(den_ngay)}


@frappe.whitelist()
def chay_bu(tu_ngay=None, den_ngay=None, gioi_han=None):
	"""Chạy tay một lượt dựng chứng từ, dùng khi phát hiện sót."""
	_kiem_quyen("dựng chứng từ từ hoá đơn điện tử")
	return _chay(tu_ngay, den_ngay, gioi_han)


def chay_tu_dong():
	"""Điểm gọi của bộ lập lịch. Lỗi giao dịch phải tới worker để đánh dấu thất bại.

	PHẢI CÓ TÊN NÀY TRONG `hooks.py`. Xem ca kiểm "nhip tu dong da khai
	trong hooks" ở khung/kiem_thu/thu_minvoice_chung_tu.py để biết vì sao
	có một ca kiểm chỉ để canh đúng một dòng khai báo.
	"""
	try:
		if not frappe.db.exists("DocType", DT_HD):
			return
		_chay()
	except Exception:
		# Không để scheduler nhận thành công rồi commit phần giao dịch hỏng.
		frappe.db.rollback()
		# Claude #352: ghi Error Log bằng hàng chờ (defer_insert), KHÔNG insert
		# trong giao dịch. Worker của Frappe v16 (ScheduledJobType.execute) gặp
		# exception thì rollback thêm một lần rồi mới ghi Failed, nên bản ghi
		# insert thường ở đây bị cuộn mất cùng giao dịch. Hàng chờ nằm ở redis,
		# nhịp save_to_db ghi sau, không phụ thuộc giao dịch này và không phải
		# thêm commit vào đường tài chính.
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: nhip tu dong vo loi", defer_insert=True)
		raise


# ------------------------------------------------- nút bấm tay và chuông báo


@frappe.whitelist()
def dong_bo_ngay(so_ngay=None):
	"""Kéo hoá đơn từ M-Invoice rồi dựng chứng từ, trong MỘT nhịp bấm.

	Đây là ruột của nút "Đồng bộ M-Invoice" trên màn danh sách Desk (anh
	Việt xin 31/08/2026). Trước bản này muốn chạy tay phải mở console gọi
	hai cửa riêng, mà kế toán thì không có đường nào.

	HAI BƯỚC, KHÔNG PHẢI MỘT. Bước kéo đổ hoá đơn từ M-Invoice vào bảng
	trung gian, bước dựng biến chúng thành chứng từ trong sổ. Ngày
	26/08/2026 bước kéo vẫn chạy đều suốt năm ngày trong khi bước dựng đã
	chết, và không ai nhận ra vì trong đầu mọi người "đồng bộ" là một việc.
	Nên ở đây trả về số đếm của CẢ HAI bước, để nhìn một cái là biết bước
	nào đứng.
	"""
	_kiem_quyen("đồng bộ hoá đơn điện tử")
	from vagabond import minvoice_dong_bo

	keo = minvoice_dong_bo._keo(so_ngay=cint(so_ngay) or 0)
	dung_ct = _chay()
	hoan_tat = not (keo.get("loi_o_loai") or keo.get("nguon_chua_du") or dung_ct.get("con_hong") or dung_ct.get("dang_chay_do"))
	return {
		"ok": int(hoan_tat),
		"keo": keo,
		"dung": dung_ct,
		"loi_nhan": (
			"Kéo về %s tờ mới, lành %s tờ vỏ ruột. Dựng được %s chứng từ, "
			"còn %s tờ hỏng cần soi."
			% (keo.get("moi", 0), keo.get("chua_lanh", 0),
				dung_ct.get("da_dung", 0), dung_ct.get("con_hong", 0))
		),
	}


# Bao nhiêu giờ không dựng được tờ nào thì coi là nhịp đã tắc.
#
# Nhịp dựng chạy 15 phút một lần, nên 6 tiếng là hai mươi tư lượt trượt
# liên tiếp - đủ dài để không kêu oan vì một đêm vắng hoá đơn, đủ ngắn để
# không lặp lại chuyện 26/08.
GIO_COI_LA_TAC = 6


def nhip_da_tac(so_to_cho, gio_ke_tu_lan_dung_cuoi, nguong=GIO_COI_LA_TAC):
	"""Nhịp dựng chứng từ có đang tắc không. THUẦN.

	Tắc = ĐANG có tờ xếp hàng VÀ đã quá lâu không dựng được tờ nào.

	Hai vế phải đi cùng nhau. Chỉ nhìn "lâu rồi không dựng" thì đêm nào
	cũng kêu, vì đêm không ai mua gì. Chỉ nhìn "có tờ xếp hàng" thì lúc
	nào cũng kêu, vì luôn có tờ vừa về chưa tới lượt.
	"""
	try:
		cho = int(so_to_cho or 0)
	except (TypeError, ValueError):
		cho = 0
	try:
		gio = float(gio_ke_tu_lan_dung_cuoi or 0)
	except (TypeError, ValueError):
		gio = 0.0
	return cho > 0 and gio >= float(nguong)


def canh_bao_tac_nhip():
	"""Nhịp ngày: nhịp dựng chứng từ mà tắc thì gửi thư, đừng để im.

	VÌ SAO CÓ HÀM NÀY
	-----------------
	Ngày 26/08/2026 lúc 16h28, kịch bản dựng chứng từ trên site bị tắt, và
	bản thay thế trong mã nguồn thì chưa được khai vào bộ lập lịch. Bước
	kéo vẫn chạy đều nên bảng hoá đơn điện tử vẫn đầy lên mỗi 15 phút,
	nhìn vào đâu cũng thấy "đang chạy".

	NĂM NGÀY sau anh Việt mới phát hiện, và phát hiện bằng cách ngồi so
	tay một tờ của Tác Khí Việt trên trang m-invoice với màn hoá đơn mua
	hàng. 69 tờ hoá đơn mua đứng ngoài sổ suốt thời gian đó.

	Không lớp nào kêu lên, vì không lớp nào có việc kêu. Error Log thì im
	(nhịp có chạy đâu mà lỗi), `con_sot` thì có nhưng phải mở ra mới thấy.

	Hàm này là cái lớp còn thiếu: nó không sửa gì cả, nó chỉ la lên.
	"""
	try:
		if not frappe.db.exists("DocType", DT_HD):
			return
		cho = frappe.db.count(DT_HD, {
			"da_tao_chung_tu": 0, "loai": LOAI_VAO,
			"ngay_lap": ["is", "set"],
		})
		lan_cuoi = frappe.db.get_value(
			PI, {"custom_minvoice_id": ["is", "set"]}, "creation",
			order_by="creation desc")
		gio = 999.0
		if lan_cuoi:
			gio = (
				frappe.utils.now_datetime() - frappe.utils.get_datetime(lan_cuoi)
			).total_seconds() / 3600.0
		# HAI CHUYỆN KHÁC HẲN NHAU, MỘT LÁ THƯ
		#
		# Tắc nhịp là thiếu chứng từ. Trùng là THỪA chứng từ. Ngày 31/08/2026
		# gặp cả hai trong một buổi sáng, và cái thừa nguy hơn: thiếu thì kế
		# toán tự thấy vì hoá đơn không có trong sổ, còn thừa thì nằm im
		# trong danh sách trông y như thật, ghi sổ xong là mua vào đếm hai lần.
		trung = _dem_trung()
		tac = nhip_da_tac(cho, gio)
		if not tac and not cint(trung.get("so_to_thua")):
			return
		phan = []
		if tac:
			phan.append(
				"<p><b>Nhịp dựng chứng từ đang tắc.</b> Đang có <b>%s</b> hoá "
				"đơn điện tử đầu vào xếp hàng mà <b>%s tiếng</b> nay hệ không "
				"dựng thêm được chứng từ nào.</p>"
				"<p>Mở màn Hoá đơn mua hàng trên Desk, bấm nút "
				"<b>Đồng bộ M-Invoice</b>. Vẫn không nhúc nhích thì báo anh "
				"Việt, nhiều khả năng nhịp tự động đã tắt.</p>" % (cho, int(gio))
			)
		if cint(trung.get("so_to_thua")):
			phan.append(
				"<p><b>Có chứng từ trùng.</b> %s tờ hoá đơn điện tử đang có "
				"nhiều hơn một chứng từ trỏ về, thừa <b>%s tờ</b>.</p>"
				"<p>ĐỪNG GHI SỔ khi còn trùng, ghi sổ là mua vào đếm hai lần. "
				"Giữ tờ dựng trước, tick <b>Đã huỷ</b> cho tờ sau. Các tờ đang "
				"trùng: %s.</p>"
				% (
					trung.get("so_nhom"),
					trung.get("so_to_thua"),
					", ".join(
						" và ".join(n.get("ten") or [])
						for n in (trung.get("ds") or [])[:10]
					) or "(xem màn Còn sót)",
				)
			)
		frappe.sendmail(
			recipients=[EMAIL_KE_TOAN],
			subject=(
				"Hoá đơn điện tử: %s"
				% (" và ".join(
					(["nhịp dựng chứng từ đang tắc"] if tac else [])
					+ (["có chứng từ trùng"] if cint(trung.get("so_to_thua")) else [])
				))
			),
			message=_khung_chuong("".join(phan)),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(),
			"minvoice_chung_tu: chuong bao tac nhip")


def _khung_chuong(than):
	"""Boc thu chuong bao vao khuon thu chung. Hong thi gui than thu tho."""
	try:
		from vagabond import thu_khung as _tk

		return _tk.khung("Hoá đơn điện tử đầu vào cần xem ngay", than, chan="noi_bo", nhan="Chuông báo")
	except Exception:
		return than

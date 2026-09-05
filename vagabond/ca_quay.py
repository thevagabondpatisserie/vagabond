# -*- coding: utf-8 -*-
"""Ca làm việc tại quầy: mở ca, chốt ca mù, đối soát từng phương thức.

Vì sao có tệp này
-----------------
Trước giờ "chốt ca" chỉ là một BẢNG BÁO CÁO (`ban_hang.pos_chot_ca`): máy
cộng doanh thu trong ngày cho thu ngân nhìn, nhìn xong là hết, không lưu
lại gì. Không có tiền lẻ đầu ca, không có số thu ngân tự đếm, nên khi két
lệch thì không truy được lệch từ ca nào, và tiền mặt bàn giao về quỹ không
có chứng từ gốc để đối chiếu.

Anh Việt 20/08/2026: cần luồng dòng tiền chặt từ Mở ca tới Bàn giao tiền
cho kế toán. Tệp này lo nửa đầu: ca. Nửa sau (phiếu nộp quỹ, bảng kê mệnh
giá, ký hai bên) nằm ở `nop_quy.py`.

Ba nguyên tắc
-------------
Một, ĐẾM MÙ. Lúc chốt ca thu ngân chỉ thấy các ô trống để gõ số mình đếm
được theo từng phương thức, KHÔNG thấy số máy. Cho thấy số máy trước là
mời người ta gõ lại đúng số đó, và phép đối soát thành vô nghĩa.

Hai, số máy chốt tại thời điểm chốt. Doanh thu hệ thống của ca đọc từ
hoá đơn quầy (`vgb_quay`, `vgb_pt_thanh_toan`, giờ tạo nằm trong khoảng
mở tới chốt), tính xong GHI CỨNG vào dòng ca. Không tính lại lúc xem, vì
hoá đơn có thể bị sửa sau đó bằng OTP quản lý, mà biên bản thì phải giữ
đúng con số tại thời khắc hai bên nhìn nhau.

Ba, tiền mặt là phương thức duy nhất mang tiền lẻ đầu ca. Phải có trong
két = tiền lẻ đầu ca + doanh thu tiền mặt. Các phương thức khác (chuyển
khoản, thẻ, ví) không có khái niệm đầu ca.

Lệch ca thuộc về ai
-------------------
Lệch bắt ở đây là lệch CỦA CA: giữa số thu ngân đếm và số máy ghi nhận
trong đúng khoảng giờ người đó đứng quầy. Lệch lúc bàn giao tiền về quỹ là
chuyện khác, bắt ở `nop_quy.py`. Tách hai tầng để lệch do bán hàng và lệch
do vận chuyển tiền không trộn vào nhau.
"""

import json

import frappe
from frappe.utils import cint, flt, get_datetime, now_datetime, nowdate

CA = "Vagabond Ca Quay"
DONG = "Vagabond Ca Quay Dong"

TT_DANG_MO = "Đang mở"
TT_DA_CHOT = "Đã chốt"
TT_DA_NOP = "Đã nộp quỹ"

TIEN_MAT = "Tiền mặt"

# Lệch dưới mức này coi như tròn số, không bắt gõ lý do. 1.000đ vì tiền
# mặt Việt Nam không có tờ nhỏ hơn thực tế lưu thông ở quầy bánh.
NGUONG_LECH = 1000.0


# ============================================================ phép THUẦN
#
# Không chạm Frappe nên kiểm thử được không cần site.


def ghep_doi_soat(pt_may, pt_dem, tien_le_dau_ca=0.0, so_bill=None):
	"""Ghép số máy và số đếm thành bảng đối soát từng phương thức. THUẦN.

	`pt_may` và `pt_dem` là dict tên phương thức sang số tiền. Lấy HỢP của
	hai tập tên: máy có mà thu ngân không đếm thì đếm coi như 0 (thiếu cả
	dòng), thu ngân đếm ra tiền ở phương thức máy không ghi nhận thì máy
	coi như 0 (thừa không rõ nguồn) - cả hai đều phải lộ ra, không được
	nuốt.

	Chỉ dòng Tiền mặt được cộng tiền lẻ đầu ca vào cột phải có.
	"""
	tien_le_dau_ca = flt(tien_le_dau_ca)
	ten = sorted(set(list(pt_may or {}) + list(pt_dem or {})))
	# Tiền mặt luôn đứng đầu bảng: đó là dòng có tiền lẻ đầu ca và là dòng
	# hay lệch nhất, người đọc tìm nó trước tiên.
	ten.sort(key=lambda t: (0 if t == TIEN_MAT else 1, t))
	ra = []
	for t in ten:
		may = flt((pt_may or {}).get(t))
		dem = flt((pt_dem or {}).get(t))
		phai_co = may + (tien_le_dau_ca if t == TIEN_MAT else 0.0)
		ra.append({
			"phuong_thuc": t,
			"so_bill": cint((so_bill or {}).get(t)),
			"may": may,
			"phai_co": phai_co,
			"dem": dem,
			"lech": dem - phai_co,
		})
	return ra


def tong_lech(bang):
	"""Tổng lệch tuyệt đối của cả bảng. THUẦN."""
	return sum(abs(flt(d.get("lech"))) for d in bang or [])


def can_ly_do(bang, nguong=NGUONG_LECH):
	"""Ca này có bắt buộc gõ lý do không. THUẦN.

	Xét TỪNG dòng chứ không xét tổng: thiếu 500k tiền mặt mà thừa 500k
	chuyển khoản thì tổng bằng 0 nhưng vẫn là hai chuyện phải giải thích.
	"""
	return any(abs(flt(d.get("lech"))) >= flt(nguong) for d in bang or [])


def loc_trong_ket(pt, ngoai_ket):
	"""Tách doanh thu thành phần NẰM TRONG KÉT và phần không. THUẦN.

	Anh Việt 01/09/2026 mở ca cho Sales Online, và chỗ này lộ ra một lỗi có
	sẵn từ trước: bảng đối soát ca gom MỌI phương thức, kể cả tiền bên thứ
	ba đang giữ.

	Grab Dine-Out thì Grab giữ tới hôm sau mới trả. Công nợ thì khách còn
	nợ. Hàng tặng thì không bao giờ có tiền. Ba loại đó KHÔNG nằm trong két
	lúc thu ngân đếm, nên đưa vào bảng đối soát là bắt người ta gõ 0 rồi máy
	báo thiếu đúng bằng số đó, ca nào cũng lệch, ca nào cũng phải bịa một
	lý do. Ở quầy thì phiền, ở Sales Online thì hỏng hẳn vì phần lớn doanh
	thu là tiền các sàn giữ.

	Màn Chốt ca cũ đã tách đúng từ lâu (`ban_hang.pos_chot_ca`), chỉ có ca
	là chưa. Đây là gom về một luật (QT-19).

	Trả (trong_ket, ngoai_ket_chi_tiet), cả hai đều là dict tên sang tiền.
	"""
	kho = set(ngoai_ket or [])
	trong, ngoai = {}, {}
	for ten, so in (pt or {}).items():
		if ten in kho:
			ngoai[ten] = flt(so)
		else:
			trong[ten] = flt(so)
	return trong, ngoai


def doc_so_dem(tho):
	"""Đọc chuỗi JSON số đếm của thu ngân thành dict sạch. THUẦN.

	Nhận cả dict lẫn chuỗi JSON. Số âm là gõ nhầm, chặn thẳng ở đây chứ
	không đợi ra bảng đối soát rồi mới thấy số kỳ dị.
	"""
	if isinstance(tho, str):
		tho = json.loads(tho or "{}")
	ra = {}
	for k, v in (tho or {}).items():
		t = str(k or "").strip()
		if not t:
			continue
		tien = flt(v)
		if tien < 0:
			raise ValueError("Số đếm của %s là số âm." % t)
		ra[t] = tien
	return ra


# ========================================================= chạm vào hệ


def _kiem_quyen():
	from vagabond.ban_hang import _kiem_quyen as kq

	kq()


def _co_quay(diem):
	"""Điểm bán này có quầy tiền mặt không. Rỗng hoặc lạ thì coi như không."""
	try:
		from vagabond import diem_ban

		d = diem_ban.theo_ma(str(diem or "").strip().upper())
		return bool((d or {}).get("quay"))
	except Exception:
		return False


def _ngoai_ket():
	"""Tên các phương thức KHÔNG mang tiền vào két lúc chốt ca."""
	try:
		from vagabond import pt_thanh_toan

		return (set(pt_thanh_toan.chua_ve_tien())
			| set(pt_thanh_toan.ve_sau())
			| set(pt_thanh_toan.khong_thu())
			# Tiền đã về rồi nhưng về hôm khác (khách đặt bánh ổ trả trước).
			# Ngày giao có hoá đơn mà không có đồng nào vào két, để trong
			# bảng đối soát thì thu ngân bị đòi một khoản đã nộp hôm trước.
			| set(pt_thanh_toan.thu_ngay_khac()))
	except Exception:
		return set()


def _pt_cua_diem(diem):
	"""Danh sách phương thức để vẽ ô đếm mù cho MỘT điểm bán.

	Điểm có quầy thì lấy bộ phương thức tại quầy. Điểm không quầy (Sales
	Online) mà lấy bộ đó thì màn đếm mù bày ra Thẻ Payoo, Thẻ ShinhanBank,
	Grab Dine-Out - những thứ điểm đó không có - và thiếu các phương thức
	app mà điểm đó dùng thật. Mỗi dòng thừa thiếu là một dòng lệch.

	Cuối cùng bỏ các phương thức không mang tiền vào két ra, vì thu ngân
	không đếm được thứ mình không cầm.
	"""
	from vagabond import pt_thanh_toan

	try:
		if _co_quay(diem):
			pt = list(pt_thanh_toan.ten_quay())
		else:
			pt = list(pt_thanh_toan.ten_online())
	except Exception:
		pt = [TIEN_MAT]
	kho = _ngoai_ket()
	pt = [t for t in pt if t not in kho]
	# Tien mat luon con lai trong danh sach du Cai dat co go the nao: do la
	# dong duy nhat mang tien le dau ca, thieu no thi ca khong doi soat duoc.
	if TIEN_MAT not in pt:
		pt.insert(0, TIEN_MAT)
	return pt


def _ca_dang_mo(quay):
	"""Tên ca đang mở của một quầy, hoặc None."""
	return frappe.db.get_value(
		CA, {"quay": quay, "trang_thai": TT_DANG_MO}, "name"
	)


def _doanh_thu_he_thong(diem, tu_luc, den_luc):
	"""Doanh thu hệ thống theo phương thức trong khoảng của ca.

	`diem` là MÃ ĐIỂM BÁN chứ không phải mã quầy. Với điểm có quầy hai cái
	đó bằng nhau, với Sales Online thì mã điểm là SALES còn ô `vgb_quay`
	trên hoá đơn để TRỐNG - đó là quy ước cũ của hệ, báo cáo và đối soát
	đều dựa vào nó nên không đổi được.

	VÌ THẾ KHÔNG ĐƯỢC LỌC BẰNG `vgb_quay = diem`. Lọc như vậy thì với Sales
	Online kết quả ra RỖNG, và bảng đối soát sẽ báo toàn bộ tiền thu ngân
	đếm được là "tiền thừa không rõ nguồn". Dùng `_loc_diem_ban` của
	ban_hang, cùng phép lọc mà màn Chốt ca cũ đang dùng (QT-19).

	Nạp ban_hang TRONG hàm chứ không ở đầu tệp: ban_hang mở đầu bằng
	`import requests`, đặt ở đầu tệp là cả bộ kiểm thử tầng khung đỏ trên
	máy CI tay không. Bài học ba ca đỏ ngày 20/08/2026.

	MỐC THỜI GIAN khác nhau theo loại điểm:

	  - Điểm có quầy: giờ TẠO hoá đơn, vì bill quầy sinh ra ngay lúc tính
	    tiền, và ca là một khoảng giờ có thể vắt qua nửa đêm.
	  - Điểm không quầy: NGÀY hoá đơn. Đơn của Sales Online về theo nhịp
	    đồng bộ, giờ tạo là giờ MÁY KÉO VỀ chứ không phải giờ bán. Lọc theo
	    giờ tạo thì một ca mở 8h sẽ nuốt cả đơn hôm qua vừa đồng bộ lúc
	    8h05, và bỏ sót đơn bán lúc 21h55 chưa kịp về. Phiếu nộp quỹ đường
	    NGÀY cũng đọc theo ngày, để hai bên nói cùng một con số.

	Bỏ bill huỷ (không phải doanh thu) và bill tạm tính (chưa chốt tiền).
	"""
	from vagabond import ban_hang as _bh

	loc = _bh._loc_diem_ban(str(diem or "").strip().upper())
	if loc is None:
		frappe.throw("Mã điểm bán %s không có trong danh sách điểm bán." % diem)
	loc["docstatus"] = ["<", 2]
	if _co_quay(diem):
		loc["creation"] = ["between", [str(tu_luc), str(den_luc)]]
	else:
		loc["posting_date"] = [
			"between",
			[str(get_datetime(tu_luc).date()), str(get_datetime(den_luc).date())],
		]
	ds = frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=["name", "grand_total", "vgb_pt_thanh_toan", "vgb_tam_tinh", "vgb_huy"],
		limit_page_length=0,
	)
	# Mot don tra bang NHIEU phuong thuc thi khong duoc don ca to vao mot
	# ten (anh Viet 01/09/2026). Don 92857 ngay 31/08 la vi du that: 2 trieu
	# tien mat cong 225.000 quet the. Don ca to vao "Tien mat" thi ket cuoi
	# ca lech dung 225.000 ma khong ai truy ra, vi so noi la tien mat.
	#
	# Chi doc bang con cho nhung to CO dong; to mot phuong thuc van di
	# nguyen duong cu, khong them mot vong doc nao.
	from vagabond import thanh_toan_nhieu as ttn

	pt, so_bill = {}, {}
	con_lam = [r for r in ds
		if not (cint(r.get("vgb_huy")) or cint(r.get("vgb_tam_tinh")))]
	nhieu = {}
	try:
		nhieu = ttn.bang_dong_cua([r["name"] for r in con_lam])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ca_quay: doc dong thanh toan")
	for r in con_lam:
		tach = ttn.tach_theo_pt(nhieu.get(r["name"]) or [], flt(r.get("grand_total")))
		if not tach:
			t = (r.get("vgb_pt_thanh_toan") or "").strip() or "Chưa rõ"
			tach = {t: flt(r.get("grand_total"))}
		# So BILL dem theo phuong thuc CHINH, khong dem moi dong mot lan:
		# mot to tra hai duong van la MOT bill, dem hai lan thi tong so bill
		# cua ca lon hon so to that va thu ngan tuong minh sot phieu.
		chinh = ttn.chinh_cua(nhieu.get(r["name"]) or []) \
			or (r.get("vgb_pt_thanh_toan") or "").strip() or "Chưa rõ"
		so_bill[chinh] = so_bill.get(chinh, 0) + 1
		for ten, so in tach.items():
			ten = (ten or "").strip() or "Chưa rõ"
			pt[ten] = pt.get(ten, 0.0) + flt(so)
			so_bill.setdefault(ten, 0)
	# Tiền khách TRẢ TRƯỚC cho phiếu đặt bánh ổ (anh Việt chốt 05/09/2026).
	#
	# Ngày khách đặt, tiền vào két nhưng KHÔNG có hoá đơn nào, vì hoá đơn
	# VAT xuất vào ngày giao. Không cộng đoạn này vào thì két thừa đúng bằng
	# số tiền đó và không dòng nào trên bảng đối soát giải thích được, ca nào
	# có đơn đặt bánh là ca đó lệch.
	#
	# Chiều ngược lại đã xử lý ở chỗ khác: tờ hoá đơn ngày giao mang phương
	# thức "Trả trước" thuộc nhóm TIEN_NGAY_KHAC, và `_ngoai_ket()` đã kể
	# nhóm đó nên nó rơi khỏi bảng đối soát két. Nhờ vậy tiền của một đơn
	# chỉ vào két ĐÚNG MỘT LẦN, ở ngày thu.
	#
	# VÌ SAO Ở ĐÂY NUỐT LỖI ĐƯỢC, mà chỗ đo giữ chỗ thì không (Codex hỏi ở
	# PR #197): đọc hỏng ở đây làm bảng đối soát THIẾU một dòng, thu ngân
	# thấy lệch và báo ngay, không ai mất gì. Đọc hỏng ở cột giữ chỗ mà nuốt
	# lỗi thì bảng ghi 0 và NHẢ bánh đã giữ của khách ra bán tiếp, im lặng.
	# Nuốt lỗi chỉ an toàn khi hậu quả của nó tự lộ ra.
	try:
		from vagabond import dat_banh

		ung = dat_banh.thu_ung_truoc(
			diem, tu_luc, den_luc, theo_ngay=not _co_quay(diem)
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ca_quay: doc thu ung truoc")
		ung = {}
	for ten, so in (ung or {}).items():
		ten = (ten or "").strip() or "Chưa rõ"
		pt[ten] = pt.get(ten, 0.0) + flt(so)
		so_bill.setdefault(ten, 0)
	return pt, so_bill


@frappe.whitelist()
def tinh_trang(quay):
	"""Màn quầy hỏi: quầy này đang có ca mở không.

	Trả về đủ để vẽ dòng trạng thái, nhưng KHÔNG trả doanh thu hệ thống:
	số đó chỉ lộ ra sau khi thu ngân đã gõ số đếm (đếm mù).
	"""
	_kiem_quyen()
	quay = (quay or "").strip()
	# Danh sach phuong thuc cua DIEM BAN nay: man chot ca ve moi phuong thuc
	# mot o trong de thu ngan go so dem. Chi tra TEN, khong tra so lieu nao.
	pt = _pt_cua_diem(quay)
	ten = _ca_dang_mo(quay)
	if not ten:
		return {"dang_mo": 0, "phuong_thuc": pt}
	d = frappe.db.get_value(
		CA, ten, ["name", "mo_luc", "nguoi_mo", "tien_le_dau_ca"], as_dict=True
	)
	return {
		"dang_mo": 1,
		"ma": d.name,
		"mo_luc": str(d.mo_luc),
		"nguoi_mo": d.nguoi_mo,
		"tien_le_dau_ca": flt(d.tien_le_dau_ca),
		"phuong_thuc": pt,
	}


@frappe.whitelist()
def mo_ca(quay, tien_le_dau_ca=0):
	"""Mở ca: khai tiền lẻ đầu ca cho một quầy.

	Một quầy chỉ một ca mở tại một thời điểm. Quên chốt ca hôm qua thì
	phải chốt nó trước, không cho mở đè: mở đè là bill lọt vào khe giữa
	hai ca, không ca nào nhận.
	"""
	_kiem_quyen()
	quay = (quay or "").strip()
	if not quay:
		frappe.throw("Thiếu mã điểm bán.")
	tien_le = flt(tien_le_dau_ca)
	if tien_le < 0:
		frappe.throw("Tiền lẻ đầu ca không thể là số âm.")
	dang = _ca_dang_mo(quay)
	if dang:
		frappe.throw(
			"Điểm bán này đang có ca %s chưa chốt (mở lúc %s). Chốt ca đó "
			"trước rồi mới mở ca mới."
			% (dang, frappe.db.get_value(CA, dang, "mo_luc"))
		)
	doc = frappe.get_doc({
		"doctype": CA,
		"quay": quay,
		"ngay": nowdate(),
		"trang_thai": TT_DANG_MO,
		"mo_luc": now_datetime(),
		"nguoi_mo": frappe.session.user,
		"tien_le_dau_ca": tien_le,
	})
	doc.insert(ignore_permissions=True)
	# CHAN HAI NGUOI CUNG MO MOT LUC. Phep kiem o tren doc truoc khi ghi, nen
	# hai nguoi bam cach nhau mot giay thi ca hai deu thay "chua co ca nao"
	# va ra HAI ca cung mo. Voi mot quay vat ly thi hiem, vi chi mot may dung
	# do. Voi Sales Online thi that: nhieu ban cung mo app tren nhieu may.
	# Hai ca chong nhau la doanh thu duoc dem hai lan.
	#
	# Dem lai SAU khi ghi, con hon mot ca thi nem loi - Frappe cuon nguoc ca
	# luot ghi khi co loi nem ra truoc luc commit, nen ban ghi vua tao bien
	# mat theo. Nguoi bam sau nhan duoc loi, nguoi bam truoc giu ca.
	so_mo = frappe.db.count(CA, {"quay": quay, "trang_thai": TT_DANG_MO})
	if cint(so_mo) > 1:
		frappe.throw(
			"Vừa có người khác mở ca cho điểm bán này cùng lúc. Tải lại màn "
			"hình để thấy ca đang mở, đừng mở thêm ca thứ hai."
		)
	frappe.db.commit()
	return {"ma": doc.name, "mo_luc": str(doc.mo_luc), "tien_le_dau_ca": tien_le}


@frappe.whitelist()
def chot_ca(quay, dem, ly_do_lech="", ghi_chu=""):
	"""Chốt ca mù: nhận số thu ngân đếm, so với số máy, ghi cứng biên bản.

	`dem` là JSON tên phương thức sang số tiền thu ngân đếm được. Máy tính
	doanh thu hệ thống TẠI ĐÂY, sau khi đã nhận số đếm, nên thu ngân không
	có cách nào nhìn thấy số máy trước lúc gõ.

	Có dòng lệch từ 1.000đ mà không gõ lý do thì máy trả bảng đối soát về
	kèm cờ `can_ly_do`, KHÔNG chốt. Màn hình cho gõ lý do rồi gọi lại.
	"""
	_kiem_quyen()
	quay = (quay or "").strip()
	ten = _ca_dang_mo(quay)
	if not ten:
		frappe.throw("Điểm bán này không có ca nào đang mở.")
	try:
		so_dem = doc_so_dem(dem)
	except ValueError as e:
		frappe.throw(str(e))
	if not so_dem:
		frappe.throw("Chưa có số đếm nào. Gõ số tiền đếm được của từng phương thức, kể cả bằng 0.")

	doc = frappe.get_doc(CA, ten)
	luc = now_datetime()
	pt_may, so_bill = _doanh_thu_he_thong(quay, doc.mo_luc, luc)
	# Tien bên thứ ba đang giữ (Grab Dine-Out), khách còn nợ (Công nợ) và
	# hàng tặng KHÔNG nằm trong két, nên không đưa vào bảng đối soát. Bày ra
	# riêng để quản lý biết còn bao nhiêu phải đi đòi.
	pt_may, pt_ngoai = loc_trong_ket(pt_may, _ngoai_ket())
	bang = ghep_doi_soat(pt_may, so_dem, doc.tien_le_dau_ca, so_bill)

	if can_ly_do(bang) and not (ly_do_lech or "").strip():
		return {
			"can_ly_do": 1,
			"bang": bang,
			"ngoai_ket": pt_ngoai,
			"tong_lech": tong_lech(bang),
			"nhac": (
				"Có phương thức lệch từ %s đồng. Gõ lý do (đếm sót, trả nhầm "
				"tiền thừa, khách chuyển thiếu...) rồi bấm chốt lại."
				% int(NGUONG_LECH)
			),
		}

	doc.chot_luc = luc
	doc.nguoi_chot = frappe.session.user
	doc.trang_thai = TT_DA_CHOT
	doc.ly_do_lech = (ly_do_lech or "").strip()
	doc.ghi_chu = (ghi_chu or "").strip()
	doc.set("dong", [])
	for d in bang:
		doc.append("dong", d)
	doc.tong_may = sum(flt(d["may"]) for d in bang)
	doc.tong_dem = sum(flt(d["dem"]) for d in bang)
	doc.tong_lech = sum(flt(d["lech"]) for d in bang)
	# Số tiền mặt đếm được lúc chốt: chính là số phiếu nộp quỹ sẽ kỳ vọng.
	doc.tien_mat_dem = flt(so_dem.get(TIEN_MAT))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"ma": doc.name,
		"da_chot": 1,
		"bang": bang,
		"ngoai_ket": pt_ngoai,
		"tong_lech": tong_lech(bang),
		"tien_mat_dem": flt(doc.tien_mat_dem),
	}


@frappe.whitelist()
def danh_sach(quay=None, tu_ngay=None, den_ngay=None, trang_thai=None, so_dong=200):
	"""Danh sách ca, cho màn lịch sử và cho phiếu nộp quỹ chọn ca."""
	_kiem_quyen()
	loc = {}
	if quay:
		loc["quay"] = quay
	if trang_thai:
		loc["trang_thai"] = trang_thai
	if tu_ngay and den_ngay:
		loc["ngay"] = ["between", [tu_ngay, den_ngay]]
	elif tu_ngay:
		loc["ngay"] = [">=", tu_ngay]
	ds = frappe.get_all(
		CA,
		filters=loc,
		fields=["name", "quay", "ngay", "trang_thai", "mo_luc", "chot_luc",
			"tien_le_dau_ca", "tien_mat_dem", "tong_may", "tong_dem",
			"tong_lech", "nguoi_mo", "nguoi_chot", "phieu_nop"],
		order_by="mo_luc desc",
		limit=cint(so_dong) or 200,
	)
	return {"ds": ds}


@frappe.whitelist()
def chi_tiet(ma):
	"""Một ca, đủ bảng đối soát từng phương thức."""
	_kiem_quyen()
	doc = frappe.get_doc(CA, ma)
	return {
		"ma": doc.name,
		"quay": doc.quay,
		"ngay": str(doc.ngay),
		"trang_thai": doc.trang_thai,
		"mo_luc": str(doc.mo_luc or ""),
		"chot_luc": str(doc.chot_luc or ""),
		"nguoi_mo": doc.nguoi_mo,
		"nguoi_chot": doc.nguoi_chot,
		"tien_le_dau_ca": flt(doc.tien_le_dau_ca),
		"tien_mat_dem": flt(doc.tien_mat_dem),
		"tong_may": flt(doc.tong_may),
		"tong_dem": flt(doc.tong_dem),
		"tong_lech": flt(doc.tong_lech),
		"ly_do_lech": doc.ly_do_lech or "",
		"ghi_chu": doc.ghi_chu or "",
		"phieu_nop": doc.phieu_nop or "",
		"bang": [
			{
				"phuong_thuc": d.phuong_thuc, "so_bill": cint(d.so_bill),
				"may": flt(d.may), "phai_co": flt(d.phai_co),
				"dem": flt(d.dem), "lech": flt(d.lech),
			}
			for d in doc.dong
		],
	}

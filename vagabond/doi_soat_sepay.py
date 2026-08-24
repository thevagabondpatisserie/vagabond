"""Tầng đối soát SePay dùng chung cho MỌI màn.

Anh Việt chốt 24/08/2026: *"Tất cả các phần đối chiếu SePay này phải làm ở
cấp độ backend cho mọi màn cần đối soát SePay, gồm đối soát tự động và nút
đối soát thủ công ở kế bên."*


VÌ SAO PHẢI CÓ TỆP NÀY
======================

Trước v294, mười đường đối soát rải khắp bảy mô đun, và BẢY phép "một dòng
sao kê có khớp phiếu này không" được viết lại độc lập, mỗi phép sai một kiểu:

    hoan_tien.tim_ma_hoa_don      không gọt, chặn chữ số CẢ HAI đầu
    hoan_tien.khop_giao_dich      có gọt,    chặn chữ số CHỈ PHÍA SAU
    de_nghi_chi.khop_noi_dung     có gọt,    KHÔNG chặn đầu nào
    cong_no._sepay_theo_ma_cn     có gọt,    dựa vào độ dài regex
    ho_so_tt._sepay_theo_ma_app   có gọt,    dựa vào độ dài regex
    ban_hang._sepay_theo_don      không gọt, chặn cả hai đầu
    ban_hang._sepay_theo_ma_bill  không gọt, KHÔNG chặn gì

Bốn hàm gọt chuỗi làm y hệt một việc, mang bốn cái tên khác nhau: `_got`,
`_chuan_ma`, `_tran`, và một lambda `sach` viết chen giữa hàm.

Chính `hoan_tien.chon_ma_khop` ra đời ngày 16/08/2026 vì hai đường trong CÙNG
một mô đun đã lệch nhau, và chú thích của nó viết "Mot phep, mot cho". Bài học
đó chưa được mang sang sáu mô đun còn lại. Tệp này mang nó sang.


BA DÒNG SAO KÊ THẬT ĐÃ QUYẾT ĐỊNH THIẾT KẾ
==========================================

Ngày 24/08/2026, ba phiếu hoàn tiền của đơn Pancake đã huỷ:

    "MBCT THE VAGABOND HOAN TIEN DH 92156 D2HLVNHF/428417"
    "THE VAGABOND HOAN TIEN DH 92252"
    "MBCT VAGABOND HOAN TIEN DON HANG 92245 D237BVMB/870581"

App bảo kế toán gõ "THE VAGABOND HOAN TIEN 92245". Chị Dung gõ "VAGABOND HOAN
TIEN DON HANG 92245": bỏ chữ THE, thêm hai chữ DON HANG. Ngân hàng chèn thêm
"MBCT" ở đầu và mã tham chiếu ở cuối.

Kết luận rút ra, và nó là gốc của cả tệp này:

  1. Kế toán KHÔNG gõ y nguyên chuỗi app đưa, và sẽ không bao giờ gõ y nguyên.
     Dò theo CẢ CÂU là dò theo một thứ không ổn định.
  2. Thứ DUY NHẤT ổn định trong cả ba dòng là con số mã đơn.
  3. Nên phải dò theo MÃ TRẦN. Mà dò mã trần chỉ an toàn khi chặn chữ số CẢ
     HAI ĐẦU, nếu không "92252" sẽ dính vào một dòng chứa "192252".

Phiếu 92245 chính vì phép cũ dò cả câu nên máy trượt, và chị Dung phải bấm
nút Khớp SePay thủ công lúc 14:31 cùng ngày.


SỐ TIỀN KHÔNG BAO GIỜ ĐỦ ĐỂ MÁY TỰ QUYẾT
========================================

Trước v294 có ba ngưỡng so tiền khác nhau, và `sepay.tim_gd_vao` còn dò THUẦN
theo số tiền với dung sai 2 phần trăm - đơn 700.000 đ chấp nhận lệch 14.000 đ.

Ở đây số tiền chỉ làm hai việc: XÁC NHẬN sau khi mã đã khớp, và XẾP THỨ TỰ ứng
viên cho người nhìn. Không có mã thì máy trả về "không", không đoán.
"""

import re

import frappe
from frappe.utils import cint, flt

BT = "Bank Transaction"

# Ba ket qua cua mot phep xet. Chuoi chu khong phai so, de doc log ra la hieu.
KHOP = "khop"
XEM_LAI = "xem_lai"
KHONG = "khong"

# Lech bao nhieu dong thi van coi la dung so tien. Mot dong, khong phai phan
# tram: ngan hang khong lam tron tien Viet.
DUNG_SAI = 1.0


# --------------------------------------------------------- lớp 1 và 2: THUẦN
#
# Nằm ở `vagabond/khop_sao_ke.py`, không chạm Frappe. Nhập lại vào đây để mọi
# chỗ gọi cũ chỉ cần biết một cái tên.

from vagabond.khop_sao_ke import (  # noqa: E402,F401
	DUNG_SAI,
	KHONG,
	KHOP,
	XEM_LAI,
	co_ma,
	got,
	tien_vn,
	tim_ma,
	xep_ung_vien,
	xet,
)


# ----------------------------------------------------------- lớp 3: sổ đăng ký
#
# Mỗi mô đun nghiệp vụ khai một BẢN MÔ TẢ rồi cả hệ dùng chung ba cửa ngõ ở
# dưới. Thêm màn mới sau này là thêm một bản mô tả, không viết lại phép khớp
# lần thứ tám.

# Chieu tien.
RA = "ra"
VAO = "vao"

_SO = {}


def khai(loai, doctype, chieu, ma_do, so_tien, dang_cho, khi_khop=None,
		ten_man="", truong_gd="ma_gd", loc_chiem=None,
		truong_nguoi="", truong_luc=""):
	"""Khai một luồng đối soát vào sổ chung.

	  loai       khoa ngan, man hinh goi cua ngo bang khoa nay
	  doctype    doctype cua phieu
	  chieu      RA hoac VAO
	  ma_do      ham nhan doc phieu, tra ve MA de do tren sao ke, rong la bo qua
	  so_tien    ham nhan doc phieu, tra ve so tien phai khop
	  dang_cho   dict loc frappe: phieu nao con dang cho doi soat
	  khi_khop   ham nhan (doc, ma_gd) chay khi khop duoc. Bo trong thi tang
	             nay chi danh dau `truong_gd` chu khong lam gi them.
	  truong_gd  truong luu ma giao dich ngan hang tren phieu
	"""
	_SO[loai] = {
		"doctype": doctype, "chieu": chieu, "ma_do": ma_do, "so_tien": so_tien,
		"dang_cho": dang_cho, "khi_khop": khi_khop, "ten_man": ten_man or loai,
		"truong_gd": truong_gd, "loc_chiem": loc_chiem or {},
		"truong_nguoi": truong_nguoi, "truong_luc": truong_luc,
	}


def _ban(loai):
	b = _SO.get(str(loai or "").strip())
	if not b:
		frappe.throw("Chưa khai luồng đối soát '%s' trong sổ chung." % loai)
	return b


def nap_so():
	"""Nạp mọi bản mô tả. Gọi lười, vì mỗi mô đun lại nhập ngược tệp này."""
	if _SO:
		return
	from vagabond import de_nghi_chi  # noqa: F401
	from vagabond import hoan_tien  # noqa: F401

	if not _SO:
		frappe.throw("Sổ đối soát SePay rỗng: chưa mô đun nào khai luồng của mình.")


def da_chiem(loai, tru_phieu=None):
	"""Mã giao dịch nào đã được một phiếu KHÁC của cùng luồng chiếm.

	Một dòng sao kê là MỘT lần tiền rời hoặc vào tài khoản. Cho hai phiếu
	cùng trỏ vào nó là khai hai lần cho một lần chuyển.

	Cho phép một phiếu giữ lại chính giao dịch của nó (tham số `tru_phieu`),
	để kế toán bấm lại nút Đối soát thì không bị chính mình chặn.
	"""
	b = _ban(loai)
	loc = {b["truong_gd"]: ["!=", ""]}
	# Phieu da huy hay bi tra lai thi NHA giao dich ra, vi tien do hoac chua
	# ra, hoac da duoc thu lai bang mot phieu khac. Moi luong khai bo loc
	# rieng cua no vi moi doctype goi trang thai do mot ten khac.
	loc.update(b.get("loc_chiem") or {})
	if tru_phieu:
		loc["name"] = ["!=", tru_phieu]
	ra = {}
	for r in frappe.get_all(b["doctype"], filters=loc,
			fields=["name", b["truong_gd"]], limit_page_length=0):
		ma = str(r.get(b["truong_gd"]) or "").strip()
		if ma:
			ra.setdefault(ma, r["name"])
	return ra


def dong_sao_ke(chieu, so_ngay=45, tu_ngay=None):
	"""Các dòng sao kê đúng chiều tiền trong khoảng ngày. Chạm hệ."""
	from frappe.utils import add_days, nowdate

	n = max(1, min(cint(so_ngay) or 45, 180))
	moc = str(tu_ngay or "")[:10] or nowdate()
	cot = "withdrawal" if chieu == RA else "deposit"
	ds = frappe.get_all(
		BT,
		filters=[
			["date", "between", [add_days(moc, -n), add_days(moc, 1)]],
			[cot, ">", 0],
			["docstatus", "<", 2],
		],
		fields=["name", "date", "deposit", "withdrawal", "description",
			"reference_number", "bank_account"],
		order_by="date desc", limit_page_length=500,
	)
	for g in ds:
		# Ghep ca hai o lai lam mot chuoi de do: ngan hang doi khi day ma
		# tham chieu sang o rieng chu khong de trong noi dung.
		g["mo_ta"] = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
		g["tien"] = flt(g.get(cot))
	return ds


# ------------------------------------------------------------- ba cửa ngõ chung


@frappe.whitelist()
def tu_dong(loai, ma_phieu=None, so_ngay=45):
	"""Quét sao kê và khớp, cho một phiếu hoặc cho cả mẻ đang chờ.

	Trả về `da_khop`, `xem_lai`, `so_phieu_quet`. Danh sách `xem_lai` là thứ
	người phải nhìn: mã khớp mà tiền lệch, hoặc dòng đã có chủ. Im lặng bỏ
	qua chúng là để phiếu nằm mãi ở trạng thái chờ mà không ai biết vì sao.

	GHI XUỐNG NGAY, TRƯỚC KHI LÀM VIỆC SAU. Bài học của phiếu HT-2026-00899
	ngày 19/08/2026: gộp "đánh dấu đã đối soát" và "sinh chứng từ" vào một
	giao dịch cơ sở dữ liệu thì một lỗi ở bước sau sẽ rollback xoá luôn cái
	dấu vừa ghi, và phiếu nằm mãi ở "Chờ chi" dù tiền đã rời tài khoản. Hai
	sự thật khác hẳn nhau, không được gộp làm một.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	nap_so()
	b = _ban(loai)

	loc = dict(b["dang_cho"])
	if ma_phieu:
		loc = {"name": ma_phieu}
	phieu = frappe.get_all(b["doctype"], filters=loc, fields=["name"],
		limit_page_length=0)
	cho = []
	for p in phieu:
		doc = frappe.get_doc(b["doctype"], p["name"])
		ma = str(b["ma_do"](doc) or "").strip()
		if not ma:
			continue
		cho.append({"doc": doc, "ma": ma, "tien": flt(b["so_tien"](doc))})
	if not cho:
		return {"da_khop": 0, "xem_lai": [], "so_phieu_quet": 0,
			"ghi_chu": "Không có phiếu nào dò được trên sao kê."}

	gds = dong_sao_ke(b["chieu"], so_ngay)
	chiem = da_chiem(loai, tru_phieu=ma_phieu)

	da, xem = 0, []
	for c in cho:
		for g in gds:
			kq, vi_sao = xet(g["mo_ta"], g["tien"], c["ma"], c["tien"],
				chu_cu=chiem.get(g["name"]))
			if kq == KHONG:
				continue
			if kq == XEM_LAI:
				xem.append({
					"phieu": c["doc"].name, "ma_do": c["ma"],
					"giao_dich": g["name"], "ngay": str(g.get("date") or ""),
					"tien_phieu": c["tien"], "tien_dong": g["tien"],
					"vi_sao": vi_sao,
				})
				continue
			frappe.db.set_value(b["doctype"], c["doc"].name, b["truong_gd"], g["name"])
			frappe.db.commit()
			chiem[g["name"]] = c["doc"].name
			da += 1
			if b["khi_khop"]:
				# Boc rieng tung phieu: mot phieu hong khong duoc keo theo ca
				# me dang quet, vi cac phieu kia da duoc danh dau roi.
				try:
					b["khi_khop"](frappe.get_doc(b["doctype"], c["doc"].name), g["name"])
					frappe.db.commit()
				except Exception:
					frappe.db.rollback()
					frappe.log_error(frappe.get_traceback(),
						"doi_soat_sepay: khi_khop loi %s %s" % (loai, c["doc"].name))
			break
	frappe.db.commit()
	return {"da_khop": da, "xem_lai": xem[:50], "so_phieu_quet": len(cho)}


@frappe.whitelist()
def ung_vien(loai, ma_phieu, so_ngay=45, tu_khoa=""):
	"""Các dòng sao kê để NGƯỜI tự chọn, xếp dòng khớp mã lên trước.

	Màn hình không tự quyết. Nó bày ra ứng viên rồi để người đọc mắt và chỉ,
	và tên người chỉ được ghi lại ngay trên phiếu.

	KHÔNG lọc theo số tiền. Lọc theo tiền chính là cái bẫy của bản cũ: ngân
	hàng trừ phí hay kế toán chuyển làm hai lần là đúng dòng cần tìm bị cắt
	mất khỏi danh sách, và người dùng kết luận "không có dòng nào".
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	nap_so()
	b = _ban(loai)
	doc = frappe.get_doc(b["doctype"], ma_phieu)
	ma = str(b["ma_do"](doc) or "").strip()
	tien = flt(b["so_tien"](doc))

	chiem = da_chiem(loai, tru_phieu=ma_phieu)
	tk = str(tu_khoa or "").strip().lower()
	tho = []
	for g in dong_sao_ke(b["chieu"], so_ngay):
		if chiem.get(g["name"]):
			continue
		if tk and tk not in (g["mo_ta"] or "").lower():
			continue
		tho.append({
			"name": g["name"], "date": str(g.get("date") or ""),
			"tien": g["tien"], "mo_ta": (g.get("description") or "").strip(),
			"bank_account": g.get("bank_account"),
		})
	return {
		"rows": xep_ung_vien(tho, ma, tien)[:60],
		"ma_do": ma, "so_tien": tien, "ten_man": b["ten_man"],
		"ma_gd_dang_gan": doc.get(b["truong_gd"]) or "",
		"nhac": ("" if ma else
			"Phiếu này chưa có mã nào để dò, nên hệ thống không xếp được dòng "
			"nào lên trước. Vui lòng đọc nội dung rồi chọn."),
	}


@frappe.whitelist()
def khop_tay(loai, ma_phieu, ma_gd):
	"""Gắn TAY một dòng sao kê vào phiếu, rồi chạy nốt việc sau khớp.

	Đi đến ĐÚNG cái đích của đường tự động, chỉ khác chỗ chọn dòng: ở kia máy
	đọc nội dung, ở đây người nhìn sao kê và chỉ. Nên nó phải làm ĐỦ những
	việc kia làm, không được làm thiếu.

	Lệch tiền thì CẢNH BÁO chứ không chặn: ngân hàng có thể trừ phí, kế toán
	có thể chuyển làm hai lần. Nhưng con số phải được nói ra thành lời.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	nap_so()
	b = _ban(loai)
	doc = frappe.get_doc(b["doctype"], ma_phieu)
	gd = str(ma_gd or "").strip()
	if not gd:
		frappe.throw("Chưa chọn dòng sao kê nào.")

	cot = "withdrawal" if b["chieu"] == RA else "deposit"
	g = frappe.db.get_value(BT, gd,
		["name", "date", "deposit", "withdrawal", "docstatus", "description",
		 "reference_number"], as_dict=True)
	if not g:
		frappe.throw("Không có giao dịch ngân hàng %s. Vui lòng tìm lại." % gd)
	if cint(g["docstatus"]) >= 2:
		frappe.throw("Giao dịch %s đã bị huỷ nên không dùng làm căn cứ được." % gd)
	if flt(g[cot]) <= 0:
		frappe.throw(
			"Giao dịch %s không phải dòng tiền %s. Vui lòng chọn lại."
			% (gd, "ra" if b["chieu"] == RA else "vào")
		)
	chu_cu = da_chiem(loai, tru_phieu=ma_phieu).get(gd)
	if chu_cu:
		frappe.throw(
			"Giao dịch %s đã được phiếu %s dùng rồi. Một lần tiền chỉ ứng với "
			"một phiếu." % (gd, chu_cu)
		)

	tien_phieu = flt(b["so_tien"](doc))
	lech = flt(g[cot]) - tien_phieu

	# Ghi ten NGUOI bam. Day la mot chu ky cua nguoi chu khong phai mot phep
	# may, va ba thang sau ke toan phai tra loi duoc "ai bao dong nay la cua
	# phieu nay". Doctype nao chua co hai o rieng thi ghi vao nhat ky tai
	# lieu, van tra loi duoc cau hoi do.
	ghi = {b["truong_gd"]: gd}
	if b.get("truong_nguoi"):
		ghi[b["truong_nguoi"]] = frappe.session.user
	if b.get("truong_luc"):
		ghi[b["truong_luc"]] = frappe.utils.now_datetime()
	frappe.db.set_value(b["doctype"], ma_phieu, ghi)
	frappe.db.commit()
	if not b.get("truong_nguoi"):
		try:
			frappe.get_doc(b["doctype"], ma_phieu).add_comment(
				"Comment",
				"Khớp SePay thủ công: gắn giao dịch %s, người làm %s."
				% (gd, frappe.session.user),
			)
			frappe.db.commit()
		except Exception:
			pass

	loi = ""
	if b["khi_khop"]:
		try:
			b["khi_khop"](frappe.get_doc(b["doctype"], ma_phieu), gd)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(),
				"doi_soat_sepay: khop_tay khi_khop loi %s %s" % (loai, ma_phieu))
			loi = ("Tiền đã khớp nhưng hệ thống chưa chạy xong bước sau: %s. Vui "
				"lòng bấm lại nút Khớp SePay, nếu vẫn hỏng thì báo bộ phận kỹ thuật."
				% str(frappe.get_traceback()).strip().splitlines()[-1][:200])

	return {
		"ok": 1, "gd": gd, "lech": lech, "loi": loi,
		"so_tien_dong": flt(g[cot]), "so_tien_phieu": tien_phieu,
		"nhac": (
			("Đã khớp. Số tiền trên sao kê lệch %s đ so với phiếu, vui lòng xem "
			 "lại." % tien_vn(abs(lech)))
			if abs(lech) > DUNG_SAI else "Đã khớp dòng sao kê vào phiếu."
		),
	}

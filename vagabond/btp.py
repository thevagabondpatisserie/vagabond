"""Bang BTP banh o - so hoa tam bang trang cua bep.

Bep moi ngay du tru so banh BTP cap 2 (dong lanh, cho finish) du dung cho
2-3 ngay, truoc gio viet whiteboard roi chup gui sales. Tu 01/08 bep nhap
thang vao day tren dien thoai (man hinh /btp), sales thay tuc thi.

So sales can la "CON NHAN" = BTP san - don da nhan ma bep chua finish
(chot voi anh Viet 01/08: tru don cua HOM NAY + 2 ngay ke chua chot so).
Con nhan ve 0 la sales lai khach sang mon con nhieu - dung nhu cach van
hanh cu, chi bo cong chup bang.
"""

import frappe
from frappe.utils import add_days, getdate, now_datetime

from vagabond.giu_vo import don_con_giu_vo
from vagabond.kiem_banh import _co_that, _dang_ma_dung, _tra_anh_ten
from vagabond.lib import cfg, key

SO_NGAY_GIU = 3  # hom nay + 2 ngay ke

# CHI BEP duoc sua so BTP (anh Viet chot 01/08: bep nhap thi bep chiu
# trach nhiem so). Giam doc / System Manager van sua duoc de go roi.
BEP_EMAILS = {
	"djvinci05@gmail.com",  # Duy
	"hieu0703573936@gmail.com",  # Hieu
	"lethilinh051996@gmail.com",  # Linh
	"ngochan41096@gmail.com",  # Han
}


# Vai tro bep - de sau nay them nguoi thi chi can gan role, khoi sua code.
BEP_ROLES = {"Bếp phó", "Bếp trưởng", "System Manager"}


def _duoc_sua_btp():
	user = frappe.session.user
	if user in BEP_EMAILS:
		return True
	return bool(BEP_ROLES & set(frappe.get_roles(user)))


@frappe.whitelist()
def quyen_btp():
	"""Man hinh hoi de biet co mo o sua BTP cho nguoi nay khong."""
	return {"sua": 1 if _duoc_sua_btp() else 0}


def _refill_cua_bang(doc=None):
	"""{mã: {so, tu, den}} refill còn hiệu lực trên bảng BTP (v646)."""
	from vagabond import refill

	doc = doc or frappe.get_single("BTP Banh O")
	return refill.hieu_luc_tu_dong(doc.dong, getdate())


def _giu_ngay_mai(rf=None):
	"""Don giao NGAY MAI (da dat + phat sinh + cho chot) neu so chua chot.

	Y Linh 01/08: sau 12h trua, do decor cho ngay mai khong kip chuan bi
	them - nen don giao ngay mai chi nhan trong pham vi so "du decor".
	v646: đơn của bánh giao trong khoảng refill trừ vào refill, không trừ decor.
	"""
	from vagabond import refill

	giu = {}
	ngay = add_days(getdate(), 1)
	ma_doc = "KB-%s" % ngay
	if not frappe.db.exists("Kiem Banh Ngay", ma_doc):
		return giu
	kb = frappe.get_doc("Kiem Banh Ngay", ma_doc)
	if kb.tinh_trang == "Da chot":
		return giu
	for d in kb.dong:
		if refill.ngay_cua_refill(rf, d.ma_hang, ngay):
			continue
		# v649 Codex #552 vòng 7: bánh bếp làm trước cho đơn ngày mai đã trừ vỏ.
		giu[d.ma_hang] = giu.get(d.ma_hang, 0) + don_con_giu_vo(d)
	return giu


def _giu_theo_ma(rf=None):
	"""Tong (da dat + phat sinh + cho chot) cac ngay CHUA CHOT trong cua so.
	v646: bỏ ngày nằm trong khoảng refill của chính mã đó (trừ vào refill)."""
	from vagabond import refill

	giu = {}
	hom_nay = getdate()
	for i in range(SO_NGAY_GIU):
		ngay = add_days(hom_nay, i)
		ma_doc = "KB-%s" % ngay
		if not frappe.db.exists("Kiem Banh Ngay", ma_doc):
			continue
		kb = frappe.get_doc("Kiem Banh Ngay", ma_doc)
		if kb.tinh_trang == "Da chot":
			continue
		for d in kb.dong:
			if refill.ngay_cua_refill(rf, d.ma_hang, ngay):
				continue
			# v649: vỏ của bánh bếp đã làm (mọi ngày, kể cả làm trước cho ngày
			# tới) đã trừ thẳng vào BTP sẵn; một phép duy nhất don_con_giu_vo.
			giu[d.ma_hang] = giu.get(d.ma_hang, 0) + don_con_giu_vo(d)
	return giu


def chenh_sx(cu, moi):
	"""v649 (Loan Anh đề xuất, anh Việt chọn A 11/11/2026): số bánh bếp làm thêm
	của từng mã giữa bản đang lưu (cu) và bản sắp lưu (moi) của một ngày Kiểm
	bánh. Sửa tăng ra số dương (trừ thêm vỏ), sửa bớt ra số âm (cộng lại vỏ).
	Thuần, không chạm Frappe."""
	def gom(dong):
		ra = {}
		for d in dong or []:
			ma = str((d.get("ma_hang") if hasattr(d, "get") else getattr(d, "ma_hang", "")) or "").strip()
			if not ma:
				continue
			sx = d.get("sx") if hasattr(d, "get") else getattr(d, "sx", 0)
			ra[ma] = ra.get(ma, 0) + int(sx or 0)
		return ra

	a, b = gom(cu), gom(moi)
	ra = {}
	for ma in set(a) | set(b):
		n = b.get(ma, 0) - a.get(ma, 0)
		if n:
			ra[ma] = n
	return ra


def tru_vo_theo_sx(chenh, nguon=None, ly_do=None):
	"""Trừ BTP sẵn và Đủ decor NGAY khi bếp nhập hay sửa ô Bếp làm (v649).

	Một cái bánh bếp làm xong là đã ăn một vỏ BTP đã đủ decor, nên trừ cả hai
	ô theo số làm, không chờ chốt sổ (chốt sổ thôi trừ theo số bán, xem
	kiem_banh.chot_ngay). Bếp đếm lại tủ rồi nhập lại BTP sẵn thì số đếm là gốc
	mới: các lần sửa Bếp làm sau đó mới trừ tiếp.

	Trừ bằng một câu UPDATE cộng dồn trên từng dòng để hai người lưu cùng lúc
	không đè số của nhau, và không kẹp về 0: sửa bớt thì cộng lại đúng phần đã
	trừ. Số âm chỉ là hiển thị 0 (bang_btp) và báo bếp cần đếm lại tủ.
	Mã không có trong bảng BTP thì bỏ qua: không UPDATE, không đổi giờ "BTP
	bếp cập nhật" trên màn (nhập Bếp làm cho bánh khác không phải bếp vừa sửa
	bảng BTP).

	v653 (sự cố Tira 18cm 12/11/2026): khoá đúng các dòng cần trừ (for update)
	để đọc số trước, rồi ghi Nhật ký BTP cho cả hai ô kèm bảng Kiểm bánh nguồn
	và người đang lưu. `ly_do` để trống thì máy tự gọi theo dấu: trừ Bếp làm
	hay cộng lại Bếp làm; bản vá truyền "ban_va"."""
	can = {ma: n for ma, n in (chenh or {}).items() if n}
	if not can:
		return 0
	truoc = {r[0]: r for r in frappe.db.sql(
		"""select ma_hang, so_btp, so_decor, ten_banh from `tabBTP Banh O Dong`
		where parent = 'BTP Banh O' and parenttype = 'BTP Banh O' and ma_hang in %(ma)s
		for update""",
		{"ma": tuple(sorted(can))},
	)}
	doi = 0
	for ma, n in sorted(can.items()):
		if ma not in truoc:
			continue
		frappe.db.sql(
			"""update `tabBTP Banh O Dong` set so_btp = ifnull(so_btp, 0) - %(n)s,
			so_decor = ifnull(so_decor, 0) - %(n)s,
			decor_da_lam = ifnull(decor_da_lam, 0) + %(n)s
			where parent = 'BTP Banh O' and parenttype = 'BTP Banh O' and ma_hang = %(ma)s""",
			{"n": int(n), "ma": ma},
		)
		_, btp_cu, decor_cu, ten = truoc[ma]
		ld = ly_do or ("tru_bep_lam" if n > 0 else "cong_lai_bep_lam")
		for truong, cu in (("so_btp", btp_cu), ("so_decor", decor_cu)):
			ghi_nhat_ky(ma, ten, truong, int(cu or 0), int(cu or 0) - int(n), ld, nguon=nguon)
		doi += 1
	if doi:
		# Đổi mốc sửa của bảng BTP: ai đang mở bảng cũ mà lưu đè thì Frappe báo
		# bảng đã đổi, thay vì ghi lại số cũ lên số vừa trừ.
		frappe.db.set_single_value("BTP Banh O", "cap_nhat_luc", now_datetime())
	return doi


# ------------------------------------------------ Nhật ký BTP (v653)
#
# Sự cố Tira 18cm (Loan Anh báo 12/11/2026): BTP sẵn và Đủ decor của
# BAWC00079 cùng từ 1 lên 2, bếp nói không nhập. Bảng không có lịch sử nào
# và mọi cửa lưu ghi lại CẢ BẢNG, nên không truy được ai đổi. Từ v653:
#   - mọi cửa ghi bảng BTP đi qua `ghi_nhat_ky` (ca kiểm chạy từng cửa);
#   - không cửa nào còn `doc.save()` cả bảng Single: lưu cả bảng ghi lại mọi
#     dòng con, có thể đè số `tru_vo_theo_sx` vừa trừ ở giao dịch khác;
#   - cửa sửa một ô khoá đúng dòng (for update), đọc số trước, UPDATE dòng đó.

DT_NK = "Nhat Ky BTP"
NHAN_LY_DO = {
	"nhap_tay": "nhập tay",
	"tru_bep_lam": "trừ theo Bếp làm",
	"cong_lai_bep_lam": "cộng lại vì sửa bớt Bếp làm",
	"refill": "nhập refill",
	"ban_va": "bản vá nâng cấp",
	"them_ma": "thêm mã",
	"xoa_ma": "gỡ mã",
	"sua_bep_lam": "sửa Bếp làm",
	"desk": "sửa thẳng trên Desk",
}
NHAN_O = {"so_btp": "BTP sẵn", "so_decor": "Đủ decor", "decor_da_lam": "Đã trừ theo Bếp làm",
	"so_refill": "Refill", "refill_tu": "Refill từ ngày", "refill_den": "Refill tới ngày", "ma": "Mã trên bảng",
	"sx": "Bếp làm"}
O_HIEN = ("so_btp", "so_decor")
MAY = {"Administrator", "Guest", ""}


def chenh_so(truoc, sau):
	"""THUẦN: chênh giữa hai số (None nếu một bên không phải số)."""
	try:
		return int(sau or 0) - int(truoc or 0)
	except (TypeError, ValueError):
		return None


def gio_ngan(luc):
	"""THUẦN: "2026-11-12 22:27:55.1" ra "22:27" nếu là hôm nay theo `hom_nay`,
	còn lại ra "12/11 22:27". Màn hiện thẳng chữ này."""
	s = str(luc or "")
	return (s[8:10] + "/" + s[5:7] + " " + s[11:16]) if len(s) >= 16 else ""


def nhan_doi(x, hom_nay=None):
	"""THUẦN: một dòng chữ ngắn dưới số trên màn, ví dụ "Linh 22:27 · nhập tay"
	hoặc "Máy trừ · Bếp làm 13/11 (Hân)". Một nguồn cho màn Kiểm bánh và /btp."""
	if not x:
		return ""
	s = str(x.get("luc") or "")
	gio = s[11:16] if hom_nay and s[:10] == str(hom_nay)[:10] else gio_ngan(s)
	ten = x.get("ten_nguoi") or "Máy"
	ld = x.get("ly_do") or ""
	if ld in ("tru_bep_lam", "cong_lai_bep_lam"):
		kb = str(x.get("nguon") or "")
		ngay = (kb[-2:] + "/" + kb[-5:-3]) if len(kb) >= 13 else ""
		dau = "Máy trừ" if ld == "tru_bep_lam" else "Máy cộng lại"
		return "%s · Bếp làm %s (%s)" % (dau, ngay, ten) if ngay else "%s · Bếp làm (%s)" % (dau, ten)
	if ld == "ban_va":
		return "Máy %s · bản vá nâng cấp" % gio
	return "%s %s · %s" % (ten, gio, NHAN_LY_DO.get(ld, ld))


def _ten_nguoi(nguoi):
	if nguoi in MAY:
		return "Máy"
	try:
		return frappe.db.get_value("User", nguoi, "full_name") or str(nguoi).split("@")[0]
	except Exception:
		return str(nguoi).split("@")[0]


def ghi_nhat_ky(ma_hang, ten_banh, truong, truoc, sau, ly_do, nguon=None, nguoi=None):
	"""Ghi một dòng nhật ký. Số không đổi thì không ghi. Cùng giao dịch với lần
	ghi số: lưu hỏng thì nhật ký cũng lùi."""
	if str(truoc if truoc is not None else "") == str(sau if sau is not None else ""):
		return None
	nguoi = nguoi or frappe.session.user
	d = frappe.new_doc(DT_NK)
	d.update({
		"ma_hang": ma_hang, "ten_banh": ten_banh or "", "truong": truong,
		"truoc": "" if truoc is None else str(truoc), "sau": "" if sau is None else str(sau),
		"chenh": chenh_so(truoc, sau) or 0, "ly_do": ly_do, "nguon": nguon or "",
		"nguoi": nguoi if nguoi not in MAY else None, "ten_nguoi": _ten_nguoi(nguoi), "luc": now_datetime(),
	})
	d.flags.ignore_permissions = True
	d.insert(ignore_permissions=True)
	return d.name


def _khoa_dong(ma_hang):
	"""Khoá đúng dòng của mã (for update) và trả số đang lưu, hoặc None.
	Không có chỉ mục trên ma_hang nên InnoDB khoá cả khoảng đã quét: hai người
	cùng thêm một mã mới sẽ đi lần lượt, không ra hai dòng."""
	r = frappe.db.sql(
		"""select name, ma_hang, ten_banh, so_btp, so_decor, decor_da_lam, so_refill, refill_tu, refill_den
		from `tabBTP Banh O Dong` where parent = 'BTP Banh O' and parenttype = 'BTP Banh O'
		and ma_hang = %(ma)s for update""",
		{"ma": ma_hang}, as_dict=True,
	)
	return r[0] if r else None


def _them_dong(ma_hang, ten="", anh="", kiem_ma=True):
	"""Thêm dòng mới cho mã chưa có trên bảng, không lưu lại cả bảng."""
	if kiem_ma and not _dang_ma_dung(ma_hang):
		frappe.throw(
			"Bảng BTP chỉ theo dõi bánh ổ và bánh sỉ. Mã phải là BAWC hoặc BAWS "
			"kèm 5 chữ số, ví dụ BAWC00098 - mã %s không thêm được." % ma_hang
		)
	idx = frappe.db.sql("""select ifnull(max(idx), 0) from `tabBTP Banh O Dong`
		where parent = 'BTP Banh O' and parenttype = 'BTP Banh O'""")[0][0] or 0
	d = frappe.new_doc("BTP Banh O Dong")
	d.update({"parent": "BTP Banh O", "parenttype": "BTP Banh O", "parentfield": "dong", "idx": int(idx) + 1, "ma_hang": ma_hang, "ten_banh": ten or "", "hinh": anh or "",
		"so_btp": 0, "so_decor": 0, "decor_da_lam": 0, "so_refill": 0, "name": frappe.generate_hash(length=10)})
	d.db_insert()
	ghi_nhat_ky(ma_hang, ten, "ma", "", ma_hang, "them_ma")
	return frappe._dict(name=d.name, ma_hang=ma_hang, ten_banh=ten or "", so_btp=0, so_decor=0, decor_da_lam=0,
		so_refill=0, refill_tu=None, refill_den=None)


def _dong_hoac_them(ma_hang):
	"""Dòng đã khoá của mã; chưa có thì thêm (giữ cách cũ của _dong_cua_ma:
	kiểm mã BAWC/BAWS, tra tên và ảnh, Pancake lỗi vẫn cho lưu số)."""
	ma_hang = str(ma_hang or "").strip()
	if not ma_hang:
		frappe.throw("Thieu ma hang")
	d = _khoa_dong(ma_hang)
	if d:
		return d
	if not _dang_ma_dung(ma_hang):
		frappe.throw(
			"Bảng BTP chỉ theo dõi bánh ổ và bánh sỉ. Mã phải là BAWC hoặc BAWS "
			"kèm 5 chữ số, ví dụ BAWC00098 - mã %s không thêm được." % ma_hang
		)
	ten, anh = "", ""
	try:
		c = cfg()
		ten, anh = _tra_anh_ten(c, key(c, "pancake_api_key"), ma_hang)
	except Exception:
		# Pancake loi hay chua co key thi van cho luu so, ten/hinh do sau.
		frappe.log_error(frappe.get_traceback(), "BTP: khong tra duoc ten/anh %s" % ma_hang)
	return _them_dong(ma_hang, ten, anh, kiem_ma=False)


def _ghi_o(d, gia_tri, ly_do):
	"""UPDATE đúng một dòng (đã khoá), ghi nhật ký từng ô đổi, đổi mốc bảng."""
	doi = {k: v for k, v in gia_tri.items() if str(d.get(k) if d.get(k) is not None else "") != str(v if v is not None else "")}
	if doi:
		frappe.db.sql("update `tabBTP Banh O Dong` set %s where name = %%(ten)s" % ", ".join("`%s` = %%(%s)s" % (k, k) for k in sorted(doi)),
			dict(doi, ten=d.name))
		for k in sorted(doi):
			if k == "decor_da_lam":
				continue
			ghi_nhat_ky(d.ma_hang, d.ten_banh, k, d.get(k), doi[k], ly_do)
	frappe.db.set_single_value("BTP Banh O", "cap_nhat_luc", now_datetime())
	return doi


def _gan_doi(dong, hom_nay=None):
	"""Lần đổi gần nhất của BTP sẵn và Đủ decor cho từng mã: {mã: {ô: {...}}}.
	Một câu đọc cho cả bảng, màn khỏi gọi thêm."""
	ma = [d["ma_hang"] for d in dong if d.get("ma_hang")]
	if not ma:
		return {}
	try:
		rows = frappe.db.sql(
			"""select n.ma_hang, n.truong, n.ten_nguoi, n.luc, n.ly_do, n.nguon from `tabNhat Ky BTP` n
			join (select ma_hang, truong, max(creation) c from `tabNhat Ky BTP`
				where ma_hang in %(ma)s and truong in %(o)s group by ma_hang, truong) m
			on m.ma_hang = n.ma_hang and m.truong = n.truong and m.c = n.creation""",
			{"ma": tuple(ma), "o": O_HIEN}, as_dict=True)
	except Exception:
		# Bảng nhật ký chưa dựng (trước migrate) thì màn vẫn chạy, chỉ thiếu dòng.
		return {}
	ra = {}
	for r in rows:
		ra.setdefault(r["ma_hang"], {})[r["truong"]] = {"chu": nhan_doi(r, hom_nay), "luc": str(r.get("luc") or "")}
	return ra


@frappe.whitelist()
def lich_su_btp(ma_hang, so=10):
	"""Mười lần đổi gần nhất của một mã cho hộp "Lịch sử" trên màn."""
	if frappe.session.user == "Guest":
		frappe.throw("Đăng nhập rồi mới xem được lịch sử BTP.", frappe.PermissionError)
	try:
		so = max(1, min(50, int(so or 10)))
	except (TypeError, ValueError):
		so = 10
	rows = frappe.get_all(DT_NK, filters={"ma_hang": str(ma_hang or "").strip()},
		fields=["truong", "truoc", "sau", "chenh", "ly_do", "nguon", "ten_nguoi", "luc"],
		order_by="creation desc", limit_page_length=so, ignore_permissions=True)
	hom = str(getdate())
	return {"ma_hang": ma_hang, "dong": [{
		"o": NHAN_O.get(r.truong, r.truong), "truoc": r.truoc, "sau": r.sau, "chenh": r.chenh,
		"chu": nhan_doi(r, hom), "ly_do": NHAN_LY_DO.get(r.ly_do, r.ly_do or ""), "luc": str(r.luc or ""),
	} for r in rows]}


@frappe.whitelist()
def bang_btp():
	"""Du lieu cho man hinh /btp va nhan BTP tren man kiem banh."""
	from vagabond import refill

	doc = frappe.get_single("BTP Banh O")
	rf = _refill_cua_bang(doc)
	giu = _giu_theo_ma(rf)
	giu_mai = _giu_ngay_mai(rf)
	# v646 Refill: số còn nhận refill và đơn đặt xa ngày (Pancake, phiếu đặt).
	so_rf = refill.tinh(dong=doc.dong)
	doi = _gan_doi([{"ma_hang": d.ma_hang} for d in doc.dong], getdate())
	dong = []
	for d in doc.dong:
		decor = min(d.so_decor or 0, d.so_btp or 0)
		dong.append(
			{
				"ma_hang": d.ma_hang,
				"ten_banh": d.ten_banh or "",
				"hinh": d.hinh or "",
				# v649: bếp làm nhiều hơn số đếm thì số lưu có thể âm; màn hiện 0,
				# còn các ô Còn nhận vẫn tính trên số thật để báo thiếu.
				"so_btp": max(0, d.so_btp or 0),
				"so_decor": max(0, d.so_decor or 0),
				"dang_giu": giu.get(d.ma_hang, 0),
				"con_nhan": (d.so_btp or 0) - giu.get(d.ma_hang, 0),
				"giao_mai": decor - giu_mai.get(d.ma_hang, 0),
				"refill": (so_rf.get("refill") or {}).get(d.ma_hang),
				# v653: lần đổi gần nhất của BTP sẵn, Đủ decor (chữ ngắn sẵn để hiện).
				"doi": doi.get(d.ma_hang) or {},
			}
		)
	return {"cap_nhat_luc": str(doc.cap_nhat_luc or ""), "dong": dong,
		"dat_xa": so_rf.get("dat_xa") or {}, "refill_loi": so_rf.get("loi") or "",
		"lich_refill": sorted((dict(v, ma_hang=m) for m, v in (so_rf.get("refill") or {}).items()), key=lambda x: (x["tu"], x["ma_hang"]))}


@frappe.whitelist()
def luu_btp(ma_hang, so_btp):
	"""Bep sua so BTP mot mon. Giu quyen that cua nguoi sua de con vet.
	v653: khoá đúng dòng, UPDATE dòng đó, ghi nhật ký; không lưu cả bảng."""
	if not _duoc_sua_btp():
		frappe.throw("Cột BTP sẵn chỉ bếp được nhập - bếp nhập thì bếp chịu trách nhiệm số")
	d = _dong_hoac_them(ma_hang)
	_ghi_o(d, {"so_btp": max(0, int(so_btp or 0))}, "nhap_tay")
	frappe.db.commit()
	return bang_btp()


@frappe.whitelist()
def luu_decor(ma_hang, so_decor):
	"""Bep sua so BTP da du do decor - so nay quyet dinh nhan don ngay mai."""
	if not _duoc_sua_btp():
		frappe.throw("Cột Đủ decor chỉ bếp được nhập - bếp nhập thì bếp chịu trách nhiệm số")
	d = _dong_hoac_them(ma_hang)
	# v649: bếp đếm lại decor là gốc mới, phần đã trừ theo Bếp làm về 0.
	_ghi_o(d, {"so_decor": max(0, int(so_decor or 0)), "decor_da_lam": 0}, "nhap_tay")
	frappe.db.commit()
	return bang_btp()


@frappe.whitelist()
def luu_refill(ma_hang, so_refill=None, refill_tu=None, refill_den=None):
	"""v646: bếp nhập mẻ refill của một bánh. Số 0 là bỏ refill."""
	from vagabond import refill

	if not _duoc_sua_btp():
		frappe.throw("Ô Refill chỉ bếp được nhập - bếp nhập thì bếp chịu trách nhiệm số")
	try:
		so, tu, den = refill.chuan_refill(so_refill, refill_tu, refill_den, getdate())
	except refill.LoiRefill as e:
		frappe.throw(str(e))
	d = _dong_hoac_them(ma_hang)
	_ghi_o(d, {"so_refill": so, "refill_tu": tu or None, "refill_den": den or None}, "refill")
	frappe.db.commit()
	try:
		# Số refill mới phải lên bảng ngay, không chờ hết 5 phút giữ số đơn.
		frappe.cache().delete_value("vgb_refill_don:%s" % getdate().isoformat())
	except Exception:
		pass
	return bang_btp()


@frappe.whitelist()
def them_ma_btp(ma_hang):
	if not _duoc_sua_btp():
		frappe.throw("Bảng BTP chỉ bếp được thêm mã")
	ma_hang = str(ma_hang or "").strip()
	if not ma_hang:
		frappe.throw("Thieu ma hang")
	if not _dang_ma_dung(ma_hang):
		frappe.throw(
			"Bảng BTP chỉ theo dõi bánh ổ và bánh sỉ. Mã phải là BAWC hoặc BAWS "
			"kèm 5 chữ số, ví dụ BAWC00098 - mã %s không thêm được." % ma_hang
		)
	if _khoa_dong(ma_hang):
		frappe.throw("Ma nay da co trong bang")
	c = cfg()
	k = key(c, "pancake_api_key")
	if not _co_that(c, k, ma_hang):
		frappe.throw(
			"Không tìm thấy mã %s ở cả Pancake lẫn danh mục Hàng hoá bên Next. "
			"Anh chị kiểm tra lại mã, hoặc tạo mã đó trước rồi thêm sau." % ma_hang
		)
	ten, anh = _tra_anh_ten(c, k, ma_hang)
	_them_dong(ma_hang, ten, anh, kiem_ma=False)
	frappe.db.set_single_value("BTP Banh O", "cap_nhat_luc", now_datetime())
	frappe.db.commit()
	return bang_btp()


@frappe.whitelist()
def xoa_ma_btp(ma_hang):
	"""Go mot ma go nham khoi bang BTP - chi khi ca hai so deu bang 0."""
	if not _duoc_sua_btp():
		frappe.throw("Bảng BTP chỉ bếp được xoá mã")
	d = _khoa_dong(str(ma_hang or "").strip())
	if not d:
		frappe.throw("Khong thay ma hang %s trong bang BTP" % ma_hang)
	if int(d.so_btp or 0) or int(d.so_decor or 0) or int(d.so_refill or 0):
		frappe.throw("Mã %s đang có số BTP, số decor hoặc refill, xoá số về 0 trước đã." % ma_hang)
	frappe.db.sql("delete from `tabBTP Banh O Dong` where name = %(ten)s", {"ten": d.name})
	ghi_nhat_ky(d.ma_hang, d.ten_banh, "ma", d.ma_hang, "", "xoa_ma")
	frappe.db.set_single_value("BTP Banh O", "cap_nhat_luc", now_datetime())
	frappe.db.commit()
	return bang_btp()


@frappe.whitelist()
def gieo_tu_kiem_banh():
	"""Do san cac ma dang co trong bang kiem 4 ngay toi - bep khoi go tay."""
	hom_nay = getdate()
	them = 0
	for i in range(4):
		ma_doc = "KB-%s" % add_days(hom_nay, i)
		if not frappe.db.exists("Kiem Banh Ngay", ma_doc):
			continue
		kb = frappe.get_doc("Kiem Banh Ngay", ma_doc)
		for d in kb.dong:
			if not d.ma_hang or _khoa_dong(d.ma_hang):
				continue
			_them_dong(d.ma_hang, d.ten_banh, d.hinh, kiem_ma=False)
			them += 1
	if them:
		frappe.db.set_single_value("BTP Banh O", "cap_nhat_luc", now_datetime())
		frappe.db.commit()
	return {"them": them}

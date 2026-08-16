"""Khoa xoa vinh vien chung tu (anh Viet 11/08/2026).

Ngay 10/08 quan ly cua hang xoa 37 hoa don quay Tran Cao Van, tong
7.455.700 d. Hoa don da co so hoa don dien tu 10139-10176 nam ben co quan
thue, con chung tu goc trong he thong thi bien mat sach - khong con gi de
doi chieu, chi Dung phai lam hoa don thay the ve 0 dong.

Anh Viet chot: "khong duoc phep xoa vinh vien bat cu hoa don nao o bat cu
phan he nao, du la app hay desktop. Viec xoa vinh vien chung tu la qua
nguy hiem."

Nen o day khoa THANG o tang document bang hook on_trash. Khoa o tang nay
thi moi duong nguoi dung cham toi deu bit: nut xoa tren Desk, nut xoa tren
app, goi API, bulk delete tu man danh sach, ca script cua chinh minh. Ke ca
Administrator cung khong xoa duoc, vi nguoi gay ra su co hoan toan co the
dang nhap bang tai khoan manh.

Con hai duong ngoai tam voi cua hook, phai biet de con canh: cong cu
"Transaction Deletion Record" cua ERPNext xoa bang SQL thang, va lenh
bench execute / console chay duoi quyen he thong. Ca hai deu can quyen quan
tri may chu chu khong phai thao tac hang ngay cua ai o cua hang.

Doi lai, phai co duong hop le de bo mot phieu sai:
  - Phieu DA GHI SO: huy dung nghiep vu (docstatus 2). ERPNext lo san.
  - Phieu CON NHAP: ERPNext khong cho huy ban nhap, nen danh dau mem bang
    truong vgb_huy. Phieu van nam nguyen cho cu, chi doi mau va bi loc ra
    khoi cac so lieu.
"""

import frappe
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate

from vagabond.lib import cfg

# Chung tu tai chinh va kho. Doi mot dong o day la doi pham vi khoa, nen
# doc ky truoc khi them bot.
KHOA_XOA = {
	"Sales Invoice",
	"POS Invoice",
	"Purchase Invoice",
	"Payment Entry",
	"Journal Entry",
	"Sales Order",
	"Purchase Order",
	"Delivery Note",
	"Purchase Receipt",
	"Stock Entry",
	"Stock Reconciliation",
}

# Ai duoc danh dau huy mot phieu nhap. Bill quay di duong rieng qua
# ban_hang.pos_huy (thu ngan huy duoc bill cua quay minh, co OTP quan ly).
QUYEN_HUY = {"System Manager", "Accounts Manager", "Accounts User"}

TEN_VIET = {
	"Sales Invoice": "hoá đơn bán",
	"POS Invoice": "hoá đơn quầy",
	"Purchase Invoice": "hoá đơn mua",
	"Payment Entry": "phiếu thu chi",
	"Journal Entry": "bút toán",
	"Sales Order": "đơn bán hàng",
	"Purchase Order": "đơn mua hàng",
	"Delivery Note": "phiếu giao hàng",
	"Purchase Receipt": "phiếu nhập mua",
	"Stock Entry": "phiếu kho",
	"Stock Reconciliation": "phiếu kiểm kê",
}


def chan_xoa(doc, method=None):
	"""Hook on_trash cho MOI doctype. Chung tu thi nem loi, con lai cho qua.

	Dat o hook "*" chu khong liet ke tung doctype: liet ke thi hom nao them
	mot loai chung tu moi la lai quen, ma quen o day thi khong ai biet cho
	den luc mat chung tu.
	"""
	dt = getattr(doc, "doctype", None)
	if dt not in KHOA_XOA:
		return
	ten = TEN_VIET.get(dt, "chứng từ")
	if cint(getattr(doc, "docstatus", 0)) == 0:
		cach = (
			"Phiếu còn nháp thì bấm nút Huỷ phiếu, phiếu vẫn nằm nguyên chỗ cũ "
			"và được đánh dấu đã huỷ."
		)
	else:
		cach = "Muốn bỏ thì huỷ phiếu đúng nghiệp vụ, đừng xoá."
	frappe.throw(
		"Không xoá được %s %s. Hệ thống không cho xoá vĩnh viễn bất cứ chứng từ "
		"nào, ở app hay trên máy tính đều vậy - mất chứng từ gốc là mất luôn "
		"đường đối chiếu với cơ quan thuế. %s" % (ten, doc.name, cach),
		title="Chứng từ không được xoá",
	)


def chan_ghi_so(doc, method=None):
	"""Hook before_submit: phieu da danh dau huy thi khong duoc ghi so.

	Khong co chot nay thi huy mem chi la mot cai nhan: go_don_trung danh dau
	huy mot phieu trung, roi sales bam Chot doanh so la phieu do van submit,
	van vao so cai, van phat hanh hoa don dien tu - dung cai canh tinh doanh
	thu hai lan ma huy mem sinh ra de tranh.
	"""
	dt = getattr(doc, "doctype", None)
	if dt not in KHOA_XOA or not cint(doc.get("vgb_huy") or 0):
		return
	frappe.throw(
		"Phiếu %s đã huỷ nên không ghi sổ được. Lý do huỷ: %s. Muốn dùng lại "
		"thì gỡ dấu huỷ trước, hoặc lập phiếu mới."
		% (doc.name, (doc.get("vgb_huy_ly_do") or "không ghi")),
		title="Phiếu đã huỷ",
	)


# ---------------------------------------------------------------- huy mem


def _kiem_quyen_huy(doc=None, cho_chu_phieu=True):
	"""Ke toan huy duoc moi phieu; ai lap phieu NHAP thi bo phieu cua minh.

	Khong mo cho chu phieu thi thu mua lap nham mot don mua hang cung phai
	di nho ke toan - vua khong xoa duoc (hook chan) vua khong huy duoc, ket
	cung. Phieu DA GHI SO thi van chi ke toan dung toi.

	Ngoai le: BILL QUAY. Bill quay la tien that da thu cua khach nen phai di
	dung duong ban_hang.pos_xoa, o do co ma OTP cua quan ly ca va co canh
	bao rieng cho bill da xuat hoa don dien tu. Mo nhanh chu phieu cho no
	thi thu ngan goi thang ham nay la lach het cac chot do.
	"""
	if QUYEN_HUY & set(frappe.get_roles()):
		return
	if doc is not None and (doc.get("vgb_quay") or "").strip():
		frappe.throw(
			"Bill quầy thì huỷ ngay trong màn hoá đơn của quầy, ở đó máy hỏi mã "
			"OTP của quản lý ca."
		)
	if (
		cho_chu_phieu
		and doc is not None
		and cint(getattr(doc, "docstatus", 1)) == 0
		and doc.get("owner") == frappe.session.user
	):
		return
	frappe.throw("Chỉ kế toán, giám đốc hoặc người lập phiếu mới huỷ được phiếu này.")


def danh_dau_huy(doc, ly_do=None, ghi_vet=True):
	"""Danh dau mot ban nhap la da huy. Ghi thang bang db.set_value.

	Khong dung doc.save(): ban nhap sai co the dang vuong validate (thieu
	kho, thieu tai khoan, gia am) - dung save thi chinh cai phieu can bo di
	lai la cai khong luu duoc, nguoi dung ket cung khong loi ra.
	"""
	dt, ten = doc.doctype, doc.name
	if cint(doc.docstatus) != 0:
		frappe.throw(
			"Phiếu %s đã ghi sổ rồi nên phải huỷ đúng nghiệp vụ, không đánh dấu "
			"kiểu này được." % ten
		)
	gt = {
		"vgb_huy": 1,
		"vgb_huy_ly_do": (ly_do or "").strip()[:500],
		"vgb_huy_luc": now_datetime(),
		"vgb_huy_boi": frappe.session.user,
	}
	# Hoa don ban mang ma don Pancake thi phai NHA ma ra khi huy. Ma nay co
	# khoa duy nhat trong co so du lieu va la thu chan_trung_ma_pancake dua
	# vao; giu no lai tren mot to da huy thi don do vinh vien khong lap duoc
	# hoa don moi, va lan dong bo sau con lay chinh to da huy ra dung lai -
	# don thanh ra khong bao gio vao doanh thu ma khong ai bao loi. Ma cu
	# cat sang vgb_ma_pancake_huy de con doi chieu.
	if dt == "Sales Invoice" and (doc.get("custom_pancake_id") or "").strip():
		gt["vgb_ma_pancake_huy"] = str(doc.get("custom_pancake_id")).strip()
		# PHAI la None chu khong duoc la chuoi rong: cot nay mang khoa duy
		# nhat ux_vgb_pancake_id. MariaDB cho nhieu dong NULL nhung hai dong
		# cung '' la trung khoa - huy bill thu hai se no loi SQL, ma xoa thi
		# hook chan, thu ngan ket cung khong duong ra.
		gt["custom_pancake_id"] = None
	frappe.db.set_value(dt, ten, gt)
	if ghi_vet:
		_ghi_vet(dt, ten, "Huỷ phiếu nháp. Lý do: %s" % ((ly_do or "").strip() or "không ghi"))
	frappe.db.commit()

	# TRA LAI DIEM DA TRU. Duong nay KHONG di qua on_cancel.
	#
	# Huy mem chi dat co vgb_huy bang db.set_value, Frappe khong goi hook
	# on_cancel nao ca. Neu chi gan hoan diem vao on_cancel thi moi bill
	# quay bi huy mem se nuot luon diem cua khach, va khong ai phat hien ra
	# cho den luc khach di doi qua - luc do khong con doi chieu duoc nua.
	#
	# Dat SAU commit va boc try: tra diem hong khong duoc lam hong viec huy
	# phieu. Hong thi ghi nhat ky, chay lai bang nut duoc.
	if dt == "Sales Invoice":
		try:
			from vagabond import diem_otp

			diem_otp.hoan_diem_don(ten, "Bill bị đánh dấu huỷ: %s" % ((ly_do or "").strip() or "không ghi"))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "chung_tu: hoan diem khi huy mem")


@frappe.whitelist()
def huy_phieu_nhap(doctype, name, ly_do=None):
	"""Nut Huy phieu tren Desk va tren app cho cac phieu con nhap."""
	if doctype not in KHOA_XOA:
		frappe.throw("Loại chứng từ này không dùng nút huỷ ở đây.")
	if not (ly_do or "").strip():
		frappe.throw("Phải ghi lý do huỷ thì sau này còn biết vì sao.")
	doc = frappe.get_doc(doctype, name)
	_kiem_quyen_huy(doc)
	if cint(doc.get("vgb_huy") or 0):
		return {"ok": 1, "da_huy_tu_truoc": 1}
	danh_dau_huy(doc, ly_do)
	return {"ok": 1, "name": name}


@frappe.whitelist()
def bo_danh_dau_huy(doctype, name):
	"""Danh dau nham thi go ra duoc - nhung van ghi vet lai."""
	if doctype not in KHOA_XOA:
		frappe.throw("Loại chứng từ này không dùng nút huỷ ở đây.")
	doc = frappe.get_doc(doctype, name)
	# Go dau huy la lam song lai mot chung tu, nang hon huy - chi ke toan.
	_kiem_quyen_huy(doc, cho_chu_phieu=False)
	if not cint(doc.get("vgb_huy") or 0):
		return {"ok": 1, "chua_huy": 1}
	gt = {"vgb_huy": 0, "vgb_huy_ly_do": "", "vgb_huy_luc": None, "vgb_huy_boi": ""}
	them = ""
	ma_cu = (doc.get("vgb_ma_pancake_huy") or "").strip()
	if doctype == "Sales Invoice" and ma_cu:
		# Tra ma don Pancake ve, nhung chi khi cho do con trong: trong luc to
		# nay nam huy, dong bo hoan toan co the da lap mot hoa don khac cho
		# cung don do. Doi ma vao thi dinh khoa duy nhat va hong ca lenh go.
		da_co = frappe.db.get_value(
			"Sales Invoice", {"custom_pancake_id": ma_cu, "name": ["!=", name]}, "name"
		)
		if da_co:
			them = (
				" Mã đơn Pancake %s không trả lại được vì hoá đơn %s đang giữ."
				% (ma_cu, da_co)
			)
		else:
			gt["custom_pancake_id"] = ma_cu
			gt["vgb_ma_pancake_huy"] = ""
	frappe.db.set_value(doctype, name, gt)
	_ghi_vet(doctype, name, "Gỡ dấu huỷ, phiếu dùng lại bình thường." + them)
	frappe.db.commit()
	return {"ok": 1, "name": name, "nhac": them.strip()}


def _ghi_vet(doctype, name, viec):
	"""Moi lan huy hay go dau huy deu phai biet ai lam, luc nao."""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": doctype,
				"reference_name": name,
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "chung_tu: ghi vet %s" % name)


# ------------------------------------------------------ trang thai da sua


def ghi_nhan_sua(doctype, name):
	"""Dem so lan mot ban nhap bi sua, de chip "Da sua" co cai ma loc.

	Ban nhap sua tai cho thi ERPNext khong luu lai dau vet nao o muc
	docstatus, nen phai tu dem.
	"""
	try:
		cu = cint(frappe.db.get_value(doctype, name, "vgb_lan_sua") or 0)
		frappe.db.set_value(
			doctype,
			name,
			{"vgb_lan_sua": cu + 1, "vgb_sua_luc": now_datetime()},
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "chung_tu: dem lan sua %s" % name)


def ds_da_bi_sua(doctype, ten_ds):
	"""Nhung phieu DA CO BAN THAY THE: co phieu khac amended_from tro toi.

	Huy roi sua lai trong ERPNext la tao mot phieu moi mang amended_from
	tro ve phieu cu. Nhin tu phieu cu thi no chi thay minh docstatus 2,
	khong biet minh da duoc thay the hay bi bo han - hai viec rat khac nhau
	voi ke toan.
	"""
	ten_ds = [t for t in (ten_ds or []) if t]
	if not ten_ds:
		return set()
	try:
		return {
			r.amended_from
			for r in frappe.get_all(
				doctype,
				filters={"amended_from": ["in", ten_ds]},
				fields=["amended_from"],
				limit_page_length=0,
			)
			if r.amended_from
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "chung_tu: doc ban thay the")
		return set()


@frappe.whitelist()
def pham_vi_khoa():
	"""Cho man Cai dat xem dang khoa nhung loai nao."""
	return [{"dt": dt, "ten": TEN_VIET.get(dt, dt)} for dt in sorted(KHOA_XOA)]


# ====================================================================
# KHOA SO THEO NGAY (anh Viet 12/08/2026, hoc tu Fabi muc 3.7)
#
# Truoc day hoa don da ghi so van sua duoc vo thoi han mien co ma OTP, va
# huy duoc bat cu luc nao. Nghia la so lieu thang truoc - da nop thue, da
# doi soat voi ngan hang - van co the doi ma khong ai hay.
#
# Nay khoa lai: chung tu cua ngay da khoa thi khong ghi so, khong huy,
# khong sua duoc nua. Ke toan truong can dong mot to cu thi mo khoa rieng
# to do, co ghi ly do va ten nguoi mo.
# ====================================================================

# Ai duoc doi cau hinh khoa so va mo khoa tung to.
QUYEN_KHOA_SO = {"System Manager", "Accounts Manager"}

# Truong ngay cua tung loai chung tu. Don ban va don mua dung ngay chung
# tu, con lai dung ngay hach toan.
TRUONG_NGAY = {
	"Sales Order": "transaction_date",
	"Purchase Order": "transaction_date",
}


def ngay_khoa():
	"""Ngay khoa hien tai: chung tu tu ngay nay tro ve TRUOC deu bi khoa.

	Lay cai muon hon trong hai moc: "khoa sau N ngay" tinh lui tu hom nay,
	va moc khoa cung do ke toan dat tay sau khi chot so mot ky.
	Tra ve None neu khong khoa gi.
	"""
	try:
		c = cfg()
	except Exception:
		return None
	moc = []
	n = cint(c.get("khoa_so_ngay") or 0)
	if n > 0:
		moc.append(getdate(add_days(nowdate(), -n)))
	den = c.get("khoa_so_den")
	if den:
		try:
			moc.append(getdate(den))
		except Exception:
			pass
	return max(moc) if moc else None


def _ngay_cua(doc):
	truong = TRUONG_NGAY.get(doc.doctype, "posting_date")
	gt = doc.get(truong) or doc.get("posting_date") or doc.get("transaction_date")
	try:
		return getdate(gt) if gt else None
	except Exception:
		return None


def chan_ngay_khoa(doc, method=None):
	"""Hook before_submit / before_cancel / on_update_after_submit.

	Dat o khoa "*" cung ba hook kia nhung THOAT NGAY neu khong phai chung
	tu, de khong lam cham moi thu con lai trong he.
	"""
	dt = getattr(doc, "doctype", None)
	if dt not in KHOA_XOA:
		return

	# Doi tru tien coc / tam ung: khi ghi so mot hoa don co dong Advance,
	# ERPNext mo chinh phieu thu cu ra va save() lai de danh dau da doi tru.
	# Chan duong do thi khach dat coc thang truoc la khong lap noi hoa don
	# thang nay - het duong di. Frappe dung co nay rieng cho luong do.
	if getattr(frappe.flags, "ignore_party_validation", False):
		return

	# Doc co mo khoa o BAN CU trong co so du lieu, KHONG doc ban trong bo nho.
	# vgb_mo_khoa la truong sua duoc sau khi ghi so, nen chinh lan luu bat co
	# do cung di qua day - doc ban moi thi co tu cap phep cho chinh no, ai
	# tick mot cai la thoat khoa, toan bo quyen han va ghi vet thanh vo nghia.
	truoc = None
	try:
		truoc = doc.get_doc_before_save()
	except Exception:
		truoc = None
	da_mo = cint((truoc.get("vgb_mo_khoa") if truoc else doc.get("vgb_mo_khoa")) or 0)
	if da_mo:
		return
	khoa = ngay_khoa()
	if not khoa:
		return
	ngay = _ngay_cua(doc)
	if not ngay or ngay > khoa:
		return
	frappe.throw(
		"Sổ ngày %s đã khoá (khoá đến hết %s) nên không đụng vào %s %s được "
		"nữa. Số liệu kỳ đó đã chốt và đã đối chiếu rồi. Thật sự cần sửa thì "
		"nhờ kế toán mở khoá riêng tờ này, máy sẽ ghi lại lý do và tên người mở."
		% (
			ngay.strftime("%d/%m/%Y"),
			khoa.strftime("%d/%m/%Y"),
			TEN_VIET.get(dt, "chứng từ"),
			doc.name,
		),
		title="Sổ đã khoá",
	)


def _kiem_quyen_khoa():
	if not QUYEN_KHOA_SO & set(frappe.get_roles()):
		frappe.throw("Chỉ kế toán trưởng hoặc giám đốc mới đụng được vào khoá sổ.")


@frappe.whitelist()
def cai_dat_khoa_so():
	"""Man Cai dat doc cau hinh khoa so."""
	if not (QUYEN_HUY | QUYEN_KHOA_SO) & set(frappe.get_roles()):
		frappe.throw("Khoá sổ chỉ mở cho kế toán và giám đốc.")
	c = cfg()
	k = ngay_khoa()
	dem = 0
	for x in KHOA_XOA:
		try:
			dem += frappe.db.count(x, {"vgb_mo_khoa": 1})
		except Exception:
			pass
	return {
		"so_ngay": cint(c.get("khoa_so_ngay") or 0),
		"den": str(c.get("khoa_so_den") or ""),
		"ngay_khoa": str(k) if k else "",
		"so_to_dang_mo": dem,
		"sua_duoc": 1 if QUYEN_KHOA_SO & set(frappe.get_roles()) else 0,
		"loai": sorted(TEN_VIET.get(x, x) for x in KHOA_XOA),
	}


@frappe.whitelist()
def luu_khoa_so(so_ngay=None, den=None):
	"""Luu cau hinh khoa so tu man Cai dat."""
	_kiem_quyen_khoa()
	n = cint(so_ngay or 0)
	if n < 0 or n > 3650:
		frappe.throw("Số ngày khoá sổ phải từ 0 đến 3650.")
	# Moc khoa cung khong duoc dat vao tuong lai: dat nham la khoa luon so
	# cua hom nay, thu ngan khong ghi so duoc to nao ma khong hieu vi sao.
	moc = ""
	if str(den or "").strip():
		try:
			d = getdate(den)
		except Exception:
			frappe.throw("Mốc khoá sổ không đúng định dạng ngày.")
		if d >= getdate(nowdate()):
			frappe.throw(
				"Mốc khoá sổ phải là ngày đã qua. Đặt ngày %s là khoá luôn sổ "
				"của hôm nay, quầy không chốt được bill nào và chuỗi cuối ngày "
				"cũng không ghi sổ được tờ nào."
				% d.strftime("%d/%m/%Y")
			)
		moc = str(d)
	frappe.db.set_single_value("Vagabond Settings", "khoa_so_ngay", n)
	frappe.db.set_single_value("Vagabond Settings", "khoa_so_den", moc or None)
	frappe.db.commit()
	_ghi_vet(
		"Vagabond Settings",
		"Vagabond Settings",
		"Đổi khoá sổ: sau %d ngày%s" % (n, (", mốc cứng %s" % moc) if moc else ""),
	)
	return cai_dat_khoa_so()


@frappe.whitelist()
def mo_khoa_mot_to(doctype, name, ly_do=None):
	"""Mo khoa DUNG MOT to de sua, co ghi ly do va ten nguoi mo."""
	if doctype not in KHOA_XOA:
		frappe.throw("Loại chứng từ này không nằm trong diện khoá sổ.")
	_kiem_quyen_khoa()
	if not (ly_do or "").strip():
		frappe.throw("Phải ghi lý do mở khoá thì sau này còn giải trình được.")
	if not frappe.db.exists(doctype, name):
		frappe.throw("Không tìm thấy chứng từ %s." % name)
	frappe.db.set_value(doctype, name, "vgb_mo_khoa", 1)
	_ghi_vet(doctype, name, "MỞ KHOÁ SỔ để sửa. Lý do: %s" % ly_do.strip())
	frappe.db.commit()
	return {"ok": 1}


@frappe.whitelist()
def dong_khoa_mot_to(doctype, name):
	"""Sua xong thi dong lai."""
	if doctype not in KHOA_XOA:
		frappe.throw("Loại chứng từ này không nằm trong diện khoá sổ.")
	_kiem_quyen_khoa()
	if not frappe.db.exists(doctype, name):
		frappe.throw("Không tìm thấy chứng từ %s." % name)
	frappe.db.set_value(doctype, name, "vgb_mo_khoa", 0)
	_ghi_vet(doctype, name, "Đóng khoá sổ lại.")
	frappe.db.commit()
	return {"ok": 1}


# ------------------------------------------------- huy ghi so hang loat
#
# Anh Viet 13/08/2026: 135 hoa don bi keo nham sang ngay moi roi ghi so, can
# huy ghi so va an khoi danh sach bill cua Sales.
#
# Vi sao lam thanh MOT NUT trong app chu khong chay thang mot lan roi thoi:
# huy hang loat hoa don da ghi so la viec dong den tien va khong lui lai
# duoc, nen phai co NGUOI BAM, co ly do, va co dau vet ai lam luc nao. Lam
# thanh nut thi lan sau gap viec tuong tu da co san cong cu, khong phai moi
# lan lai nho nguoi viet ma chay tay.


def _khong_duoc_huy(trang_thai):
	"""To nao KHONG duoc huy o day. Luat viet theo chieu CHO PHEP chu khong
	theo chieu cam.

	Ban dau ham nay viet la "co chu ky va khong co chu cho thi chan". Phep
	thu offline bat ngay: trang thai "CQT chap nhan" khong co chu ky nao nen
	LOT QUA, ma do la to da nam ben co quan thue - nguy hiem hon ca to da ky.
	Nen dao lai: chi cho huy khi o trang thai TRONG hoac CHO KY, con lai chan
	het. Sau nay m-invoice them trang thai moi thi mac dinh la chan, an toan.
	"""
	t = (trang_thai or "").strip().lower()
	if not t:
		return False
	return "chờ ký" not in t


def _mo_ta_huy(ds):
	"""Tom tat mot tap hoa don de nguoi bam nhin truoc khi quyet."""
	ra = {"so_don": len(ds), "tong_tien": 0.0, "co_hddt": 0, "da_ky": 0, "vi_du": []}
	for r in ds:
		ra["tong_tien"] += flt(r.get("grand_total"))
		if (r.get("custom_hddt_so") or "").strip():
			ra["co_hddt"] += 1
		if _khong_duoc_huy(r.get("custom_hddt_trang_thai")):
			ra["da_ky"] += 1
		if len(ra["vi_du"]) < 15:
			ra["vi_du"].append({
				"don": r.get("name"),
				"ma": r.get("custom_pancake_display_id") or "",
				"tien": flt(r.get("grand_total")),
				"hddt": r.get("custom_hddt_so") or "",
				"hddt_tt": r.get("custom_hddt_trang_thai") or "",
			})
	return ra


def _tap_huy(ds=None, ngay=None, tao_truoc=None):
	"""Doc tap hoa don se huy. Hai duong: liet ke thang, hoac theo tieu chi."""
	if isinstance(ds, str):
		ds = frappe.parse_json(ds) if ds.strip().startswith("[") else [
			x.strip() for x in ds.split(",") if x.strip()
		]
	loc = {"docstatus": 1}
	if ds:
		loc["name"] = ["in", list(ds)]
	else:
		if not ngay:
			frappe.throw("Phải nêu ngày ghi sổ hoặc danh sách hoá đơn cần huỷ.")
		loc["posting_date"] = str(ngay)
		loc["custom_pancake_id"] = ["is", "set"]
		if tao_truoc:
			# Loc theo NGAY LAP PHIEU chu khong theo ngay ghi so: dung de bat
			# dung nhung to bi keo tu ngay cu sang, con to sinh trong ngay
			# thi khong dinh toi.
			loc["creation"] = ["<", str(tao_truoc)]
	return frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=[
			"name", "posting_date", "creation", "grand_total", "customer",
			"custom_pancake_id", "custom_pancake_display_id",
			"custom_hddt_so", "custom_hddt_trang_thai", "vgb_quay",
		],
		order_by="name asc",
		limit_page_length=0,
	)


@frappe.whitelist()
def xem_truoc_huy_ghi_so(ds=None, ngay=None, tao_truoc=None):
	"""Xem tap hoa don se huy, KHONG ghi gi. Luon xem truoc roi hay huy."""
	_kiem_quyen_huy()
	return _mo_ta_huy(_tap_huy(ds, ngay, tao_truoc))


@frappe.whitelist()
def huy_ghi_so_hang_loat(ds=None, ngay=None, tao_truoc=None, ly_do=None, xoa_so_hddt=1):
	"""Huy ghi so ca loat hoa don ban, roi danh dau de an khoi man Sales.

	Bon buoc cho moi to:
	  1. cancel() dung nghiep vu - ERPNext dao nguoc but toan, hook cua he
	     rut lai diem da tich va tra so cho bang kiem banh.
	  2. Xoa so hoa don dien tu ben Next neu ben m-invoice da xoa: de lai
	     thi chuoi ky hang loat luc 23h van thay va van ky.
	  3. Danh dau vgb_huy de cac man danh sach loc ra.
	  4. Ghi vet ly do va nguoi bam.

	CHAN to DA KY: hoa don da ky la da nam ben co quan thue, huy ben Next
	ma khong xu ly ben thue la hai so lech nhau. To do phai di duong hoa
	don thay the, khong huy o day.
	"""
	_kiem_quyen_huy()
	if not (ly_do or "").strip():
		frappe.throw("Phải ghi lý do huỷ thì sau này còn biết vì sao.")
	tap = _tap_huy(ds, ngay, tao_truoc)
	if not tap:
		return {"ok": 1, "khong_co_to_nao": 1, "huy": 0}

	kq = {"chon": len(tap), "huy": 0, "bo_qua_da_ky": 0, "loi": [], "tong_tien": 0.0}
	for r in tap:
		if _khong_duoc_huy(r.get("custom_hddt_trang_thai")):
			kq["bo_qua_da_ky"] += 1
			kq["loi"].append(
				"Đơn %s đang ở trạng thái hoá đơn điện tử %s nên không huỷ ở đây, "
				"phải làm hoá đơn thay thế." % (r["name"], r.get("custom_hddt_trang_thai"))
			)
			continue
		try:
			doc = frappe.get_doc("Sales Invoice", r["name"])
			doc.flags.ignore_permissions = True
			doc.cancel()
			gt = {
				"vgb_huy": 1,
				"vgb_huy_ly_do": (ly_do or "").strip()[:500],
				"vgb_huy_luc": now_datetime(),
				"vgb_huy_boi": frappe.session.user,
			}
			if cint(xoa_so_hddt):
				gt["custom_hddt_so"] = None
				gt["custom_hddt_trang_thai"] = None
			frappe.db.set_value("Sales Invoice", r["name"], gt, update_modified=False)
			frappe.db.commit()
			_ghi_vet(
				"Sales Invoice", r["name"],
				"Huỷ ghi sổ hàng loạt. Lý do: %s" % (ly_do or "").strip(),
			)
			kq["huy"] += 1
			kq["tong_tien"] += flt(r.get("grand_total"))
		except Exception:
			frappe.db.rollback()
			frappe.local.message_log = []
			frappe.log_error(frappe.get_traceback(), "chung_tu: huy ghi so %s" % r["name"])
			if len(kq["loi"]) < 40:
				kq["loi"].append("Đơn %s huỷ lỗi, xem Error Log." % r["name"])
	frappe.db.commit()
	return kq

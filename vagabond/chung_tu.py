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
from frappe.utils import cint, now_datetime

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
		"nào, ở app hay trên máy tính đều vậy — mất chứng từ gốc là mất luôn "
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

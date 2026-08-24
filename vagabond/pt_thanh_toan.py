"""Phuong thuc thanh toan - mot noi khai duy nhat (anh Viet 12/08/2026).

Truoc day mot phuong thuc phai khai o SAU cho khac nhau trong ban_hang.py:
PT_THAM_CHIEU (logo, nhan o nhap, vi du, mau kiem), PT_QUAY (hien o man
quay), PT_PANCAKE (hien cho don online), PT_CHUA_VE_TIEN va PT_VE_SAU
(tien chua nam trong ket), PTTT_MINVOICE (ma gui sang co quan thue).

Them mot may ca the moi la phai sua ca sau cho. Quen mot cho thi khong ai
bao loi ngay - no lam lech so cua man chot ca, hoac to hoa don dien tu gui
sai ma hinh thuc thanh toan, den luc doi soat moi lo ra.

Nay gom ve mot noi, cat trong Vagabond Settings duoi dang JSON. An toan
khi deploy: chua ai luu gi thi doc ra MAC_DINH - dung y nguyen sau danh
sach cu.
"""

import json

import frappe
from frappe.utils import cint

from vagabond.lib import cfg

TRUONG = "vgb_pt_thanh_toan_ds"

# Tien ve luc nao. Anh huong man Chot ca: tien "ngay" phai nam trong ket,
# hai loai kia tach ra dong rieng de thu ngan khong bi lech khi dem tien.
TIEN_NGAY = "ngay"      # tien vao ngay: tien mat, the, chuyen khoan
TIEN_VE_SAU = "sau"     # ben thu ba giu roi tra sau: Grab Dine-Out
TIEN_CONG_NO = "cong_no"  # khach no, phai di doi

from vagabond.vai_cua_hang import VAI_QLCH

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager", VAI_QLCH}

# Ma hinh thuc thanh toan m-invoice nhan. Go bay mot ma la ca lo hoa don
# dien tu bi tra ve, ma loi thi hien ra tan ben co quan thue chu khong hien
# tren man cua minh.
MA_THUE = ("", "TM", "CK", "TM/CK")

# Ten phuong thuc bi CHOT CUNG vi con cho khac trong phan mem goi thang ten
# nay ra so sanh. Doi ten o day thi cho kia im lang hong, khong bao loi.
TEN_KHOA = {
	"Chuyển khoản": "đối soát SePay dò theo đúng tên này",
	"Công nợ": "phân hệ Công nợ phải thu lọc hoá đơn theo đúng tên này",
}

# Giu DUNG mau cu ben ban_hang.py: bill ca the in ca "So tham chieu" toan
# so lan "Ma chuan chi" chu va so, sales go cai nao ngan hon cung duoc.
MAU_BILL = r"^[A-Z0-9]{4,20}$"
LOI_BILL = (
	"Nhập Số tham chiếu (chỉ chữ số, ví dụ 621416783893) hoặc Mã chuẩn chi "
	"(chữ và số, ví dụ F62221) in trên bill cà thẻ."
)

# Sau danh sach cu gom lai. Thu tu o day chinh la thu tu hien tren man
# tinh tien.
MAC_DINH = [
	{
		"ten": "Tiền mặt", "lg": "/files/pt-tienmat.png",
		"quay": 1, "online": 1, "tien_ve": TIEN_NGAY, "minvoice": "TM",
	},
	{
		"ten": "Chuyển khoản", "lg": "/files/pt-mb.png",
		"quay": 1, "online": 1, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"nhan": "Nội dung chuyển khoản (SePay tự khớp, để trống cũng được)",
	},
	{
		"ten": "Thẻ - Payoo", "lg": "/files/pt-payoo5.png",
		"quay": 1, "online": 1, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"bat": 1, "nhan": "Số tham chiếu trên bill cà thẻ Payoo",
		"vd": "249853", "mau": MAU_BILL, "loi": LOI_BILL,
	},
	{
		"ten": "Thẻ - ShinhanBank", "lg": "/files/pt-shinhan5.png",
		"quay": 1, "online": 1, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"bat": 1, "nhan": "Số tham chiếu hoặc mã chuẩn chi trên bill ShinhanBank",
		"vd": "621416783893 hoặc F62221", "mau": MAU_BILL, "loi": LOI_BILL,
	},
	{
		"ten": "OnePay", "lg": "/files/pt-onepay.png",
		"quay": 1, "online": 1, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"nhan": "Order Reference của OnePay", "vd": "PL_VAGABOND_260801143012",
	},
	{
		# Khach mua voucher tren app Grab roi den quan an. Grab giu tien cua
		# hoa don do va chuyen ve cho tiem ngay T+1, nen phai tach rieng mot
		# phuong thuc de doi soat - khong duoc lan vao tien mat hay the.
		"ten": "Grab Dine-Out", "lg": "/assets/vagabond/images/pt-grab-dineout.png",
		"quay": 1, "online": 0, "tien_ve": TIEN_VE_SAU, "minvoice": "",
		"bat": 1,
		# Grab bao lai ngay 12/08/2026: ma doi soat cua Dine-Out bat dau bang
		# "GD-". Ma nay hien tren man xac nhan thanh toan trong app cua khach,
		# dong "Order". Cuoi thang doi soat file cua Grab chinh la khop theo
		# ma nay, nen bat go dung dang ngay tu luc chot bill - go sai mot ky
		# tu la thang do phai do tay.
		"nhan": "Mã đơn Grab Dine-Out trên máy khách", "vd": "GD-KKJDUSEH",
		"mau": r"^GD-[A-Z0-9]{4,20}$",
		"loi": "Mã Grab Dine-Out bắt đầu bằng GD- rồi tới chữ và số, ví dụ "
		"GD-KKJDUSEH. Nhờ khách đưa màn hình xác nhận thanh toán, dòng Order.",
	},
	{
		# Khach si (Ravie...) va khach VIP gom nhieu hoa don tra mot lan.
		"ten": "Công nợ", "ic": "📒",
		"quay": 1, "online": 1, "tien_ve": TIEN_CONG_NO, "minvoice": "",
		"nhan": "Tên hoặc mã khách công nợ", "vd": "Ravie",
	},
	# Bon phuong thuc duoi day di theo NGUON DON cua san, khong hien o man
	# chon phuong thuc - nhung van phai khai de con kiem ma don va gui dung
	# ma hinh thuc thanh toan sang co quan thue.
	{
		"ten": "GrabFood", "lg": "/files/pt-grab.png",
		"quay": 0, "online": 0, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"bat": 1, "nhan": "Mã đơn GrabFood", "vd": "GF-689",
		"mau": r"^GF-\d{1,10}$",
		"loi": "Mã đơn GrabFood có dạng GF- rồi tới số, ví dụ GF-689.",
	},
	{
		"ten": "BeFood", "lg": "/files/pt-befood.png",
		"quay": 0, "online": 0, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"bat": 1, "nhan": "Mã đơn BeFood (8 số)", "vd": "76481763",
		"mau": r"^\d{8}$",
		"loi": "Mã đơn BeFood gồm đúng 8 chữ số, ví dụ 76481763.",
	},
	{
		"ten": "GreenSM Food", "lg": "/files/pt-greensm.png",
		"quay": 0, "online": 0, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"bat": 1, "nhan": "Mã đơn GreenSM", "vd": "XSM-3621",
		"mau": r"^XSM-[A-Z0-9]{1,12}$",
		"loi": "Mã đơn GreenSM có dạng XSM- rồi tới mã, ví dụ XSM-3621.",
	},
	{
		"ten": "ShopeeFood", "lg": "/files/pt-shopee4.png",
		"quay": 0, "online": 0, "tien_ve": TIEN_NGAY, "minvoice": "CK",
		"bat": 1, "nhan": "Mã đơn ShopeeFood (4 số)", "vd": "3621",
		"mau": r"^\d{4}$",
		"loi": "Mã đơn ShopeeFood gồm đúng 4 chữ số, ví dụ 3621.",
	},
]


def _chuan(d, i=0):
	ten = str(d.get("ten") or "").strip()
	tv = str(d.get("tien_ve") or TIEN_NGAY).strip()
	if tv not in (TIEN_NGAY, TIEN_VE_SAU, TIEN_CONG_NO):
		tv = TIEN_NGAY
	lg = str(d.get("lg") or "").strip()
	# Logo phai la tep da tai len site nay. Khong cho tro ra ngoai: man hinh
	# nhan vien ma nap anh tu ten mien la thi vua lo dia chi tiem cho ben do,
	# vua co ngay anh bi doi ma minh khong biet.
	if lg and not lg.startswith("/"):
		lg = ""
	return {
		"ten": ten,
		"lg": lg,
		"ic": str(d.get("ic") or "").strip(),
		"quay": 1 if cint(d.get("quay")) else 0,
		"online": 1 if cint(d.get("online")) else 0,
		# bat = bat buoc nhap ma tham chieu moi cho chot bill
		"bat": 1 if cint(d.get("bat")) else 0,
		"nhan": str(d.get("nhan") or "").strip(),
		"vd": str(d.get("vd") or "").strip(),
		"mau": str(d.get("mau") or "").strip(),
		"loi": str(d.get("loi") or "").strip(),
		"tien_ve": tv,
		"minvoice": str(d.get("minvoice") or "").strip().upper(),
		# Khoa ben Pancake, tuc gia tri `type` trong payment_purchase_histories
		# (vi du "onepay", "mbbank"). Khai o day thay vi go cung trong ma
		# nguon: Pancake them vi moi thi khai mot dong, khong phai deploy.
		"khoa_pancake": str(d.get("khoa_pancake") or "").strip().lower(),
		"dung": 1 if cint(d.get("dung") if d.get("dung") is not None else 1) else 0,
		"thu_tu": cint(d.get("thu_tu") or (i + 1)),
	}


def ds(chi_dung=False):
	"""Toan bo phuong thuc, da chuan hoa va sap theo thu tu."""
	try:
		tho = json.loads((cfg().get(TRUONG) or "").strip() or "[]")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "pt_thanh_toan: cau hinh hong")
		tho = []
	if not isinstance(tho, list) or not tho:
		tho = MAC_DINH
	ra = [_chuan(d, i) for i, d in enumerate(tho)]
	ra = [d for d in ra if d["ten"]]
	if not ra:
		ra = [_chuan(d, i) for i, d in enumerate(MAC_DINH)]
	ra.sort(key=lambda d: (d["thu_tu"], d["ten"]))
	return [d for d in ra if d["dung"]] if chi_dung else ra


def theo_ten(ten):
	t = str(ten or "").strip()
	for d in ds():
		if d["ten"] == t:
			return d
	return None


def ten_quay():
	"""Phuong thuc hien o man tinh tien tai quay."""
	return [d["ten"] for d in ds(chi_dung=True) if d["quay"]]


def ten_online():
	"""Phuong thuc hien cho don Pancake."""
	return [d["ten"] for d in ds(chi_dung=True) if d["online"]]


def ma_minvoice(ten):
	"""Ma hinh thuc thanh toan gui sang co quan thue."""
	d = theo_ten(ten)
	return (d["minvoice"] if d else "") or "TM/CK"


def chua_ve_tien():
	"""Phuong thuc ma tien CHUA nam trong ket luc chot ca."""
	return [d["ten"] for d in ds() if d["tien_ve"] == TIEN_CONG_NO]


def ve_sau():
	"""Phuong thuc ben thu ba giu tien roi tra sau."""
	return [d["ten"] for d in ds() if d["tien_ve"] == TIEN_VE_SAU]


# Anh xa san cho hai kenh dang chay that, dung khi nguoi dung chua kip khai
# o Cai dat. Do tren du lieu that 15/08/2026: 285 giao dich mbbank va 41
# giao dich onepay trong bay ngay.
KHOA_PANCAKE_MAC_DINH = {
	"mbbank": "Chuyển khoản",
	"onepay": "OnePay",
}


def theo_khoa_pancake(khoa):
	"""Ten phuong thuc thanh toan tu khoa `type` cua Pancake.

	Uu tien cai dat nguoi dung khai; chua khai thi dung bang mac dinh; van
	khong ra thi tra rong de noi goi biet la CHUA BIET, chu khong doan bua.
	"""
	k = str(khoa or "").strip().lower()
	if not k:
		return ""
	for d in ds(chi_dung=True):
		if d.get("khoa_pancake") == k:
			return d["ten"]
	ten = KHOA_PANCAKE_MAC_DINH.get(k, "")
	# Ten mac dinh chi dung duoc khi phuong thuc do dang bat o Cai dat.
	return ten if ten in {d["ten"] for d in ds(chi_dung=True)} else ""


def bang_tham_chieu():
	"""Dang bang tra ten -> cau hinh, thay cho PT_THAM_CHIEU cu."""
	return {d["ten"]: d for d in ds()}


# ------------------------------------------------------------------ man app


@frappe.whitelist()
def danh_sach():
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return {
		"pt": ds(),
		"sua_duoc": 1 if QUYEN_SUA & set(frappe.get_roles()) else 0,
		"tien_ve": [
			{"k": TIEN_NGAY, "ten": "Tiền vào ngay"},
			{"k": TIEN_VE_SAU, "ten": "Bên thứ ba giữ, trả sau"},
			{"k": TIEN_CONG_NO, "ten": "Khách nợ, phải đi đòi"},
		],
	}


def _kiem(ra):
	import re

	if not ra:
		frappe.throw("Phải có ít nhất một phương thức thanh toán.")
	da_co = {}
	for d in ra:
		if not d["ten"]:
			frappe.throw("Có phương thức chưa đặt tên.")
		if d["ten"] in da_co:
			frappe.throw("Phương thức \"%s\" bị trùng tên." % d["ten"])
		da_co[d["ten"]] = 1
		if d["minvoice"] not in MA_THUE:
			frappe.throw(
				"Mã gửi cơ quan thuế của \"%s\" phải là TM, CK, TM/CK hoặc để "
				"trống. Ghi \"%s\" là cả lô hoá đơn điện tử bị trả về."
				% (d["ten"], d["minvoice"])
			)
		if d["mau"]:
			try:
				mau = re.compile(d["mau"])
			except Exception:
				frappe.throw(
					"Mẫu kiểm mã của \"%s\" không hợp lệ. Để trống nếu không "
					"muốn kiểm định dạng." % d["ten"]
				)
			# Vi du la cau thu ngan nhin vao ma go theo. Vi du khong khop mau
			# thi nguoi lam dung y hop dong van bi may chan - loi kieu nay
			# khong ai doan ra duoc dang dung o dau.
			vd = (d["vd"] or "").split(" hoặc ")[0].strip()
			if vd and not mau.match(vd):
				frappe.throw(
					"Ví dụ \"%s\" của \"%s\" không khớp chính mẫu kiểm vừa đặt. "
					"Thu ngân gõ đúng như ví dụ vẫn sẽ bị máy chặn." % (vd, d["ten"])
				)
		if d["bat"] and not d["nhan"]:
			frappe.throw(
				"Phương thức \"%s\" bắt buộc nhập mã tham chiếu thì phải ghi "
				"nhãn ô nhập, không thì thu ngân không biết phải gõ gì."
				% d["ten"]
			)
	for ten, vi in TEN_KHOA.items():
		if ten not in da_co:
			frappe.throw(
				"Không bỏ hay đổi tên phương thức \"%s\" được vì %s. Muốn ngừng "
				"dùng thì tắt nó đi." % (ten, vi)
			)
	if not [d for d in ra if d["dung"] and d["quay"]]:
		frappe.throw("Phải còn ít nhất một phương thức dùng được ở màn tính tiền tại quầy.")
	if not [d for d in ra if d["dung"] and d["online"]]:
		frappe.throw("Phải còn ít nhất một phương thức dùng được cho đơn online.")


def _kiem_nguon(ra):
	"""Moi nguon don dang bat phai con it nhat mot phuong thuc dung duoc.

	Nguon don cua san (GrabFood, ShopeeFood...) moi nguon chi di duy nhat
	mot phuong thuc cung ten. Tat phuong thuc do di la nguon do het duong
	chot bill, ma man Cai dat nay khong he noi cho ai biet.
	"""
	from vagabond import ban_hang, diem_ban

	dung = {d["ten"] for d in ra if d["dung"]}
	quay = {d["ten"] for d in ra if d["dung"] and d["quay"]}
	online = {d["ten"] for d in ra if d["dung"] and d["online"]}
	for d in diem_ban.ds(chi_bat=True):
		for n in d["nguon"]:
			if n == "Pancake":
				continue
			m = ban_hang.NGUON_META.get(n) or {}
			if m.get("pt"):
				con = set(m["pt"]) & dung
			else:
				con = quay if d["quay"] else online
			if not con:
				frappe.throw(
					"Nguồn đơn \"%s\" (điểm %s) không còn phương thức thanh "
					"toán nào dùng được. Bật lại %s, hoặc tắt nguồn đơn đó bên "
					"màn Điểm bán trước."
					% (n, d["ten"], " hoặc ".join(m.get("pt") or ["một phương thức"]))
				)


def _dang_dung(ten, loc=None):
	try:
		dk = {"vgb_pt_thanh_toan": ten}
		dk.update(loc or {})
		return frappe.db.count("Sales Invoice", dk)
	except Exception:
		return 0


def _mo_loi_next(ra):
	"""Khai luon phuong thuc moi sang Next.

	Ben Next (ERPNext) giu mot bang Mode of Payment rieng, va _kiem_pt ben
	ban_hang.py bat buoc ten phai co trong bang do moi cho chot bill. Neu
	khong tu khai thi man Cai dat nay noi doi: them mot dong xong, thu ngan
	chon vao la an "Chua khai phuong thuc thanh toan X ben Next" - ma khong
	ai biet phai vao dau de khai.
	"""
	for d in ra:
		ten = d["ten"]
		if frappe.db.exists("Mode of Payment", ten):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Mode of Payment",
					"mode_of_payment": ten,
					# General: khong rang buoc tai khoan ngan hang nao, vi he
					# minh chi ghi TEN phuong thuc len hoa don chu khong sinh
					# phieu thu tu bang nay.
					"type": "General",
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "pt_thanh_toan: khong khai duoc %s" % ten)
			frappe.throw(
				"Không khai được phương thức \"%s\" sang Next nên chưa lưu được. "
				"Nhờ kế toán khai tay trong Mode of Payment rồi lưu lại." % ten
			)


@frappe.whitelist()
def luu(pt=None):
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới sửa được phương thức thanh toán.")
	if isinstance(pt, str):
		pt = frappe.parse_json(pt or "[]")
	ra = [_chuan(d, i) for i, d in enumerate(pt or [])]
	ra = [d for d in ra if d["ten"]]
	_kiem(ra)
	_kiem_nguon(ra)

	# Ten phuong thuc la thu duoc GHI THANG vao tung hoa don, khong phai ma
	# tra bang. Bo mot ten da co hoa don la nhung to do tro thanh mo coi:
	# chot ca khong biet xep vao dau, bao cao theo phuong thuc mat mot cot.
	ten_moi = {d["ten"] for d in ra}
	con_dung = {d["ten"] for d in ra if d["dung"]}
	for cu in ds():
		if cu["ten"] not in ten_moi:
			n = _dang_dung(cu["ten"])
			if n:
				frappe.throw(
					"Phương thức \"%s\" đã có %d hoá đơn nên không bỏ khỏi danh "
					"sách được. Muốn ngừng dùng thì tắt nó đi, hoá đơn cũ vẫn "
					"đọc được." % (cu["ten"], n)
				)
			continue
		# Tat mot phuong thuc la no bien khoi danh sach hop le, nen nhung to
		# CHUA GHI SO dang mang phuong thuc do se khong ghi so duoc nua -
		# thu ngan om bill khong chot noi ma khong hieu tai sao.
		if cu["dung"] and cu["ten"] not in con_dung:
			n = _dang_dung(cu["ten"], {"docstatus": 0})
			if n:
				frappe.throw(
					"Đang còn %d hoá đơn chưa ghi sổ trả bằng \"%s\". Tắt bây "
					"giờ là mấy tờ đó kẹt lại, không ai ghi sổ được. Xử lý hết "
					"mấy tờ đó rồi hãy tắt." % (n, cu["ten"])
				)

	_mo_loi_next(ra)
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG, json.dumps(ra, ensure_ascii=False, indent=1)
	)
	frappe.db.commit()
	_ghi_vet(
		"Sửa phương thức thanh toán: %s"
		% ", ".join("%s%s" % (d["ten"], "" if d["dung"] else " (tắt)") for d in ra)
	)
	return danh_sach()


def _ghi_vet(viec):
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Vagabond Settings",
				"reference_name": "Vagabond Settings",
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass

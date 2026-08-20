# -*- coding: utf-8 -*-
"""Tao va sua ho so nha cung cap tu app, mot cua ngo lo du bon bang.

Vi sao tep nay ton tai
----------------------
Uyen thu tao nha cung cap tren app ngay 21/08/2026 va vap hai chuyen mot
luc. Mot, quyen: vai Purchase Manager cua Uyen co Sua ma khong co Tao, nen
may tra "khong co quyen truy cap doctype". Hai, form chi co bon o (ten,
nhom, ma so thue, loai) - thieu cho ghi email thi luong gui don mua hang
sau nay khong co dia chi, thieu so tai khoan thi den luc lap ho so thanh
toan lai phai mo Desk go tay.

Trong ERPNext, ho so mot nha cung cap KHONG nam trong mot bang. Ten va ma
so thue o `Supplier`, dia chi o `Address`, nguoi lien he va email o
`Contact`, so tai khoan o `Bank Account`. Bon bang, ba kieu lien ket khac
nhau (Dynamic Link cho dia chi va lien he, party cho tai khoan). Man hinh
khong nen biet chuyen do; no gui mot goi, cua ngo nay lo phan con lai.

Nguyen tac
----------
1. MOT LAN GHI, HONG THI KHONG DE LAI RAC. Tao Supplier truoc, roi dia chi,
   lien he, tai khoan. Ba cai sau hong thi ghi Error Log va van tra ve ma
   nha cung cap - khong dung ho so da tao, vi bat nguoi dung go lai tu dau
   con te hon la thieu mot o sua sau duoc.
2. EMAIL LA CUA NGO CUA DON MUA HANG NHUNG KHONG BAT BUOC. Anh Viet
   21/08/2026: co nha cung cap chi mua duoc qua app hay san thuong mai
   dien tu, ho khong co hom thu nao de gui don ca. Co email thi ghi vao CA
   HAI cho (o tren ho so va lien he chinh) vi `ho_so_tt._email_ncc` doc
   theo thu tu do; khong co thi de trong, don mua se mang kenh khac Email.
3. MA SO THUE tra cuu bang `vagabond.api.tra_mst` (VietQR, da chay san cho
   hoa don va bao gia). Tra cuu chi DIEN HO vao o tren man; nguoi dung van
   nhin thay va sua duoc truoc khi bam Luu. May khong tu ghi thang vao co
   so du lieu tu ket qua tra cuu.
"""

# ------------------------------------------------------------ phan thuan
# Ham thuan tren `import frappe`: bo kiem thu nap bang python3 tran.

LOAI_HOP_LE = ("Company", "Individual")


def chuan_mst(mst):
	"""Ma so thue ve dang chuan: 10 so, 12 so, hoac 10-3 co gach ngang.

	Ma chi nhanh 13 so PHAI giu dau gach (Thong tu 86/2024/TT-BTC), giong
	het cach `api.tra_mst` chuan hoa - hai noi lech nhau la tra cuu ra mot
	dang ma luu xuong mot dang khac.
	"""
	so = "".join(ch for ch in str(mst or "") if ch.isdigit())
	if len(so) in (10, 12):
		return so
	if len(so) == 13:
		return so[:10] + "-" + so[10:]
	return ""


def thieu_o_nao(goi):
	"""Danh sach o bat buoc con trong. Tra ve [] la du de ghi.

	EMAIL KHONG BAT BUOC (anh Viet 21/08/2026): *"co nhung NCC khong mua qua
	email, ma phai mua qua app, san thuong mai dien tu..."*. Bat buoc mot o
	ma nghiep vu khong can la ep nguoi dung go bua mot dia chi cho qua cua -
	roi thu don mua hang bay vao mot hom thu khong ai doc.

	He da co cot "Kenh dat hang" tren don mua (Email, Zalo, App nha cung
	cap, Mua truc tiep) va don kenh khac Email tu mang trang thai "Khong mua
	qua email", nen thieu email khong lam hong duong nao ca.
	"""
	thieu = []
	if not str(goi.get("ten") or "").strip():
		thieu.append("Tên nhà cung cấp")
	if not str(goi.get("nhom") or "").strip():
		thieu.append("Nhóm nhà cung cấp")
	return thieu


def loc_email_cc(ds):
	"""Danh sach email CC sach: bo trong, bo trung, giu thu tu nguoi go.

	Nhan ca chuoi ngan cach bang dau phay lan danh sach, vi man hinh gui
	ba o rieng con cho khac trong he lai luu mot chuoi.
	"""
	if isinstance(ds, str):
		ds = ds.replace(";", ",").split(",")
	ra, da = [], set()
	for x in (ds or []):
		e = str(x or "").strip()
		if not e:
			continue
		khoa = e.lower()
		if khoa in da:
			continue
		da.add(khoa)
		ra.append(e)
	return ra


def email_hop_le(email):
	"""Phep kiem toi thieu: co mot @ va sau @ co dau cham.

	Khong dung bieu thuc chinh quy dai: o day chi can chan loi go thieu
	".com" - dung cai loi da lam ca don hang khong vao duoc he ngay
	16/08/2026.
	"""
	e = str(email or "").strip()
	if e.count("@") != 1:
		return False
	ten, mien = e.split("@")
	return bool(ten) and "." in mien and not mien.startswith(".") and not mien.endswith(".")


# ------------------------------------------------------- phan can Frappe

import frappe
from frappe.utils import cint

VAI_SUA = {"System Manager", "Thu mua", "Purchase Manager", "Purchase Master Manager",
           "Accounts Manager", "Accounts User", "Giám đốc", "AP Giám đốc"}

TRUONG_MOI = {
	"Supplier": [
		{
			"fieldname": "email_cc", "label": "Email phụ cần CC",
			"fieldtype": "Small Text", "insert_after": "email_id",
			"description": (
				"Các địa chỉ cần CC khi gửi đơn mua hàng, cách nhau bằng dấu "
				"phẩy. Nhiều nhà cung cấp muốn cả kế toán và kho cùng nhận "
				"một thư."
			),
		},
	]
}


def _kiem_quyen():
	if not VAI_SUA & set(frappe.get_roles()):
		frappe.throw(
			"Tài khoản của anh chị chưa được mở quyền tạo nhà cung cấp. Nhờ "
			"anh Việt hoặc chị Dung cấp vai Thu mua giúp."
		)


@frappe.whitelist()
def danh_muc():
	"""Nhung thu man hinh can de ve form: nhom nha cung cap va danh muc ngan hang."""
	_kiem_quyen()
	return {
		"nhom": frappe.get_all(
			"Supplier Group", filters={"is_group": 0}, pluck="name",
			order_by="name asc", limit_page_length=0,
		),
		"ngan_hang": frappe.get_all(
			"Bank", pluck="name", order_by="name asc", limit_page_length=0,
		),
	}


def _gan_dia_chi(ma_ncc, ten_ncc, dia_chi, tinh=None):
	"""Ghi dia chi va noi vao nha cung cap bang Dynamic Link."""
	d = frappe.get_doc({
		"doctype": "Address",
		"address_title": ten_ncc[:100],
		"address_type": "Billing",
		"address_line1": dia_chi[:240],
		"city": (tinh or "").strip() or None,
		"country": "Vietnam",
		"is_primary_address": 1,
		"links": [{"link_doctype": "Supplier", "link_name": ma_ncc}],
	})
	d.flags.ignore_permissions = True
	d.insert(ignore_permissions=True)
	return d.name


def _gan_lien_he(ma_ncc, ten_ncc, nguoi, email, dien_thoai, cc=None):
	"""Ghi nguoi lien he, danh dau la lien he CHINH.

	Danh dau chinh khong phai de cho dep: `ho_so_tt._email_ncc` va duong gui
	don mua hang deu doc `supplier_primary_contact` truoc tien.
	"""
	ten = (nguoi or "").strip() or ten_ncc
	phan = ten.split(" ", 1)
	doc = frappe.get_doc({
		"doctype": "Contact",
		"first_name": phan[0][:60] or ten_ncc[:60],
		"last_name": (phan[1] if len(phan) > 1 else "")[:60],
		"is_primary_contact": 1,
		"links": [{"link_doctype": "Supplier", "link_name": ma_ncc}],
	})
	if email:
		doc.append("email_ids", {"email_id": email, "is_primary": 1})
	# Email CC nam CUNG mot lien he, danh dau khong phai chinh. De day thi
	# hop soan thu cua Frappe goi y duoc, ma duong doc email chinh cua
	# `ho_so_tt._email_ncc` van chi thay dia chi chinh.
	for e in (cc or []):
		if email and e.strip().lower() == email.strip().lower():
			continue
		doc.append("email_ids", {"email_id": e, "is_primary": 0})
	if dien_thoai:
		doc.append("phone_nos", {"phone": dien_thoai, "is_primary_mobile_no": 1})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	# Hai duong doc email deu phai ra ket qua: o tren ho so va lien he chinh.
	dat = {"supplier_primary_contact": doc.name}
	if email:
		dat["email_id"] = email
	if dien_thoai:
		dat["mobile_no"] = dien_thoai
	frappe.db.set_value("Supplier", ma_ncc, dat)
	return doc.name


def _gan_tai_khoan(ma_ncc, ten_ncc, so_tk, ngan_hang, chu_tk):
	"""So tai khoan nhan tien. Doc lai boi ho_so_tt._tk_nhan khi lap ho so chi."""
	if not so_tk:
		return ""
	nh = (ngan_hang or "").strip()
	if nh and not frappe.db.exists("Bank", nh):
		# Ngan hang la danh muc co san cua ERPNext. Go tay mot cai ten la
		# khong khop danh muc; bo trong con hon ghi sai roi doi soat khong ra.
		nh = ""
	doc = frappe.get_doc({
		"doctype": "Bank Account",
		"account_name": (chu_tk or "").strip() or ten_ncc[:120],
		"bank": nh or None,
		"bank_account_no": so_tk,
		"party_type": "Supplier",
		"party": ma_ncc,
		"is_default": 1,
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def tao(ten=None, nhom=None, mst=None, loai="Company", dia_chi=None, tinh=None,
        nguoi_lien_he=None, email=None, dien_thoai=None,
        so_tk=None, ngan_hang=None, chu_tk=None,
        email_cc=None, email_cc2=None, email_cc3=None):
	"""Lap ho so nha cung cap day du tu mot goi cua man hinh.

	Tra ve ma nha cung cap, kem danh sach phan nao ghi duoc va phan nao
	khong - de man hinh noi that voi nguoi dung thay vi bao "xong" chung
	chung.
	"""
	_kiem_quyen()
	goi = {"ten": ten, "nhom": nhom, "email": email}
	thieu = thieu_o_nao(goi)
	if thieu:
		frappe.throw("Còn thiếu: %s. Điền nốt rồi bấm Lưu lại giúp em." % ", ".join(thieu))
	# Email khong bat buoc, nhung DA GO thi phai dung dang. Bo trong khac
	# han go sai: bo trong la co y, con go sai la thu bay vao hu khong.
	email = str(email or "").strip()
	if email and not email_hop_le(email):
		frappe.throw(
			"Email \"%s\" trông chưa đúng - kiểm lại xem có thiếu dấu chấm "
			"hay phần đuôi không (ví dụ .com). Đơn mua hàng gửi qua email "
			"này nên sai một ký tự là thư không tới." % email
		)
	cc = loc_email_cc([email_cc, email_cc2, email_cc3])
	sai_cc = [e for e in cc if not email_hop_le(e)]
	if sai_cc:
		frappe.throw(
			"Email CC \"%s\" trông chưa đúng. Sửa lại hoặc bỏ trống giúp em."
			% ", ".join(sai_cc)
		)
	ten = str(ten).strip()
	nhom = str(nhom).strip()
	if not frappe.db.exists("Supplier Group", nhom):
		frappe.throw("Không có nhóm nhà cung cấp \"%s\". Chọn lại trong danh sách giúp em." % nhom)
	if loai not in LOAI_HOP_LE:
		loai = "Company"
	so_thue = chuan_mst(mst)
	if mst and not so_thue:
		frappe.throw(
			"Mã số thuế phải là 10, 12 hoặc 13 chữ số. Đang nhận \"%s\". Bỏ "
			"trống cũng được, điền sau vẫn kịp." % mst
		)
	# Trung ma so thue thi dung lai: hai ho so cung mot MST la cong no tach
	# lam doi, va den luc doi chieu hoa don thi khong biet ghi vao ho so nao.
	if so_thue:
		trung = frappe.db.get_value("Supplier", {"tax_id": so_thue}, ["name", "supplier_name"])
		if trung:
			frappe.throw(
				"Mã số thuế %s đã có trong hệ: %s (%s). Mở hồ sơ đó ra sửa, "
				"đừng lập thêm hồ sơ thứ hai cho cùng một nhà cung cấp."
				% (so_thue, trung[1] or trung[0], trung[0])
			)
	trung_ten = frappe.db.exists("Supplier", {"supplier_name": ten})
	if trung_ten:
		frappe.throw(
			"Đã có nhà cung cấp tên \"%s\" trong hệ. Nếu đúng là nhà đó thì "
			"mở hồ sơ cũ ra sửa; nếu là nhà khác thì thêm chi tiết vào tên "
			"cho phân biệt được." % ten
		)

	doc = frappe.get_doc({
		"doctype": "Supplier",
		"supplier_name": ten,
		"supplier_group": nhom,
		"supplier_type": loai,
		"tax_id": so_thue or None,
		"country": "Vietnam",
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)

	xong, hong = [], []
	dia_chi = str(dia_chi or "").strip()
	if dia_chi:
		try:
			_gan_dia_chi(doc.name, ten, dia_chi, tinh)
			xong.append("địa chỉ")
		except Exception:
			hong.append("địa chỉ")
			frappe.log_error(frappe.get_traceback(), "nha_cung_cap: ghi dia chi %s" % doc.name)
	if email or dien_thoai or (nguoi_lien_he or "").strip() or cc:
		try:
			_gan_lien_he(doc.name, ten, nguoi_lien_he, email, dien_thoai, cc)
			xong.append("người liên hệ")
		except Exception:
			hong.append("người liên hệ")
			frappe.log_error(frappe.get_traceback(), "nha_cung_cap: ghi lien he %s" % doc.name)
	if cc:
		try:
			frappe.db.set_value("Supplier", doc.name, "email_cc", ", ".join(cc))
			xong.append("%d email CC" % len(cc))
		except Exception:
			hong.append("email CC")
			frappe.log_error(frappe.get_traceback(), "nha_cung_cap: ghi email cc %s" % doc.name)
	so_tk = "".join(ch for ch in str(so_tk or "") if ch.isalnum())
	if so_tk:
		try:
			_gan_tai_khoan(doc.name, ten, so_tk, ngan_hang, chu_tk)
			xong.append("tài khoản ngân hàng")
		except Exception:
			hong.append("tài khoản ngân hàng")
			frappe.log_error(frappe.get_traceback(), "nha_cung_cap: ghi tai khoan %s" % doc.name)

	frappe.db.commit()
	ghi = "Đã lập hồ sơ %s." % doc.name
	if xong:
		ghi += " Kèm " + ", ".join(xong) + "."
	if hong:
		ghi += (" Riêng %s chưa ghi được, anh chị mở hồ sơ trên Desk bổ sung "
		        "giúp em." % ", ".join(hong))
	return {"ok": 1, "ma": doc.name, "ten": ten, "xong": xong, "hong": hong, "ghi_chu": ghi}


@frappe.whitelist()
def chi_tiet(ma=None):
	"""Ho so mot nha cung cap, gom du bon bang - de man hinh mo ra sua."""
	_kiem_quyen()
	if not ma or not frappe.db.exists("Supplier", ma):
		frappe.throw("Không tìm thấy nhà cung cấp %s. Quay lại danh sách rồi mở lại giúp em." % ma)
	d = frappe.get_doc("Supplier", ma)
	ra = {
		"ma": d.name, "ten": d.supplier_name, "nhom": d.supplier_group,
		"loai": d.supplier_type, "mst": d.get("tax_id") or "",
		"email": d.get("email_id") or "", "dien_thoai": d.get("mobile_no") or "",
		"ngung": cint(d.get("disabled")),
		"dia_chi": "", "nguoi_lien_he": "",
		"so_tk": "", "ngan_hang": "", "chu_tk": "",
	}
	dc = frappe.db.sql(
		"""select a.address_line1, a.city from `tabAddress` a
		inner join `tabDynamic Link` l on l.parent = a.name
		where l.link_doctype = 'Supplier' and l.link_name = %s
		order by a.is_primary_address desc limit 1""", ma, as_dict=True,
	)
	if dc:
		ra["dia_chi"] = dc[0].address_line1 or ""
		ra["tinh"] = dc[0].city or ""
	if d.get("supplier_primary_contact"):
		c = frappe.db.get_value(
			"Contact", d.supplier_primary_contact,
			["first_name", "last_name", "email_id", "mobile_no"], as_dict=True,
		) or {}
		ra["nguoi_lien_he"] = (" ".join(
			[c.get("first_name") or "", c.get("last_name") or ""]
		)).strip()
		ra["email"] = ra["email"] or (c.get("email_id") or "")
	ra["email_cc"] = frappe.db.get_value("Supplier", ma, "email_cc") or ""
	tk = frappe.get_all(
		"Bank Account", filters={"party_type": "Supplier", "party": ma},
		fields=["account_name", "bank_account_no", "bank"],
		order_by="is_default desc, modified desc", limit_page_length=1,
	)
	if tk:
		ra["chu_tk"] = tk[0].account_name or ""
		ra["so_tk"] = tk[0].bank_account_no or ""
		ra["ngan_hang"] = tk[0].bank or ""
	return ra

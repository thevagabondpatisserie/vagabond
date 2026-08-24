"""Tru diem cua khach tai quay, co xac thuc bang ma OTP gui qua Zalo ZNS.

Chot voi anh Viet 16/08/2026.

Vi sao luu OTP vao Doctype chu khong vao Redis
----------------------------------------------
Redis tren Frappe Cloud bay sach moi lan deploy: dung luc khach dang cam
dien thoai doc ma cho thu ngan thi ma boc hoi giua chung. Nhung ly do chinh
khong phai do. Diem la TIEN cua khach, nen mot luot tru diem la mot chung
cu: ba thang sau khach hoi "sao toi mat 50.000 diem" thi phai tra loi duoc
ma gui luc may gio, toi so nao, thu ngan nao bam, gan vao hoa don nao.
Redis khong giu duoc cau tra loi do.

Toc do khong phai van de: mot luot la mot INSERT va mot SELECT co chi muc,
tinh bang phan nghin giay, trong khi goi Zalo ZNS mat 300 den 800 phan
nghin giay. Toi uu hat cat ben canh hon da thi khong duoc gi.

Ba lop chan, cho ba moi lo khac nhau
------------------------------------
1. Ke ngoai do ma      -> ma song co han, sai 3 lan la chet ma, 3 ma chet
                          lien tiep la khoa khach 30 phut (mo som can OTP
                          quan ly).
2. Nguoi trong nha     -> MA CHI GUI TOI SO TRONG HO SO KHACH. Man hinh
                          KHONG co o nao go so. Day la lop quan trong
                          nhat: cho go so tay thi ca tang OTP thanh trang
                          tri, thu ngan go so cua chinh minh la xong.
3. So lieu bi be       -> so diem duyet duoc GHI VAO BAN GHI OTP luc xin
                          ma. Pha xac nhan KHONG nhan lai so diem tu may
                          khach. Khong co buoc nay thi xin ma cho 100 diem
                          roi gui len 100.000 diem la an, vi tin ZNS khach
                          nhan van ghi 100 diem.

QT-19: moi con so deu tinh lai o may chu, khong tin may khach.
QT-20: khong sua but cu, chi ghi but nguoc.
"""

import hashlib
import re
import secrets
from datetime import timedelta

import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, flt, now_datetime

from vagabond import zalo
from vagabond.lib import cfg, sdt84

DT_OTP = "Vagabond OTP"
SO_DIEM = "Vagabond So Diem"
SI = "Sales Invoice"

MUC_DICH = "Dung diem"
LOAI_TRU = "Dung diem tru vao don"
LOAI_HOAN = "Hoan lai diem da dung"

# Mac dinh khi Cai dat chua khai, hoac khai roi ma cot chua kip Migrate.
# Bai hoc v177: dung dat ma nguon phu thuoc vao mot cot vua khai, vi
# after_migrate KHONG chay sau moi lan deploy.
MD_QUY_DOI = 1.0  # 1 diem = 1 dong (anh Viet chot 16/08/2026)
MD_TRAN_PT = 50.0  # toi da 50% gia tri bill
MD_OTP_GIAY = 180  # anh Viet chot 180 giay thay vi 60
MD_BILL_TOI_THIEU = 10000.0  # bill sau khi tru khong duoc thap hon muc nay

SAI_TOI_DA = 3
MA_CHET_KHOA = 3  # bao nhieu ma chet lien tiep thi khoa khach
KHOA_PHUT = 30

# Hang KHONG duoc tieu diem. Chot cuoi cung cua anh Viet 16/08/2026.
#
# Danh sach nay doi ba lan trong mot ngay: cam, roi cho, roi cam lai. Ghi ra
# day de nguoi doc ma nguon sau nay khong tuong la go sot, va de neu co ai
# hoi "sao khach AMBASSADOR khong tieu duoc diem" thi biet ngay day la co y.
#
# AMBASSADOR va FAMILY: da nhan uu dai giam thang 10% va 20% tren moi bill,
# nen khong nhan them duong tieu diem nua.
# OWNER: bill da giam 100%, khong con gi de tru; tru diem tren bill 0 dong
# la dot diem cua chinh minh. Xem vagabond/noi_bo.py.
HANG_CAM_TIEU = {"AMBASSADOR", "FAMILY", "OWNER"}


# Truong tu them do MA NGUON khai, dung lai sau moi lan Migrate.
TRUONG_MOI = {
	"Sales Invoice": [
		{
			"fieldname": "vgb_giam_diem",
			"label": "Giảm giá từ điểm thành viên (đ)",
			"fieldtype": "Currency",
			"insert_after": "discount_amount",
			"read_only": 1,
			"description": (
				"Phần giảm giá đến TỪ ĐIỂM của khách. Tách riêng khỏi "
				"discount_amount vì nhịp đồng bộ Pancake ghi đè discount_amount "
				"vô điều kiện mỗi 30 phút; ghi thẳng vào đó thì giảm giá từ điểm "
				"biến mất trong khi bút trừ điểm vẫn nằm trong sổ."
			),
		}
	]
}


# ------------------------------------------------------------------ cai dat


def _cd():
	"""Doc cau hinh, roi ve mac dinh khi cot chua ton tai."""
	try:
		c = cfg()
	except Exception:
		return {
			"quy_doi": MD_QUY_DOI,
			"tran_pt": MD_TRAN_PT,
			"otp_giay": MD_OTP_GIAY,
			"bill_toi_thieu": MD_BILL_TOI_THIEU,
			"gia_lap": 1,
			"mau_zns": "",
		}
	return {
		"quy_doi": flt(c.get("diem_quy_doi")) or MD_QUY_DOI,
		"tran_pt": flt(c.get("diem_tran_pt")) or MD_TRAN_PT,
		"otp_giay": cint(c.get("diem_otp_giay")) or MD_OTP_GIAY,
		"bill_toi_thieu": flt(c.get("diem_bill_toi_thieu")) or MD_BILL_TOI_THIEU,
		# Chua co mau ZNS that thi TU DONG chay che gia lap, khong cho
		# nguoi dung tuong la da gui that.
		"gia_lap": 1 if (cint(c.get("diem_zns_gia_lap")) or not (c.get("zns_template_diem") or "").strip()) else 0,
		"mau_zns": (c.get("zns_template_diem") or "").strip(),
	}


# ------------------------------------------------------------ phep tinh THUAN
#
# Bon ham duoi day khong doc co so du lieu, khong ghi gi. Tach ra de bo kiem
# thu chay duoc ma khong can site (xem kiem_diem_otp.py).


def tien_tu_diem(diem, quy_doi=MD_QUY_DOI):
	"""Bao nhieu diem thi duoc bao nhieu dong. Lam tron xuong."""
	d = flt(diem)
	qd = flt(quy_doi)
	if d <= 0 or qd <= 0:
		return 0.0
	return float(int(d * qd))


def tran_dung_duoc(tong_bill, so_du, quy_doi=MD_QUY_DOI, tran_pt=MD_TRAN_PT, toi_thieu=MD_BILL_TOI_THIEU):
	"""So diem toi da mot bill nay nhan duoc. THUAN.

	Ba tran cung luc, lay cai chat nhat:
	  - khong qua so du cua khach
	  - khong qua tran_pt phan tram gia tri bill
	  - bill sau khi tru khong duoc thap hon toi_thieu
	"""
	tong = flt(tong_bill)
	# KHONG roi ve mac dinh khi quy_doi bang 0.
	#
	# Bo kiem thu bat duoc cho nay: viet `flt(quy_doi) or MD_QUY_DOI` thi
	# mot cau hinh ty le 0 se am tham thanh ty le 1. Nguoc lai neu tra tran
	# lon ma tien quy doi bang 0 thi khach dot 50.000 diem de duoc giam 0 d.
	# Ty le 0 nghia la diem khong doi ra tien duoc, va cau tra loi dung la
	# khong cho tieu diem. Cua roi-ve-mac-dinh nam o _cd(), la tang cau
	# hinh, chu khong nam trong phep tinh.
	qd = flt(quy_doi)
	if tong <= 0 or qd <= 0:
		return 0
	tran_tien = tong * flt(tran_pt) / 100.0
	con_lai = tong - flt(toi_thieu)
	if con_lai < tran_tien:
		tran_tien = con_lai
	if tran_tien <= 0:
		return 0
	return int(min(flt(so_du), tran_tien / qd))


def kiem_so_diem(xin, tong_bill, so_du, quy_doi=MD_QUY_DOI, tran_pt=MD_TRAN_PT, toi_thieu=MD_BILL_TOI_THIEU):
	"""So diem nay dung duoc khong. Tra (so_diem_duyet, cau_bao_loi). THUAN.

	Cau bao loi viet theo QT-24: noi luon nguoi dung lam gi tiep.
	"""
	try:
		d = int(flt(xin))
	except (TypeError, ValueError):
		return 0, "Số điểm phải là số nguyên. Vui lòng nhập lại."
	if d <= 0:
		return 0, "Số điểm phải lớn hơn 0. Vui lòng nhập lại."
	if flt(xin) != d:
		return 0, "Số điểm phải là số nguyên, không có phần lẻ. Vui lòng nhập lại."
	if d > flt(so_du):
		return 0, "Khách chỉ còn %s điểm nên không dùng %s điểm được. Nhập lại số nhỏ hơn." % (
			_so(so_du),
			_so(d),
		)
	tran = tran_dung_duoc(tong_bill, so_du, quy_doi, tran_pt, toi_thieu)
	if tran <= 0:
		return 0, (
			"Đơn %s đ này nhỏ quá nên chưa dùng điểm được. Đơn phải trên %s đ thì mới trừ điểm."
			% (_so(tong_bill), _so(flt(toi_thieu) * 2))
		)
	if d > tran:
		return 0, (
			"Đơn này chỉ dùng được tối đa %s điểm (bằng %s%% giá trị đơn). Nhập lại số nhỏ hơn."
			% (_so(tran), _so(tran_pt))
		)
	return d, ""


def _so(n):
	"""So co dau cham ngan, de doc trong cau bao loi."""
	try:
		return "{:,.0f}".format(flt(n)).replace(",", ".")
	except Exception:
		return str(n)


# ------------------------------------------------------------------- ma OTP


def _bam(chuoi):
	"""Bam kem muoi rieng cua site. Dung CUNG cach voi dang_nhap._bam.

	Ma OTP KHONG BAO GIO luu dang chu: nguoi doc duoc bang cung khong doi
	nguoc ra ma, va ma khong bao gio tra ve trinh duyet cua thu ngan.
	"""
	muoi = frappe.local.conf.get("encryption_key") or frappe.local.site
	return hashlib.sha256(("vgb:" + str(muoi) + ":" + str(chuoi)).encode()).hexdigest()


def _sinh_ma():
	return "".join(secrets.choice("0123456789") for _ in range(6))


def _gui_zns(so84, ma, ten_khach, so_diem, so_tien):
	"""Gui tin xac nhan. Tra (thanh_cong, loi, la_gia_lap).

	Che gia lap: anh Viet dang lam viec voi Zalo de duyet mau tin. Trong
	luc cho, ham nay tra Success de chay thu duoc luong logic noi bo.

	Ma trong che gia lap KHONG in ra tra ve, van chi ghi vao nhat ky he
	thong. Muon xem thi dung xem_ma_gia_lap() - chi System Manager, va chi
	chay khi che gia lap dang bat.
	"""
	c = _cd()
	if c["gia_lap"]:
		frappe.log_error(
			title="Vagabond: ZNS gia lap (tru diem)",
			message="So %s | khach %s | %s diem | %s d\nMa: %s" % (so84, ten_khach, so_diem, so_tien, ma),
		)
		return True, "", True
	# CHI GUI DUNG MOT THAM SO: otp.
	#
	# Mau 623902 anh Viet dang ky voi Zalo la "Mau OTP" va khai dung MOT
	# tham so <otp>, kieu string, do dai 10. Gui kem cac tham so mau khong
	# khai (ten_khach, so_diem, so_tien, phut) thi Zalo tu choi CA TIN, va
	# khach khong nhan duoc ma nao.
	#
	# Cach lam nay giong y mau dang nhap 622530 dang chay tot, xem
	# dang_nhap._gui_zns.
	#
	# DANH DOI PHAI BIET: tin khach nhan duoc chi co ma so, khong noi ro
	# dang duyet tru bao nhieu diem va giam bao nhieu tien. Khach gat dau
	# ma khong thay minh gat dau cho cai gi. So diem van duoc khoa chac o
	# may chu (ghi vao ban ghi OTP luc xin ma, pha xac nhan khong nhan lai
	# so tu may khach), nen khong ai be duoc con so; nhung lop "khach tu
	# doc thay" thi mat. Muon co lai thi phai dang ky mot mau ZNS moi co
	# du cac tham so ten_khach, so_diem, so_tien, roi sua lai dict nay.
	xong, loi = zalo.gui_tin(
		cfg(),
		so84,
		c["mau_zns"],
		{"otp": ma},
		dau_vet="vgb-diem-%s" % so84,
	)
	return xong, loi, False


# --------------------------------------------------------------- doc du lieu


def _so_du(khach):
	"""So du diem CONG LAI TU SO, khong doc o tong hop tren Customer.

	QT-19. O vgb_diem tren Customer chi la ban tong hop, lech luc nao thi
	tinh lai tu so.
	"""
	tong = frappe.db.sql("select sum(diem) from `tab%s` where khach = %%s" % SO_DIEM, (khach,))
	return flt((tong or [[0]])[0][0])


def _sdt_khach(khach):
	"""So dien thoai nhan ma, lay tu ho so khach. KHONG nhan tu may khach."""
	from vagabond.khach_hang import _lien_he

	try:
		return sdt84(_lien_he(khach).get("sdt"))
	except Exception:
		return ""


def _hoa_don(si_name):
	d = frappe.db.get_value(
		SI,
		si_name,
		["name", "customer", "grand_total", "docstatus", "vgb_huy", "custom_hddt_so", "vgb_khach_no", "vgb_giam_diem"],
		as_dict=True,
	)
	if not d:
		frappe.throw("Không có hoá đơn %s." % si_name)
	return d


def _khach_cua_don(si):
	"""Khach an diem cua don nay. Uu tien o khach than thiet tren don."""
	from vagabond.khach_hang import la_khach_gop

	kh = (si.get("vgb_khach_no") or "").strip() or (si.get("customer") or "").strip()
	return "" if la_khach_gop(kh) else kh


def _da_ghi(si_name, loai):
	"""Don nay da co but loai do chua. Chan ghi hai lan."""
	try:
		return frappe.db.exists(SO_DIEM, {"hoa_don": si_name, "loai": loai})
	except Exception:
		return None


def _diem_da_tru(si_name):
	"""Tong so diem DA TRU cho don nay, doc tu so. Tra so duong."""
	r = frappe.db.sql(
		"select sum(diem) from `tab%s` where hoa_don = %%s and loai = %%s" % SO_DIEM,
		(si_name, LOAI_TRU),
	)
	return abs(flt((r or [[0]])[0][0]))


# ------------------------------------------------------------------ kiem tra


def _kiem_don_con_tru_duoc(si):
	"""Hoa don nay con nhan duoc luot tru diem khong. Nem loi neu khong."""
	if cint(si.get("docstatus")) != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ nên không trừ điểm được nữa. Cần trừ thì báo "
			"kế toán huỷ hoá đơn rồi lập lại." % si["name"]
		)
	if cint(si.get("vgb_huy")):
		frappe.throw("Hoá đơn %s đã huỷ nên không trừ điểm được. Vui lòng lập bill mới." % si["name"])
	if (si.get("custom_hddt_so") or "").strip():
		frappe.throw(
			"Hoá đơn %s đã xuất hoá đơn điện tử số %s nên không đổi được số tiền. "
			"Cần trừ điểm thì phải huỷ hoá đơn điện tử trước." % (si["name"], si["custom_hddt_so"])
		)


def _kiem_khach_tieu_duoc(khach):
	"""Hang cua khach co duoc tieu diem khong."""
	hang = (frappe.db.get_value("Customer", khach, "vgb_hang") or "").strip()
	if hang.upper() in HANG_CAM_TIEU:
		frappe.throw(
			"Hạng %s nhận ưu đãi giảm giá thẳng trên bill nên không dùng điểm được. Vui lòng áp mức giảm của hạng cho khách." % hang
		)
	return hang


def _dang_bi_khoa(khach):
	"""Khach nay dang bi khoa vi do ma khong. Tra so phut con lai, 0 la khong.

	Dem so ma CHET (sai du SAI_TOI_DA lan) trong KHOA_PHUT vua qua. Khong
	dem ma het han binh thuong: khach doc cham khong phai la ke do ma.
	"""
	tu = now_datetime() - timedelta(minutes=KHOA_PHUT)
	n = frappe.db.count(
		DT_OTP,
		{
			"khach": khach,
			"muc_dich": MUC_DICH,
			"so_lan_sai": [">=", SAI_TOI_DA],
			"creation": [">", tu],
		},
	)
	return KHOA_PHUT if n >= MA_CHET_KHOA else 0


# ------------------------------------------------------------- pha 1: xin ma


@frappe.whitelist()
@rate_limit(limit=30, seconds=600)
def xin_ma(si_name=None, so_diem=None):
	"""Sinh ma va gui ZNS toi so cua khach. KHONG tru diem o buoc nay.

	So diem duyet duoc ghi thang vao ban ghi OTP. Pha xac nhan doc tu do
	chu khong nhan lai tu may khach - xem ghi chu dau tep.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = _hoa_don(si_name)
	_kiem_don_con_tru_duoc(si)

	khach = _khach_cua_don(si)
	if not khach:
		frappe.throw(
			"Đơn này chưa gắn khách hàng thân thiết nên không trừ điểm được. "
			"Chọn khách ở ô Khách hàng thân thiết rồi bấm lại."
		)
	_kiem_khach_tieu_duoc(khach)

	if _diem_da_tru(si["name"]) > 0:
		frappe.throw(
			"Đơn %s đã trừ điểm một lần rồi. Muốn đổi số điểm thì bấm Gỡ lượt trừ "
			"trước, rồi làm lại." % si["name"]
		)

	con_khoa = _dang_bi_khoa(khach)
	if con_khoa:
		frappe.throw(
			"Khách này vừa nhập sai mã nhiều lần nên tính năng trừ điểm đang khoá "
			"%d phút. Cần mở sớm thì xin mã OTP của quản lý ca." % con_khoa
		)

	so84 = _sdt_khach(khach)
	if not so84:
		frappe.throw(
			"Khách %s chưa có số điện thoại trong hồ sơ nên chưa gửi mã được. "
			"Vào màn Khách hàng bổ sung số rồi quay lại." % khach
		)

	c = _cd()
	so_du = _so_du(khach)
	duyet, loi = kiem_so_diem(so_diem, si["grand_total"], so_du, c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"])
	if loi:
		frappe.throw(loi)

	ma = _sinh_ma()
	doc = frappe.new_doc(DT_OTP)
	doc.update(
		{
			"sdt": so84,
			"ma_bam": _bam(ma),
			"het_han": now_datetime() + timedelta(seconds=c["otp_giay"]),
			"muc_dich": MUC_DICH,
			"khach": khach,
			"hoa_don": si["name"],
			"so_diem": duyet,
			"nguoi_xin": frappe.session.user,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	ten = frappe.db.get_value("Customer", khach, "customer_name") or khach
	tien = tien_tu_diem(duyet, c["quy_doi"])
	xong, loi_gui, gia_lap = _gui_zns(so84, ma, ten, duyet, tien)
	if not xong:
		return {"ok": 0, "ly_do": "khong_gui_duoc", "chi_tiet": loi_gui}

	return {
		"ok": 1,
		"phien": doc.name,
		"so_diem": duyet,
		"so_tien": tien,
		# Bon so cuoi thoi: du de thu ngan doc to cho khach gat dau, khong
		# du de lo so cho nguoi dung canh.
		"duoi_so": so84[-4:],
		"song_giay": c["otp_giay"],
		"gia_lap": 1 if gia_lap else 0,
	}


# --------------------------------------------------------- pha 2: xac nhan


@frappe.whitelist()
@rate_limit(limit=60, seconds=600)
def xac_nhan(si_name=None, ma=None):
	"""So ma, dung thi tru diem va cam giam gia vao don.

	KHONG nhan so diem tu may khach. So diem lay tu ban ghi OTP.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = _hoa_don(si_name)
	_kiem_don_con_tru_duoc(si)
	khach = _khach_cua_don(si)
	if not khach:
		frappe.throw("Đơn này chưa gắn khách hàng thân thiết. Chọn khách rồi làm lại.")

	ma = re.sub(r"\D", "", str(ma or ""))
	if len(ma) != 6:
		frappe.throw("Mã xác nhận gồm 6 chữ số. Vui lòng nhập lại.")

	ds = frappe.get_all(
		DT_OTP,
		filters={
			"muc_dich": MUC_DICH,
			"khach": khach,
			"hoa_don": si["name"],
			"da_dung": 0,
			"het_han": [">", now_datetime()],
		},
		fields=["name", "ma_bam", "so_lan_sai", "so_diem"],
		order_by="creation desc",
		limit_page_length=1,
	)
	if not ds:
		frappe.throw("Mã đã hết hạn. Bấm Gửi lại mã rồi đọc mã mới cho khách.")
	o = ds[0]

	if cint(o.get("so_lan_sai")) >= SAI_TOI_DA:
		frappe.throw("Mã này đã nhập sai %d lần nên không dùng được nữa. Bấm Gửi lại mã." % SAI_TOI_DA)

	if o["ma_bam"] != _bam(ma):
		con = SAI_TOI_DA - cint(o.get("so_lan_sai")) - 1
		frappe.db.set_value(DT_OTP, o["name"], "so_lan_sai", cint(o.get("so_lan_sai")) + 1)
		frappe.db.commit()
		if con <= 0:
			frappe.throw("Mã không đúng. Mã này đã hết lượt nhập, vui lòng bấm Gửi lại mã.")
		frappe.throw("Mã không đúng. Còn %d lần nhập, vui lòng kiểm tra lại rồi gõ lại." % con)

	# Ma dung. Tu day tro xuong la ghi so, nen khoa dong khach lai truoc:
	# hai thu ngan bam cung luc tren hai may thi khong duoc phep ca hai
	# cung doc mot so du roi cung tru.
	frappe.db.sql("select name from `tabCustomer` where name = %s for update", khach)

	# Kiem LAI toan bo rang buoc ngay truoc khi ghi. Giua luc xin ma va luc
	# nay co the co giao dich khac chen vao lam so du tut xuong.
	c = _cd()
	so_du = _so_du(khach)
	duyet, loi = kiem_so_diem(o.get("so_diem"), si["grand_total"], so_du, c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"])
	if loi:
		frappe.throw(loi)
	if _diem_da_tru(si["name"]) > 0:
		frappe.throw("Đơn này vừa được trừ điểm ở máy khác. Vui lòng tải lại màn hình.")

	frappe.db.set_value(DT_OTP, o["name"], "da_dung", 1, update_modified=False)
	tien = _ghi_tru_diem(khach, duyet, si["name"], c["quy_doi"])
	frappe.db.commit()

	return {
		"ok": 1,
		"so_diem": duyet,
		"so_tien": tien,
		"so_du_moi": _so_du(khach),
		"grand_total": flt(frappe.db.get_value(SI, si["name"], "grand_total")),
	}


def _ghi_tru_diem(khach, diem, si_name, quy_doi):
	"""Ghi but am vao so va cam giam gia vao hoa don. Tra so tien giam."""
	from vagabond.khach_hang import _ghi_so_diem

	tien = tien_tu_diem(diem, quy_doi)
	_ghi_so_diem(
		khach,
		-abs(int(diem)),
		LOAI_TRU,
		si_name,
		"Dùng %s điểm, giảm %s đ. Thu ngân %s." % (_so(diem), _so(tien), frappe.session.user),
	)
	dat_giam_diem(si_name, tien)
	_ghi_vet(si_name, "Trừ %s điểm của khách, giảm %s đ." % (_so(diem), _so(tien)))
	return tien


# ------------------------------------------------- cam giam gia vao hoa don


def _tran_cung(si, giam_moi):
	"""Chan cung: tong giam gia KHONG duoc vuot gia tri to. THUAN theo nghia
	chi doc mot doc da co san.

	Vi sao phai co, va vi sao khong tin vao ERPNext
	----------------------------------------------
	Diem duoc ap len SO TIEN CUOI CUNG, tuc la sau khi da tru voucher va
	combo (anh Viet chot 16/08/2026). Ham tran_dung_duoc() da lam dung viec
	do roi vi no nhan grand_total, ma grand_total la con so DA TRU moi
	khuyen mai khac.

	Nhung "da dung o duong binh thuong" khong bang "khong the sai". Ba
	duong co the dua toi mot to am: khuyen mai duoc ap THEM sau khi khach
	da tru diem; thu ngan sua bot mon lam to nho di trong khi phan diem
	giu nguyen; va nhip dong bo Pancake keo ve mot con so giam gia lon hon.
	Ca ba deu khong di qua tran_dung_duoc lan thu hai.

	Mot to am nghia la hoa don ban ra mang so tien am - no vao so cai, vao
	bao cao doanh thu, va co the vao ca hoa don dien tu. Nen chan o day,
	sat truoc luc ghi.
	"""
	# grand_total la con so DA tru discount_amount, nen cong nguoc lai thi
	# ra gia tri to truoc moi khoan giam.
	truoc_giam = flt(si.get("grand_total")) + flt(si.get("discount_amount"))
	if flt(giam_moi) > truoc_giam + 0.5:
		frappe.throw(
			"Tổng giảm giá %s đ đang vượt giá trị đơn %s đ nên đơn sẽ thành số âm. Vui lòng bớt số điểm dùng hoặc bỏ bớt khuyến mãi rồi làm lại."
			% (_so(giam_moi), _so(truoc_giam))
		)
	return truoc_giam


def dat_giam_diem(si_name, tien_diem):
	"""Dat lai phan giam gia den TU DIEM tren mot hoa don nhap.

	Vi sao KHONG ghi thang vao discount_amount
	------------------------------------------
	_upsert_hoa_don cua nhip dong bo Pancake ghi de discount_amount VO DIEU
	KIEN, va no dong vao MOI hoa don con nhap, khoang 30 phut mot lan. Ghi
	thang thi: thu ngan tru diem xong, khach ve, 30 phut sau may keo don tu
	Pancake va dat lai discount_amount bang con so Pancake bao. Giam gia tu
	diem bien mat, nhung but tru diem trong so thi van con - khach mat diem
	ma khong duoc giam dong nao, va khong co thong bao loi nao ca.

	Nen phan cua diem nam rieng o vgb_giam_diem, con discount_amount luon
	duoc dung lai bang: phan cua nguoi khac (Pancake, khuyen mai, giam tay)
	CONG phan cua diem. Nhip dong bo van ghi de phan cua no, nhung phan cua
	diem nam ngoai tam voi.
	"""
	si = frappe.get_doc(SI, si_name)
	cu = flt(si.get("vgb_giam_diem"))
	moi = flt(tien_diem)
	# Phan giam KHONG phai cua diem. Tach ra roi cong lai, de goi ham nay
	# nhieu lan khong bi cong don.
	goc = max(0.0, flt(si.discount_amount) - cu)
	# Chan cung truoc khi ghi: tong giam khong duoc vuot gia tri to.
	_tran_cung(si, goc + moi)
	si.vgb_giam_diem = moi
	si.apply_discount_on = "Grand Total"
	si.discount_amount = goc + moi
	si.flags.ignore_permissions = True
	si.flags.vgb_dat_giam_diem = True
	si.save(ignore_permissions=True)
	return flt(si.grand_total)


def giam_khong_phai_cua_diem(si, giam_moi=None):
	"""Phan giam gia nguoi khac dat, da tru phan cua diem ra. THUAN.

	quyen_quay.them_giam_gia dung ham nay: khach tieu diem cua CHINH MINH
	thi khong phai la nhan nhuong cua quan, khong nen bat goi quan ly ca
	duyet. Bat OTP quan ly cho moi luot tru diem thi quay nghen gio dong
	khach, va quan ly se quen tay duyet ma khong nhin.
	"""
	if giam_moi is None:
		return None
	return flt(giam_moi) - flt((si or {}).get("vgb_giam_diem") or 0)


# ----------------------------------------------------------------- go va hoan


@frappe.whitelist()
def go_luot_tru(si_name=None, ly_do=""):
	"""Go luot tru diem cua mot don CON NHAP, tra diem ve cho khach.

	Dung khi thu ngan bam nham so diem. Khong sua but cu (QT-20), ghi but
	hoan roi cho phep tru lai tu dau.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = _hoa_don(si_name)
	if cint(si.get("docstatus")) != 0:
		frappe.throw("Hoá đơn %s đã ghi sổ nên không gỡ được. Báo kế toán huỷ hoá đơn." % si["name"])
	n = hoan_diem_don(si["name"], (ly_do or "").strip() or "Thu ngân gỡ lượt trừ")
	if not n:
		frappe.throw("Đơn này chưa trừ điểm nên không có gì để gỡ.")
	return {"ok": 1, "da_hoan": n}


def hoan_diem_don(si_name, ly_do=""):
	"""Tra lai dung so diem da tru cho mot don. Tra so diem hoan, 0 la khong.

	Goi duoc tu ba duong don co the chet, va goi bao nhieu lan cung duoc:
	  1. on_cancel cua Sales Invoice - huy hoa don DA GHI SO
	  2. chung_tu.danh_dau_huy      - huy MEM bill quay, KHONG qua on_cancel
	  3. go_luot_tru                - thu ngan bam nham

	Duong 2 la cai bay: pos_xoa chi dat co vgb_huy chu khong goi on_cancel.
	Chi gan hoan diem vao on_cancel thi moi bill quay huy mem se nuot luon
	diem cua khach, va khong ai phat hien ra cho den luc khach di doi qua.

	Hoan DUNG SO DA TRU, doc tu so, KHONG tinh lai tu cong thuc: neu ty le
	quy doi doi giua luc tru va luc huy ma ta tinh lai thi khach nhan ve
	mot so khac so da mat.
	"""
	from vagabond.khach_hang import _ghi_so_diem

	try:
		da_tru = _diem_da_tru(si_name)
		if da_tru <= 0:
			return 0
		if _da_ghi(si_name, LOAI_HOAN):
			return 0
		khach = frappe.db.get_value(SO_DIEM, {"hoa_don": si_name, "loai": LOAI_TRU}, "khach")
		if not khach:
			return 0
		_ghi_so_diem(
			khach,
			abs(da_tru),
			LOAI_HOAN,
			si_name,
			(ly_do or "Đơn bị huỷ")[:400],
		)
		# Go luon phan giam gia tren to, neu to con nhap.
		try:
			if cint(frappe.db.get_value(SI, si_name, "docstatus")) == 0:
				dat_giam_diem(si_name, 0)
			else:
				frappe.db.set_value(SI, si_name, "vgb_giam_diem", 0, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "diem_otp: go giam gia khi hoan")
		_ghi_vet(si_name, "Hoàn lại %s điểm. %s" % (_so(da_tru), ly_do or ""))
		return int(abs(da_tru))
	except Exception:
		# Hoan diem KHONG duoc lam hong viec huy chung tu. Hong thi ghi nhat
		# ky roi thoi, chay lai bang nut duoc.
		frappe.log_error(frappe.get_traceback(), "diem_otp: hoan diem loi")
		return 0


def hoan_khi_huy_hoa_don(doc, method=None):
	"""Hook on_cancel cua Sales Invoice. Duong 1."""
	hoan_diem_don(doc.name, "Hoá đơn bị huỷ")


def hoan_khi_huy_mem(doc):
	"""Goi tu chung_tu.danh_dau_huy. Duong 2 - duong de quen nhat."""
	if getattr(doc, "doctype", None) != SI:
		return
	hoan_diem_don(doc.name, "Bill bị đánh dấu huỷ")


def _ghi_vet(si_name, viec):
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": SI,
				"reference_name": si_name,
				"content": "[Điểm] %s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


# ------------------------------------------------------------------- doc man


@frappe.whitelist()
def tinh_trang(si_name=None):
	"""Man Chi tiet don hoi: don nay tru diem duoc khong, da tru bao nhieu."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = _hoa_don(si_name)
	c = _cd()
	ra = {
		"quy_doi": c["quy_doi"],
		"tran_pt": c["tran_pt"],
		"otp_giay": c["otp_giay"],
		"gia_lap": c["gia_lap"],
		"da_tru": int(_diem_da_tru(si["name"])),
		"giam_diem": flt(si.get("vgb_giam_diem")),
		"dung_duoc": 0,
		"toi_da": 0,
		"vi_sao": "",
	}
	khach = _khach_cua_don(si)
	if not khach:
		ra["vi_sao"] = "Đơn chưa gắn khách hàng thân thiết."
		return ra
	hang = (frappe.db.get_value("Customer", khach, "vgb_hang") or "").strip()
	if hang.upper() in HANG_CAM_TIEU:
		ra["vi_sao"] = "Hạng %s nhận giảm giá thẳng nên không dùng điểm." % hang
		return ra
	if cint(si.get("docstatus")) != 0 or cint(si.get("vgb_huy")):
		ra["vi_sao"] = "Đơn đã ghi sổ hoặc đã huỷ."
		return ra
	if not _sdt_khach(khach):
		ra["vi_sao"] = "Khách chưa có số điện thoại trong hồ sơ nên chưa gửi mã được."
		return ra
	con_khoa = _dang_bi_khoa(khach)
	if con_khoa:
		ra["vi_sao"] = "Đang khoá %d phút vì nhập sai mã nhiều lần." % con_khoa
		return ra
	so_du = _so_du(khach)
	ra["so_du"] = so_du
	ra["toi_da"] = tran_dung_duoc(si["grand_total"], so_du, c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"])
	ra["dung_duoc"] = 1 if (ra["toi_da"] > 0 and not ra["da_tru"]) else 0
	if not ra["toi_da"]:
		ra["vi_sao"] = "Khách chưa đủ điểm, hoặc đơn nhỏ quá."
	elif ra["da_tru"]:
		ra["vi_sao"] = "Đơn này đã trừ %s điểm rồi." % _so(ra["da_tru"])
	return ra


@frappe.whitelist()
def xem_ma_gia_lap(si_name=None):
	"""Xem ma dang cho trong CHE GIA LAP. Chi de chay thu luong noi bo.

	Hai cua khoa: chi System Manager, va chi khi che gia lap dang bat. Khi
	mau ZNS that da duyet va che gia lap tat, ham nay tra ve rong - khong
	co duong nao doc duoc ma nua.
	"""
	if "System Manager" not in set(frappe.get_roles()):
		frappe.throw("Chỉ quản trị hệ thống xem được mã chạy thử.")
	if not _cd()["gia_lap"]:
		frappe.throw("Chế độ giả lập đã tắt, mã thật không xem được ở đây.")
	frappe.throw(
		"Mã chạy thử được ghi vào Nhật ký lỗi với tiêu đề \"Vagabond: ZNS gia lap "
		"(tru diem)\". Mở Error Log để xem, hệ không trả mã qua đường này."
	)


# ===================================================================== quay
#
# Tru diem NGAY TREN MAN TINH TIEN, luc hoa don chua ton tai.
#
# Anh Viet chon luong nay 19/08/2026: thu ngan nhap so diem ngay tren man
# tinh tien chu khong phai bam Tam tinh ra bill nhap truoc. Muot hon cho
# quay, nhung phai viet mot luong giu tien moi, nen ba doan duoi day co
# nhieu chu thich hon binh thuong.
#
# Ba pha, KHAC voi luong tren hoa don o cho pha hai KHONG tru diem:
#
#   1. xin_ma_quay    may chu tinh lai tong gio hang, duyet so diem, gui ZNS
#   2. xac_nhan_quay  so ma. Dung thi danh dau ve DA XAC THUC. VAN CHUA tru.
#   3. dung_ve        goi tu tao_don_tay NGAY SAU khi hoa don da luu. Kiem
#                     lai tran tren grand_total THAT roi moi tru diem.
#
# Vi sao tach pha 3 ra: giua luc khach doc ma va luc thu ngan bam Thu tien,
# gio hang co the doi (bot mon, them khuyen mai). Neu tru diem ngay o pha 2
# thi khach mat diem cho mot to bill co the khong bao gio duoc lap, hoac
# duoc lap voi so tien khac han. Tru o pha 3 thi con so tru luon dua tren
# to bill THAT da nam trong co so du lieu - dung tinh than QT-19.
#
# Ve chi dung duoc MOT LAN va co han: xem HAN_DUNG_PHUT.

HAN_DUNG_PHUT = 30  # ve xac thuc roi thi con dung duoc bao lau


def _tong_tam_tinh(items, giam_gia=0, phi_ship=0, km_giam=0):
	"""Tinh lai tong gio hang o MAY CHU. Tra ve so tien truoc khi tru diem.

	QT-19: khong nhan tong tien tu may khach. May khach chi gui len gio
	hang, con phep cong thi may chu lam.

	Luu y ve don gia: giong tao_don_tay, don gia van lay tu may khach, vi
	thu ngan duoc phep dat gia tay tai quay. Do KHONG phai lo hong o day:
	con so cuoi cung ma diem duoc tru vao la grand_total THAT cua to hoa
	don, kiem lai o dung_ve(). Tong tinh o day chi de duyet so diem va de
	tin ZNS gui cho khach ghi dung so tien.
	"""
	tong = 0.0
	for r in items or []:
		ma = (r.get("item_code") or "").strip()
		if not ma:
			continue
		sl = flt(r.get("qty") or 0)
		if sl <= 0:
			continue
		tong += sl * flt(r.get("rate") or 0)
	tong += flt(phi_ship)
	tong -= flt(giam_gia) + flt(km_giam)
	return max(0.0, tong)


def _km_giam_quay(items, ctkm_ap, ma_voucher, combo_ap, quay, nguon, khach, sdt, ngay):
	"""So tien khuyen mai giam, tinh lai o may chu. Loi thi tra 0.

	Dung DUNG duong ma tao_don_tay dung, de con so hien tren man tinh tien
	khong lech voi con so cuoi cung tren hoa don.
	"""
	if not (ctkm_ap or combo_ap or (ma_voucher or "").strip()):
		return 0.0
	try:
		from vagabond import khuyen_mai as _km

		kq = _km.tinh(
			items, ctkm=ctkm_ap, ma=ma_voucher, combo=combo_ap, quay=quay,
			nguon=nguon, khach=khach or None, sdt=sdt, ngay=ngay,
		)
		return flt(kq.get("tong_giam"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_otp: tinh khuyen mai o quay")
		return 0.0


def _ve_con_dung_duoc(ve, khach=None):
	"""Doc mot ve va kiem no con dung duoc khong. Nem loi neu khong.

	Tra ve ban ghi OTP.
	"""
	if not ve:
		frappe.throw("Chưa có vé trừ điểm. Vui lòng bấm Trừ điểm rồi xác nhận mã trước.")
	o = frappe.db.get_value(
		DT_OTP, ve,
		["name", "khach", "so_diem", "da_dung", "da_xac_thuc", "han_dung", "muc_dich", "hoa_don"],
		as_dict=True,
	)
	if not o or o.get("muc_dich") != MUC_DICH:
		frappe.throw("Không tìm thấy vé trừ điểm này. Vui lòng bấm Trừ điểm lại từ đầu.")
	if cint(o.get("da_dung")):
		frappe.throw(
			"Vé trừ điểm này đã dùng cho hoá đơn %s rồi. Muốn trừ tiếp thì xin mã mới."
			% (o.get("hoa_don") or "khác")
		)
	if not cint(o.get("da_xac_thuc")):
		frappe.throw("Khách chưa xác nhận mã cho lượt trừ điểm này. Vui lòng nhập mã rồi bấm lại.")
	if o.get("han_dung") and now_datetime() > o["han_dung"]:
		frappe.throw(
			"Vé trừ điểm đã quá %d phút nên hết hiệu lực. Bấm Trừ điểm lại để xin mã mới."
			% HAN_DUNG_PHUT
		)
	if khach and (o.get("khach") or "") != khach:
		frappe.throw(
			"Vé trừ điểm này của khách %s, không dùng cho khách %s được. Vui lòng bấm Trừ điểm lại cho đúng khách." % (o.get("khach"), khach)
		)
	return o


@frappe.whitelist()
@rate_limit(limit=30, seconds=600)
def xin_ma_quay(khach=None, so_diem=None, items=None, giam_gia=0, phi_ship=0,
                ctkm_ap=None, ma_voucher="", combo_ap=None, quay="", nguon="",
                sdt="", ngay=None):
	"""Pha 1 cua luong quay: duyet so diem va gui ZNS. CHUA tru diem."""
	import json as _json

	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach:
		frappe.throw(
			"Chưa chọn khách hàng thân thiết nên chưa trừ điểm được. Vui lòng chọn khách ở ô Khách rồi bấm lại."
		)
	if not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách %s trong hệ thống. Vui lòng chọn lại." % khach)
	_kiem_khach_tieu_duoc(khach)

	con_khoa = _dang_bi_khoa(khach)
	if con_khoa:
		frappe.throw(
			"Khách này vừa nhập sai mã nhiều lần nên tính năng trừ điểm đang khoá "
			"%d phút. Cần mở sớm thì xin mã OTP của quản lý ca." % con_khoa
		)

	so84 = _sdt_khach(khach)
	if not so84:
		frappe.throw(
			"Khách %s chưa có số điện thoại trong hồ sơ nên chưa gửi mã được. "
			"Vào màn Khách hàng bổ sung số rồi quay lại." % khach
		)

	if isinstance(items, str):
		items = _json.loads(items or "[]")
	if isinstance(ctkm_ap, str):
		ctkm_ap = _json.loads(ctkm_ap or "null")
	if isinstance(combo_ap, str):
		combo_ap = _json.loads(combo_ap or "null")

	km_giam = _km_giam_quay(items, ctkm_ap, ma_voucher, combo_ap, quay, nguon, khach, sdt, ngay)
	tong = _tong_tam_tinh(items, giam_gia, phi_ship, km_giam)
	if tong <= 0:
		frappe.throw(
			"Giỏ hàng đang trống hoặc bằng 0 đ nên chưa trừ điểm được. Vui lòng chọn món cho khách rồi bấm lại."
		)

	c = _cd()
	so_du = _so_du(khach)
	duyet, loi = kiem_so_diem(so_diem, tong, so_du, c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"])
	if loi:
		frappe.throw(loi)

	ma = _sinh_ma()
	doc = frappe.new_doc(DT_OTP)
	doc.update({
		"sdt": so84,
		"ma_bam": _bam(ma),
		"het_han": now_datetime() + timedelta(seconds=c["otp_giay"]),
		"muc_dich": MUC_DICH,
		"khach": khach,
		# Chua co hoa don nao ca - day chinh la diem khac cua luong quay.
		"hoa_don": None,
		"so_diem": duyet,
		"tong_bill": tong,
		"nguoi_xin": frappe.session.user,
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	ten = frappe.db.get_value("Customer", khach, "customer_name") or khach
	tien = tien_tu_diem(duyet, c["quy_doi"])
	xong, loi_gui, gia_lap = _gui_zns(so84, ma, ten, duyet, tien)
	if not xong:
		return {"ok": 0, "ly_do": "khong_gui_duoc", "chi_tiet": loi_gui}

	return {
		"ok": 1,
		"phien": doc.name,
		"so_diem": duyet,
		"so_tien": tien,
		"tong_tam_tinh": tong,
		"duoi_so": so84[-4:],
		"song_giay": c["otp_giay"],
		"gia_lap": 1 if gia_lap else 0,
	}


@frappe.whitelist()
@rate_limit(limit=60, seconds=600)
def xac_nhan_quay(phien=None, ma=None):
	"""Pha 2 cua luong quay: so ma. Dung thi cap VE, VAN CHUA tru diem."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ma = re.sub(r"\D", "", str(ma or ""))
	if len(ma) != 6:
		frappe.throw("Mã xác nhận gồm 6 chữ số. Vui lòng nhập lại.")

	o = frappe.db.get_value(
		DT_OTP, phien,
		["name", "khach", "ma_bam", "so_lan_sai", "so_diem", "het_han",
		 "da_dung", "da_xac_thuc", "muc_dich"],
		as_dict=True,
	)
	if not o or o.get("muc_dich") != MUC_DICH:
		frappe.throw("Không tìm thấy lượt xin mã này. Vui lòng bấm Trừ điểm lại từ đầu.")
	if cint(o.get("da_dung")):
		frappe.throw("Lượt này đã dùng rồi. Bấm Trừ điểm lại nếu cần trừ thêm.")
	if cint(o.get("da_xac_thuc")):
		# Bam hai lan thi khong phai loi cua ai, tra lai ve cu.
		return {"ok": 1, "ve": o["name"], "so_diem": int(flt(o.get("so_diem"))),
		        "so_tien": tien_tu_diem(o.get("so_diem"), _cd()["quy_doi"]),
		        "han_dung_phut": HAN_DUNG_PHUT}
	if o.get("het_han") and now_datetime() > o["het_han"]:
		frappe.throw("Mã đã hết hạn. Bấm Gửi lại mã rồi đọc mã mới cho khách.")
	if cint(o.get("so_lan_sai")) >= SAI_TOI_DA:
		frappe.throw("Mã này đã nhập sai %d lần nên không dùng được nữa. Bấm Gửi lại mã." % SAI_TOI_DA)

	if o["ma_bam"] != _bam(ma):
		con = SAI_TOI_DA - cint(o.get("so_lan_sai")) - 1
		frappe.db.set_value(DT_OTP, o["name"], "so_lan_sai", cint(o.get("so_lan_sai")) + 1)
		frappe.db.commit()
		if con <= 0:
			frappe.throw("Mã không đúng. Mã này đã hết lượt nhập, vui lòng bấm Gửi lại mã.")
		frappe.throw("Mã không đúng. Còn %d lần nhập, vui lòng kiểm tra lại rồi gõ lại." % con)

	frappe.db.set_value(
		DT_OTP, o["name"],
		{"da_xac_thuc": 1, "han_dung": now_datetime() + timedelta(minutes=HAN_DUNG_PHUT)},
		update_modified=False,
	)
	frappe.db.commit()
	c = _cd()
	return {
		"ok": 1,
		"ve": o["name"],
		"so_diem": int(flt(o.get("so_diem"))),
		"so_tien": tien_tu_diem(o.get("so_diem"), c["quy_doi"]),
		"han_dung_phut": HAN_DUNG_PHUT,
	}


def dung_ve(ve, si_name):
	"""Pha 3: tru diem that vao to hoa don VUA LUU. Nem loi neu khong hop le.

	KHONG whitelist: chi tao_don_tay duoc goi. Mo ra cho may khach goi thi
	ai cung tru duoc diem vao bat ky hoa don nao.
	"""
	si = _hoa_don(si_name)
	_kiem_don_con_tru_duoc(si)
	khach = _khach_cua_don(si)
	if not khach:
		frappe.throw(
			"Hoá đơn %s chưa gắn khách hàng thân thiết nên không trừ điểm được. Vui lòng chọn khách rồi lập lại bill." % si_name
		)

	# Khoa dong khach truoc khi ghi: hai may cung tru mot luc thi khong duoc
	# phep ca hai cung doc mot so du.
	frappe.db.sql("select name from `tabCustomer` where name = %s for update", khach)

	o = _ve_con_dung_duoc(ve, khach)
	if _diem_da_tru(si_name) > 0:
		frappe.throw("Hoá đơn %s đã được trừ điểm rồi. Vui lòng tải lại màn hình." % si_name)

	# Kiem LAI tran tren grand_total THAT. Giua luc khach doc ma va luc bam
	# Thu tien, gio hang co the da doi.
	c = _cd()
	so_du = _so_du(khach)
	duyet, loi = kiem_so_diem(
		o.get("so_diem"), si["grand_total"], so_du, c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"]
	)
	if loi:
		# QT-24: noi ro phai lam gi tiep, va noi ro diem CHUA bi tru.
		frappe.throw(
			"%s Bill đã lưu là %s nhưng hệ thống CHƯA trừ điểm của khách. Vui lòng mở bill đó ra trừ điểm lại." % (loi, si_name)
		)

	frappe.db.set_value(
		DT_OTP, o["name"], {"da_dung": 1, "hoa_don": si_name}, update_modified=False
	)
	tien = _ghi_tru_diem(khach, duyet, si_name, c["quy_doi"])
	return {"so_diem": duyet, "so_tien": tien}


@frappe.whitelist()
def bo_ve(phien=None):
	"""Thu ngan doi y truoc khi chot bill: huy ve, khong tru diem.

	Khong xoa ban ghi (QT-20), chi danh dau da dung de khong ai xai lai.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	o = frappe.db.get_value(DT_OTP, phien, ["name", "da_dung", "muc_dich"], as_dict=True)
	if not o or o.get("muc_dich") != MUC_DICH:
		return {"ok": 1}
	if cint(o.get("da_dung")):
		frappe.throw("Vé này đã dùng cho một hoá đơn rồi nên không bỏ được.")
	frappe.db.set_value(
		DT_OTP, o["name"],
		{"da_dung": 1, "ghi_chu_bo": "Thu ngân bỏ vé lúc %s" % now_datetime()},
		update_modified=False,
	)
	return {"ok": 1}


@frappe.whitelist()
def tinh_trang_quay(khach=None, tong=0):
	"""Man tinh tien hoi: khach nay dung duoc bao nhieu diem. CHI DOC."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	khach = (khach or "").strip()
	c = _cd()
	ra = {
		"quy_doi": c["quy_doi"], "tran_pt": c["tran_pt"],
		"otp_giay": c["otp_giay"], "gia_lap": c["gia_lap"],
		"dung_duoc": 0, "toi_da": 0, "so_du": 0, "vi_sao": "",
	}
	if not khach:
		ra["vi_sao"] = "Chưa chọn khách hàng thân thiết."
		return ra
	hang = (frappe.db.get_value("Customer", khach, "vgb_hang") or "").strip()
	if hang.upper() in HANG_CAM_TIEU:
		ra["vi_sao"] = (
			"Hạng %s đã nhận ưu đãi giảm giá thẳng trên bill nên không dùng điểm được." % hang
		)
		return ra
	so_du = _so_du(khach)
	ra["so_du"] = int(so_du)
	con_khoa = _dang_bi_khoa(khach)
	if con_khoa:
		ra["vi_sao"] = "Khách vừa nhập sai mã nhiều lần, tính năng trừ điểm đang khoá %d phút." % con_khoa
		return ra
	toi_da = tran_dung_duoc(tong, so_du, c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"])
	ra["toi_da"] = int(toi_da)
	# Tra ve CA HAI tran de man hinh noi dung ly do, dung cai nao dang chan.
	#
	# Ban dau man hinh in "toi da N diem (bang 50% gia tri bill)". Nghiem thu
	# 19/08/2026 ra ngay cho sai: khach Mr. Tri con 90.940 diem, bill 200.000,
	# tran theo bill la 100.000 diem nhung so du chi 90.940 nen tran that la
	# 90.940. Con so in ra dung, nhung cau giai thich thi sai - thu ngan doc
	# xong se tuong 50% cua 200.000 la 90.940.
	tran_bill = 0.0
	if flt(c["quy_doi"]) > 0:
		tran_tien = flt(tong) * flt(c["tran_pt"]) / 100.0
		con_lai = flt(tong) - flt(c["bill_toi_thieu"])
		if con_lai < tran_tien:
			tran_tien = con_lai
		tran_bill = max(0.0, tran_tien / flt(c["quy_doi"]))
	ra["tran_theo_bill"] = int(tran_bill)
	ra["do_so_du"] = 1 if int(so_du) < int(tran_bill) else 0
	if toi_da <= 0:
		ra["vi_sao"] = (
			"Khách chưa đủ điểm, hoặc bill còn nhỏ quá. Bill phải trên %s đ mới trừ điểm được."
			% _so(flt(c["bill_toi_thieu"]) * 2)
		)
		return ra
	ra["dung_duoc"] = 1
	return ra

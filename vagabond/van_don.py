"""Van don giao banh: sales phan don, shipper giao va bao ket qua, book xe app ngoai.

Chot voi anh Viet 02/08/2026:
- Shipper bam "Da giao" kem ANH chup tai cho (client nen anh truoc khi
  upload, luu private). Cron xoa anh giao sau 30 ngay cho nhe he thong;
  anh hoa don chi phi (chung tu) thi giu nguyen.
- Giao xong tu day trang thai "da nhan" (status 3) sang Pancake.
- Book xe: Ahamove chay that (dung san client giao_hang). GreenSM va BE
  dung khung cho key: GreenSM xac thuc OAuth2 client credentials, scope
  express.trips, base https://api-partner.vn.gsm-api.net/v1/express/
  (sandbox rieng), nho whitelist IP server. Dien key vao Vagabond Settings
  la chay, khong phai sua code.
- Chi phi shipper (xang, bao tri...): shipper khai kem anh hoa don,
  Thu mua / Ke toan duyet roi danh dau hoan ung.
"""

import json
import re

import frappe
from frappe.utils import add_days, cint, flt, get_datetime, now_datetime, nowdate

from vagabond import nhat_ky_dong_bo as nhat_ky
from vagabond.kiem_banh import BO_QUA_TT, _keo_don, _khoang_unix
from vagabond import pickup
from vagabond.lib import PANCAKE, TIMEOUT, cache_get, cache_set, cfg, key
from vagabond.vai_cua_hang import VAI_QLCH

QUYEN_SALES = {"System Manager", "Sales User", "Sales Manager", "Bộ phận đặt hàng"}
QUYEN_KE_TOAN = {"System Manager", "Accounts User", "Purchase User"}


def _roles():
	return set(frappe.get_roles())


def _la_sales():
	return bool(QUYEN_SALES & _roles())


def _la_shipper():
	return "Shipper" in _roles()


def _la_ke_toan():
	return bool(QUYEN_KE_TOAN & _roles())


def _la_quan_ly_diem():
	"""Quan ly cua hang. Ho truc quay, nen phai thay duoc don khach tu lay.

	Truoc 05/09/2026 vai nay khong nam trong cong nao cua phan he van don,
	nen mot quan ly khong kiem vai Sales User thi mo man ra bi chan, du don
	pickup dang nam ngay tren quay cua ho.
	"""
	return VAI_QLCH in _roles()


def _kiem_quyen_xem():
	if not (_la_sales() or _la_shipper() or _la_ke_toan() or _la_quan_ly_diem()):
		frappe.throw("Tài khoản chưa được cấp quyền dùng phân hệ vận đơn.")


# ---------------------------------------------------------------- Pancake

def _don_pancake(pid):
	"""Doc mot don Pancake de lay dia chi giao, ten, sdt, COD."""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id and pid):
		return {}
	try:
		r = _mang().get(
			"%s/shops/%s/orders/%s" % (PANCAKE, c.pancake_shop_id, pid),
			params={"api_key": k},
			timeout=TIMEOUT,
		)
		return (r.json() or {}).get("data") or {}
	except Exception:
		return {}


def _day_trang_thai_pancake(pid, status=3):
	"""Day trang thai don sang Pancake (3 = da nhan). Tra True/False."""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id and pid):
		return False
	try:
		r = _mang().put(
			"%s/shops/%s/orders/%s" % (PANCAKE, c.pancake_shop_id, pid),
			params={"api_key": k},
			json={"status": status},
			timeout=TIMEOUT,
		)
		return r.status_code == 200
	except Exception:
		frappe.log_error(title="Vagabond: day trang thai Pancake loi", message=frappe.get_traceback())
		return False


# ---------------------------------------------------------------- Van don

@frappe.whitelist()
def tao_van_don(si_name=None, ma_don=None, khach=None, sdt=None, dia_chi=None,
	ngay_giao=None, gio_giao=None, kenh=None, tien_thu_ho=0, ghi_chu=None,
	nguoi_nhan=None, sdt_nhan=None, tag_gio=None, lat=None, lng=None):
	"""Tao van don, uu tien keo thong tin tu hoa don + don Pancake goc.

	tag_gio la khung gio sales chon tren app, dang "9h - 11h". Ghi luon vao
	tag_gio va buoi de don tay vao duoc xep tuyen ngay, khong phai cho the
	ben Pancake. lat/lng la toa do Goong tra ve luc sales chon dia chi goi y,
	co san thi xep tuyen khoi ton mot luot geocode.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales tạo được vận đơn.")
	pid = ""
	if si_name:
		si = frappe.db.get_value(
			"Sales Invoice", si_name,
			["custom_pancake_id", "custom_pancake_display_id", "remarks", "grand_total", "outstanding_amount"],
			as_dict=True,
		)
		if not si:
			frappe.throw("Không thấy hoá đơn %s" % si_name)
		pid = si.custom_pancake_id or ""
		ma_don = ma_don or si.custom_pancake_display_id
		kh = (si.remarks or "").split(" - ")
		khach = khach or (kh[1] if len(kh) > 1 else "")
		sdt = sdt or (kh[2] if len(kh) > 2 else "")
		if not tien_thu_ho:
			tien_thu_ho = si.outstanding_amount if si.outstanding_amount else si.grand_total
		if pid and not dia_chi:
			o = _don_pancake(pid)
			sa = o.get("shipping_address") or {}
			dia_chi = sa.get("full_address") or sa.get("address") or ""
			khach = khach or (o.get("bill_full_name") or "")
			sdt = sdt or (o.get("bill_phone_number") or "")
			nguoi_nhan = (sa.get("full_name") or "").strip()
			sdt_nhan = (sa.get("phone_number") or "").strip()
	from vagabond.xep_tuyen import buoi_tu_khung

	tag_gio = (tag_gio or "").strip()
	if not tag_gio and RE_TAG_GIO.match(str(gio_giao or "")):
		tag_gio = str(gio_giao).strip()
	doc = frappe.get_doc(
		{
			"doctype": "Van Don",
			"hoa_don": si_name or None,
			"ma_don": ma_don,
			"khach": khach,
			"sdt": sdt,
			"nguoi_nhan": nguoi_nhan,
			"sdt_nhan": sdt_nhan,
			"dia_chi": dia_chi,
			"ngay_giao": ngay_giao or nowdate(),
			"gio_giao": gio_giao,
			"tag_gio": tag_gio or None,
			"buoi": buoi_tu_khung(tag_gio) if tag_gio else None,
			"lat": flt(lat) or None,
			"lng": flt(lng) or None,
			"kenh": kenh or "Shipper nội bộ",
			"tien_thu_ho": flt(tien_thu_ho),
			"ghi_chu": ghi_chu,
			"pancake_id": pid,
		}
	)
	doc.insert(ignore_permissions=True)
	mon = _mon_tu_pancake(_don_pancake(pid)) if pid else []
	if not mon:
		mon = _mon_tu_hoa_don(si_name)
	if mon:
		_ghi_mon(doc.name, mon)
	return doc.name


def _gio_tu_iso(s):
	"""Lay HH:mm tu chuoi ISO datetime cua Pancake, khong co thi tra rong."""
	s = str(s or "")
	if "T" in s and len(s) >= 16:
		return s[11:16]
	if " " in s and len(s) >= 16:
		return s[11:16]
	return ""


def _mang():
	"""Thư viện gọi mạng, nạp KHI CẦN chứ không nạp ở đầu tệp.

	Máy chạy CI của GitHub tay không, không có `requests`. Bộ kiểm thử tầng
	khung có import mô đun này để đối chiếu phép đọc ngày với `mua_vu`, nên
	đầu tệp mà kéo `requests` là CI đỏ. Đã đỏ ba ca hôm 20/08 vì đúng lý do
	này ở một tệp khác.
	"""
	import requests

	return requests


def _lech_mui(duoi):
	"""Giữ tên cũ, gọi hàm chung. Xem vagabond/ngay_pancake.py."""
	from vagabond.ngay_pancake import _lech_mui as _f

	return _f(duoi)


def _ngay_tu_iso(s):
	"""Ngày giao THEO GIỜ VIỆT NAM. Nay do vagabond/ngay_pancake.py lo.

	VÌ SAO DỜI ĐI CHỖ KHÁC (23/08/2026)
	Hàm này từng nằm ngay đây và đã sửa đúng hôm 19/08, sau khi 75 vận đơn bị
	đẩy lùi một ngày. Nhưng `mua_vu.py` có một hàm đọc ngày RIÊNG và vẫn cắt
	thẳng t[:10], nên ngày 23/08 lỗi y hệt lặp lại ở màn Có thể bán: đơn giao
	24/08 hiện ở tab 23/08.

	Sửa tại chỗ lần nữa thì lần thứ ba sẽ lại xảy ra ở tệp thứ ba. Nên phép
	đọc ngày Pancake nay chỉ còn MỘT bản, và có ca kiểm quét chặn tệp khác tự
	viết lại. Tên hàm ở đây giữ nguyên để mọi chỗ gọi cũ không phải sửa.
	"""
	from vagabond.ngay_pancake import ngay_tu_iso

	return ngay_tu_iso(s)


def _ngay_hop_le(ngay):
	"""Giữ tên cũ, gọi hàm chung. Xem vagabond/ngay_pancake.py."""
	from vagabond.ngay_pancake import ngay_hop_le

	return ngay_hop_le(ngay)


# Luat doi ngay giao theo Pancake. Anh Viet duyet 19/08/2026.
#
# Cau chuyen: don 91928 khach doi ngay giao tu 17/08 sang 18/08 tren Pancake.
# Nhip dong bo CO chay qua don do, CO ghi de gio giao thanh 08:00 cua ban
# moi, nhung khong he dung toi ngay giao - vi dict cac o duoc cap nhat khong
# he co khoa ngay_giao. Van don ket lai o 17/08, loc danh sach ngay 18/08
# khong thay don, bep va shipper deu khong biet.
#
# Nguyen tac: cai gi khach quyet thi Pancake duoc de, cai gi ben minh van
# hanh quyet thi Pancake khong duoc de nhung PHAI BAO. Im lang chinh la thu
# lam mat don 91928.
DOI_NGAY_DUOC = "de"  # de thang, chi ghi nhat ky
DOI_NGAY_CANH_BAO = "de_va_bao"  # van de, nhung go khoi chuyen va bao nguoi
DOI_NGAY_CHAN = "chan"  # khong de, chi bao


def luat_doi_ngay(trang_thai, co_chuyen, qua_han=0):
	"""Pancake doi ngay giao thi lam gi. THUAN, khong doc co so du lieu.

	trang_thai  trang thai hien tai cua van don ben minh
	co_chuyen   van don da duoc gan chuyen hoac shipper chua
	qua_han     ngay giao dang luu da troi qua chua (1 la roi)

	Van don da xong viec (Da giao, Khong giao duoc, Huy) thi khong tra ve
	nhanh nao ca: viec da xong roi, doi ngay khong con nghia gi.

	VI SAO CO THAM SO qua_han
	Don 91842 day ra bai hoc nay. Ben sales tra loi: "hien tren app se
	khong co thao tac doi trang thai gi het, ben em chi thao tac chuyen doi
	lai ngay nhan, don hang 14.8 thi trong ngay 14.8 moi cap nhat lai sang
	ngay 18/8". Nghia la don do doi ngay tu 14/08, ma van don ben minh van
	nam o "Dang giao" tu hom do toi gio.

	"Dang giao" ma ngay giao da troi qua thi khong con nghia la shipper
	dang cam banh tren duong nua, no chi la trang thai bo quen. Chan cap
	nhat vi mot trang thai bo quen thi don ket lai vinh vien o ngay sai.
	Nen truong hop do van de, nhung PHAI bao cho nguoi biet.
	"""
	tt = (trang_thai or "").strip()
	if tt == "Chờ giao":
		return DOI_NGAY_CANH_BAO if co_chuyen else DOI_NGAY_DUOC
	if tt == "Đang giao":
		if cint(qua_han):
			return DOI_NGAY_CANH_BAO
		# Ngay giao la hom nay hoac mai: shipper co the dang cam banh tren
		# duong that. Doi ngay luc nay la chuyen NGUOI phai xu, may khong
		# duoc tu quyet.
		return DOI_NGAY_CHAN
	return ""


# The khung gio cua tiem co dang "15h - 17h"; the con lai la the van hanh
# (Goi truoc khi giao, Chup anh gui truoc khi giao, Cho banh, Xuat hoa don...).
RE_TAG_GIO = re.compile(r"^\s*\d{1,2}\s*h")
THE_GOI_TRUOC = "Gọi trước khi giao"
THE_CHUP_TRUOC = "Chụp ảnh gửi trước khi giao"


def _tach_the(o):
	"""Tra (khung_gio, danh_sach_the_van_hanh).

	Luu y: luc GHI sang Pancake thi tags la mang so; luc DOC ve thi Pancake
	tra mang object {id, name}. Ham nay chiu ca hai kieu.
	"""
	gio, khac = "", []
	for t in (o.get("tags") or []):
		ten = (t.get("name") if isinstance(t, dict) else str(t)) or ""
		ten = ten.strip()
		if not ten:
			continue
		if RE_TAG_GIO.match(ten):
			if not gio:
				gio = ten
		elif ten not in khac:
			khac.append(ten)
	return gio, khac


def _phuong(sa):
	"""Ten phuong / xa theo dia gioi MOI. Pancake da cap nhat sau khi bo cap
	quan huyen nen commune_name la ten moi (vd 'Phuong An Khanh'), dung duoc
	ngay - khong phai tu dung bang doi ten cu sang moi.
	"""
	return (sa.get("commune_name") or sa.get("commnue_name") or "").strip()


def _tu_pancake(o):
	"""Gom cac truong lay tu don Pancake ve dang truong cua Van Don.

	Nguoi DAT va nguoi NHAN hay la hai nguoi khac nhau (banh sinh nhat, banh
	tang). Pancake tach san: bill_full_name / bill_phone_number la nguoi dat
	(nguoi tra tien, nguoi sales noi chuyen), con shipping_address.full_name /
	phone_number la nguoi nhan tai dia chi giao. Goi nguoi nhan khong duoc thi
	shipper goi nguoi dat de thuong luong, nen phai giu ca hai.
	"""
	from vagabond.xep_tuyen import buoi_tu_khung

	sa = o.get("shipping_address") or {}
	gio, the = _tach_the(o)
	return {
		"khach": (o.get("bill_full_name") or sa.get("full_name") or "").strip(),
		"sdt": (o.get("bill_phone_number") or sa.get("phone_number") or "").strip(),
		"nguoi_nhan": (sa.get("full_name") or "").strip(),
		"sdt_nhan": (sa.get("phone_number") or "").strip(),
		"tag_gio": gio,
		"buoi": buoi_tu_khung(gio),
		"phuong": _phuong(sa),
		"the_don": ", ".join(the),
		"goi_truoc": 1 if THE_GOI_TRUOC in the else 0,
		"chup_truoc": 1 if THE_CHUP_TRUOC in the else 0,
		"ghi_chu_in": (o.get("note_print") or "").strip(),
	}


# Pancake ghi phi giao hang thanh mot "mon" trong don (vd PHI-GIAO-HANG,
# 60 x 1.000d). Do khong phai hang de shipper cam di, hien ra chi tro roi mat.
MA_KHONG_PHAI_HANG = ("PHI-", "PHU-THU", "PHUTHU")


def _la_hang_that(ma, ten):
	ma = (ma or "").upper()
	for tien_to in MA_KHONG_PHAI_HANG:
		if ma.startswith(tien_to):
			return False
	return bool(ma or ten)


def _mon_tu_pancake(o):
	"""Danh sach mon trong don Pancake, dua ve dang dong cua bang Van Don Mon.

	Ma hang nam o variation_info.display_id (dung ma tiem dat, khop voi Item
	ben ERPNext), ten mon o variation_info.name. note_product la loi nhan cho
	tung banh - shipper can doc nen phai giu.
	"""
	ra = []
	for it in (o.get("items") or []):
		vi = it.get("variation_info") or {}
		ten = (vi.get("name") or "").strip()
		ma = (vi.get("display_id") or "").strip()
		if not _la_hang_that(ma, ten):
			continue
		ra.append({
			"ma_hang": ma,
			"ten": ten,
			"so_luong": flt(it.get("quantity") or 0),
			"gia": flt(vi.get("retail_price") or 0),
			"tang": 1 if it.get("is_bonus_product") else 0,
			"ghi_chu": (it.get("note_product") or "").strip(),
		})
	return ra


def _mon_tu_hoa_don(si_name):
	"""Danh sach mon lay tu hoa don ban hang, dung khi don khong co ben Pancake."""
	if not si_name:
		return []
	return [
		{
			"ma_hang": r.item_code,
			"ten": r.item_name,
			"so_luong": flt(r.qty),
			"gia": flt(r.rate),
			"tang": 0,
			"ghi_chu": "",
		}
		for r in frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": si_name},
			fields=["item_code", "item_name", "qty", "rate"],
			order_by="idx asc",
			limit_page_length=100,
		)
	]


def _mon_khac(doc_name, dong):
	"""Bang mon hien tai co khac voi ben Pancake khong.

	So ma hang - so luong - ghi chu tung dong. Khach them banh, bot banh hay
	sua loi chuc tren Pancake thi phai thay o day (Loan Anh 10/08/2026).
	"""
	cu = frappe.get_all(
		"Van Don Mon",
		filters={"parent": doc_name},
		fields=["ma_hang", "ten", "so_luong", "ghi_chu"],
		order_by="idx asc",
		limit_page_length=200,
	)
	def gon(ds):
		return sorted([
			(
				str(d.get("ma_hang") or "").strip().upper(),
				str(d.get("ten") or "").strip(),
				flt(d.get("so_luong")),
				str(d.get("ghi_chu") or "").strip(),
			)
			for d in ds
		])
	return gon(cu) != gon(dong or [])


def _ghi_mon(doc_name, dong):
	"""Ghi de bang mon cua mot van don. Khong co dong nao thi de nguyen bang cu."""
	if not dong:
		return 0
	doc = frappe.get_doc("Van Don", doc_name)
	doc.set("mon", [])
	for d in dong:
		doc.append("mon", d)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return len(dong)


def _pt_thu_tien_mat(ten_pt):
	"""Phuong thuc nay shipper co phai thu tien mat luc giao khong.

	Tra ve True (co thu), False (khong thu), None (chua chon nen chua biet).

	Viet theo chieu CHO PHEP: chi Mode of Payment kieu Cash moi sinh COD.
	Bam vao truong type cua ERPNext chu khong viet cung ten tieng Viet - hom
	nao chi Dung them mot phuong thuc moi la khoi phai sua ma. Bai hoc tu
	guard _khong_duoc_huy: viet theo chieu cam thi som muon cung lot.
	"""
	t = (ten_pt or "").strip()
	if not t:
		return None
	kieu = frappe.db.get_value("Mode of Payment", t, "type")
	if not kieu:
		return None
	return kieu == "Cash"


def _cod_tu_don(o, si):
	"""Tien shipper phai thu. Uu tien so con lai tren hoa don ERPNext.

	Khach da chuyen khoan thi shipper KHONG thu gi ca, du hoa don con dang
	nhap va so con no van bang tong. So con no chi ve 0 khi hoa don ghi so
	VA co but toan thu tien, ma hai viec do xay ra sau luc giao - lay no lam
	COD la doi shipper thu tien lan hai.

	Bat duoc 13/08/2026: don chi Hau 700.000 va don Oshima 1.480.000 deu
	hien trong doi soat COD du khach da chuyen khoan (Sales bao lai).
	"""
	if si:
		if _pt_thu_tien_mat(si.get("vgb_pt_thanh_toan")) is False:
			return 0.0
		return flt(si.outstanding_amount or 0)
	tong = flt(
		o.get("total_price_after_sub_discount")
		or o.get("total_price")
		or 0
	)
	da_tra = flt(o.get("prepaid") or 0)
	for truong in ("cash", "transfer_money", "charged_by_onepay", "charged_by_card",
		"charged_by_momo", "charged_by_vnpay", "charged_by_qrpay"):
		da_tra += flt(o.get(truong) or 0)
	return max(0, tong - da_tra)


@frappe.whitelist()
def dong_bo_pancake(ngay=None):
	"""Keo don Pancake giao trong NGAY ve thanh van don de sales phan shipper.

	Loc theo ngay giao du kien (updateStatus=estimate_delivery_date, moc thoi
	gian phai la UNIX GIAY - truyen ISO thi Pancake tra 0 don ma khong bao
	loi). Bo don da huy (6) va da xoa (7). Chong trung theo pancake_id: don
	da keo ve roi thi khong dung toi, tranh de len tay sales da sua.
	"""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ sales và kế toán đồng bộ được vận đơn.")
	return _dong_bo_pancake(ngay)


def _theo_ngay_giao(o, cu, pid):
	"""Ap luat doi ngay giao cho MOT van don da co. Khong nem loi ra ngoai.

	Tach rieng khoi vong so sanh chung vi ba le. Mot, quyet dinh phu thuoc
	trang thai van don chu khong chi phu thuoc gia tri lech. Hai, doi ngay
	con keo theo viec go khoi chuyen cu. Ba, day la o duy nhat ma may KHONG
	duoc phep tu quyet trong moi tinh huong.
	"""
	try:
		ngay_moi = _ngay_tu_iso(o.get("estimate_delivery_date"))
		if not ngay_moi:
			return
		ngay_cu = str(cu.get("ngay_giao") or "")[:10]
		if not ngay_cu or ngay_cu == ngay_moi:
			return
		ma = str(o.get("display_id") or pid)
		co_chuyen = bool((cu.get("chuyen") or "").strip() or (cu.get("shipper") or "").strip())
		qua_han = 1 if ngay_cu < nowdate() else 0
		luat = luat_doi_ngay(cu.get("trang_thai"), co_chuyen, qua_han)
		if luat == DOI_NGAY_CHAN:
			nhat_ky.ghi(
				"van_don", ma, "Van Don", cu.name, "Pancake doi ngay giao khi dang giao",
				"ngay_giao", ngay_cu, ngay_moi, can_nguoi_xem=1,
				ghi_chu=("Shipper dang cam hang tren duong nen may KHONG tu doi ngay. "
				         "Nho dieu phoi goi shipper roi tu doi tay."),
			)
			return
		if not luat:
			# Van don da giao xong, khong giao duoc, hoac da huy. Viec xong roi.
			return
		doi = {"ngay_giao": ngay_moi}
		can_xem = 0
		ghi_chu = ""
		if luat == DOI_NGAY_CANH_BAO:
			# Chuyen duoc xep theo NGAY. Don da doi sang ngay khac ma con
			# nam trong chuyen cu thi chuyen do sai, va thu tu diem dung cua
			# ca chuyen sai theo.
			doi["chuyen"] = ""
			doi["thu_tu"] = 0
			can_xem = 1
			if (cu.get("trang_thai") or "").strip() == "Đang giao":
				ghi_chu = ("Van don nay nam o trang thai Dang giao ma ngay giao da "
				           "troi qua, nen may hieu la trang thai bo quen chu khong "
				           "phai shipper dang tren duong. Da doi ngay theo Pancake. "
				           "Nho dieu phoi soat lai trang thai giup.")
			else:
				ghi_chu = ("Don da duoc go khoi chuyen %s vi doi sang ngay khac. "
				           "Nho dieu phoi xep lai tuyen cho ngay moi."
				           % ((cu.get("chuyen") or "").strip() or "(chua dat ten)"))
		frappe.db.set_value("Van Don", cu.name, doi, update_modified=False)
		nhat_ky.ghi(
			"van_don", ma, "Van Don", cu.name, "doi ngay giao theo Pancake",
			"ngay_giao", ngay_cu, ngay_moi, can_nguoi_xem=can_xem, ghi_chu=ghi_chu,
		)
	except Exception:
		# Ngay giao hong thi phan con lai cua nhip van phai chay.
		frappe.log_error(frappe.get_traceback(), "van_don: theo ngay giao")


def _theo_don_huy(o):
	"""Pancake bao don da huy hoac da xoa thi van don ben minh phai biet.

	Khong dung "xoa" bao gio, chi chuyen trang thai va ghi vet - QT-20.
	"""
	try:
		pid = str(o.get("id") or "")
		if not pid:
			return
		cu = frappe.db.get_value(
			"Van Don", {"pancake_id": pid}, ["name", "trang_thai", "chuyen"], as_dict=True
		)
		if not cu:
			return
		ma = str(o.get("display_id") or pid)
		tt = (cu.get("trang_thai") or "").strip()
		if tt == "Chờ giao":
			frappe.db.set_value(
				"Van Don", cu.name,
				{"trang_thai": "Huỷ", "chuyen": "", "thu_tu": 0,
				 "ly_do_loi": "Pancake bao don da huy"},
				update_modified=False,
			)
			nhat_ky.ghi(
				"van_don", ma, "Van Don", cu.name, "huy van don theo Pancake",
				"trang_thai", tt, "Huỷ", can_nguoi_xem=0,
				ghi_chu="Don chua roi tiem nen may tu huy van don.",
			)
			return
		if tt == "Đang giao":
			nhat_ky.ghi(
				"van_don", ma, "Van Don", cu.name, "Pancake huy don khi dang giao",
				"trang_thai", tt, "Huỷ", can_nguoi_xem=1,
				ghi_chu=("Shipper dang cam hang tren duong. May KHONG tu huy. "
				         "Nho dieu phoi goi shipper ngay."),
			)
			return
		# Da giao, khong giao duoc, hoac da huy san: khong dung toi.
	except Exception:
		frappe.log_error(frappe.get_traceback(), "van_don: theo don huy")


def _dong_bo_pancake(ngay=None):
	"""Ruot cua dong_bo_pancake, khong kiem quyen - de scheduler goi duoc."""
	ngay = ngay or nowdate()
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id):
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")

	dau, cuoi = _khoang_unix(ngay)
	try:
		ds = _keo_don(c, k, "estimate_delivery_date", dau, cuoi)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "van_don: dong bo Pancake")
		frappe.throw("Pancake chưa trả dữ liệu, anh chị vui lòng thử lại sau ít phút.")

	them, da_co, bo_qua, lam_moi = 0, 0, 0, 0
	for o in ds:
		if (o.get("status") or 0) in BO_QUA_TT:
			bo_qua += 1
			# Truoc 19/08/2026 cho nay bo qua HOAN TOAN, ke ca khi ben minh
			# da co van don. Hau qua: khach huy don tren Pancake ma shipper
			# van thay don cho giao, van xep tuyen, van chay di giao mot don
			# khong con ton tai.
			_theo_don_huy(o)
			continue
		pid = str(o.get("id") or "")
		if not pid:
			bo_qua += 1
			continue
		cu = frappe.db.get_value(
			"Van Don", {"pancake_id": pid},
			# Phai doc DU moi truong se so sanh ben duoi. Thieu mot truong la
			# lan nao chay cung thay "khac" roi ghi lai ca don, 5 phut mot lan
			# (bat duoc 10/08/2026: thieu buoi, goi_truoc, chup_truoc nen
			# 12/15 don bi ghi lai moi vong du khong ai sua gi).
			[
				"name", "trang_thai", "tag_gio", "phuong", "ghi_chu_in", "the_don",
				"khach", "sdt", "nguoi_nhan", "sdt_nhan",
				"buoi", "goi_truoc", "chup_truoc",
				"dia_chi", "gio_giao", "ghi_chu", "tien_thu_ho",
				# Ba o duoi day KHONG nam trong vong so sanh chung ma danh
				# rieng cho luat doi ngay giao, xem luat_doi_ngay().
				"ngay_giao", "chuyen", "shipper",
			],
			as_dict=True,
		)
		if cu:
			da_co += 1
			# Don da keo ve van phai bam theo Pancake: khach doi dia chi, doi
			# gio, them bot banh, chuyen khoan truoc... deu phai sang day
			# (Loan Anh 10/08/2026). KHONG dung toi nhung gi sales va shipper
			# da dat: shipper, chuyen, trang thai, anh giao, doi soat.
			if cu.trang_thai in ("Chờ giao", "Đang giao"):
				si_cu = frappe.db.get_value(
					"Sales Invoice",
					{"custom_pancake_id": pid, "docstatus": ["<", 2]},
					["name", "grand_total", "outstanding_amount", "vgb_pt_thanh_toan"],
					as_dict=True,
				)
				sa2 = o.get("shipping_address") or {}
				moi = _tu_pancake(o)
				moi["dia_chi"] = (sa2.get("full_address") or sa2.get("address") or "").strip()
				moi["gio_giao"] = _gio_tu_iso(o.get("estimate_delivery_date"))
				moi["ghi_chu"] = (o.get("note") or "").strip()
				moi["tien_thu_ho"] = _cod_tu_don(o, si_cu)
				# NGAY GIAO di duong rieng, khong tha vao vong so sanh chung.
				# Vong chung chi biet "khac thi ghi de", ma ngay giao thi tuy
				# trang thai van don moi biet duoc phep de hay khong.
				_theo_ngay_giao(o, cu, pid)
				doi = {}
				for k2, v2 in moi.items():
					if k2 not in cu:
						continue
					if k2 == "tien_thu_ho":
						if abs(flt(cu.get(k2)) - flt(v2)) >= 1:
							doi[k2] = v2
						continue
					if k2 in ("goi_truoc", "chup_truoc"):
						if cint(cu.get(k2)) != cint(v2):
							doi[k2] = v2
						continue
					if str(cu.get(k2) or "").strip() != str(v2 or "").strip():
						doi[k2] = v2
				if doi:
					frappe.db.set_value("Van Don", cu.name, doi, update_modified=False)
					lam_moi += 1
					nhat_ky.ghi_nhieu(
						"van_don", str(o.get("display_id") or pid), "Van Don",
						cu.name, "Pancake sua don",
						{k3: (cu.get(k3), v3) for k3, v3 in doi.items()},
					)
				# Bang mon: khach them banh hay doi loi chuc thi ghi lai.
				mon_moi = _mon_tu_pancake(o)
				if mon_moi and _mon_khac(cu.name, mon_moi):
					_ghi_mon(cu.name, mon_moi)
					if not doi:
						lam_moi += 1
			# Don keo ve truoc luc co bang mon thi nap bu ngay o day.
			elif not frappe.db.exists("Van Don Mon", {"parent": cu.name}):
				_ghi_mon(cu.name, _mon_tu_pancake(o))
			continue
		sa = o.get("shipping_address") or {}
		if str(o.get("received_at_shop") or "").lower() in ("true", "1"):
			kenh = "Khách tự lấy"
		else:
			kenh = "Shipper nội bộ"
		si = frappe.db.get_value(
			"Sales Invoice",
			{"custom_pancake_id": pid, "docstatus": ["<", 2]},
			["name", "grand_total", "outstanding_amount", "vgb_pt_thanh_toan"],
			as_dict=True,
		)
		moi_vd = frappe.get_doc(
			dict(
				{
					"doctype": "Van Don",
					"hoa_don": si.name if si else None,
					"ma_don": str(o.get("display_id") or pid),
					"dia_chi": (sa.get("full_address") or sa.get("address") or "").strip(),
					"ngay_giao": ngay,
					"gio_giao": _gio_tu_iso(o.get("estimate_delivery_date")),
					"kenh": kenh,
					"tien_thu_ho": _cod_tu_don(o, si),
					"ghi_chu": (o.get("note") or "").strip(),
					"pancake_id": pid,
				},
				**_tu_pancake(o)
			)
		)
		moi_vd.insert(ignore_permissions=True)
		mon = _mon_tu_pancake(o) or _mon_tu_hoa_don(si.name if si else None)
		if mon:
			_ghi_mon(moi_vd.name, mon)
		them += 1
	frappe.db.commit()
	return {"them": them, "da_co": da_co, "lam_moi": lam_moi, "bo_qua": bo_qua,
		"tong": len(ds), "ngay": str(ngay)}


def dong_bo_tu_dong():
	"""Scheduler goi 5 phut mot lan: keo don hom nay va ngay mai.

	Khach sua don tren Pancake luc nao cung duoc, nen ben app phai tu bam
	theo chu khong doi sales bam nut (Loan Anh 10/08/2026). Ngay mai cung
	keo vi sales chot don giao hom sau tu chieu hom truoc.
	"""
	for ngay in (nowdate(), add_days(nowdate(), 1)):
		try:
			_dong_bo_pancake(ngay)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "van_don: dong bo tu dong %s" % ngay)


TRUONG_DS = [
	"name", "ma_don", "khach", "sdt", "dia_chi", "gio_giao", "trang_thai",
	"kenh", "shipper", "diem_pickup", "nguoi_trao", "tien_thu_ho", "phi_giao", "anh_giao", "booking_id", "tracking_url",
	"ly_do_loi", "chuyen", "da_doi_soat", "nguoi_nhan", "sdt_nhan",
	"tag_gio", "buoi", "phuong", "the_don", "goi_truoc", "chup_truoc", "ghi_chu_in",
	"thu_tu", "gio_du_kien", "km_chang", "tre_khung_gio", "lat", "lng",
	# Dieu chuyen kho noi bo (04/09/2026). Phai nam trong danh sach nay thi
	# dong tren man Van don moi bay duoc chieu di va dieu kien bao quan; thieu
	# thi lai quay ve canh chi thay ten kho nhan tro tren nhu truoc.
	"la_dieu_chuyen", "chung_tu_goc", "tt_chung_tu", "kho_xuat", "kho_nhan",
	"dia_chi_lay", "nguoi_giao", "sdt_giao", "so_kien", "bao_quan", "phut_ngoai_lanh",
]


@frappe.whitelist()
def danh_sach(ngay=None, trang_thai=None, phuong=None, tag_gio=None, buoi=None,
	chuyen=None, shipper=None, chua_gan=None):
	"""Danh sach van don theo ngay, loc them theo phuong / khung gio / buoi /
	chuyen de sales xep tuyen. Shipper (khong phai sales) chi thay don cua
	minh hoac don noi bo chua ai nhan."""
	_kiem_quyen_xem()
	loc = {"ngay_giao": ngay or nowdate()}
	for truong, gt in (("trang_thai", trang_thai), ("phuong", phuong),
		("tag_gio", tag_gio), ("buoi", buoi), ("chuyen", chuyen), ("shipper", shipper)):
		if gt:
			loc[truong] = gt
	if cint(chua_gan):
		loc["shipper"] = ["in", ["", None]]
	ds = frappe.get_all(
		"Van Don",
		filters=loc,
		fields=TRUONG_DS,
		order_by="thu_tu asc, tag_gio asc, gio_giao asc, creation asc",
		limit_page_length=500,
	)
	if _la_shipper() and not _la_sales():
		# Anh Viet 03/08/2026: man hinh shipper chi hien dung don duoc phan cong,
		# khong hien don chua ai nhan nua cho do roi.
		toi = frappe.session.user
		ds = [d for d in ds if d.shipper == toi]
	_gan_tom_tat_mon(ds)
	return ds


def _gan_tom_tat_mon(ds):
	"""Gan so mon va dong tom tat mon vao tung van don trong danh sach.

	Doc mot lan cho ca danh sach chu khong doc tung don - danh sach mot ngay
	co the toi 500 don, doc tung don la app dung hinh.
	"""
	if not ds:
		return
	ten = [d["name"] for d in ds]
	rows = frappe.get_all(
		"Van Don Mon",
		filters={"parent": ["in", ten]},
		fields=["parent", "ten", "ma_hang", "so_luong", "tang"],
		order_by="parent asc, idx asc",
		limit_page_length=0,
	)
	theo_don = {}
	for r in rows:
		theo_don.setdefault(r.parent, []).append(r)

	# Anh mon, de shipper nhin mat banh la nhan ra don, khoi doc ten mon.
	# Doc mot lan cho ca danh sach giong nhu doc mon o tren.
	ma_hang = set()
	for mon in theo_don.values():
		for m in mon:
			if m.ma_hang:
				ma_hang.add(m.ma_hang)
	anh = {}
	if ma_hang:
		for it in frappe.get_all(
			"Item",
			filters={"name": ["in", sorted(ma_hang)]},
			fields=["name", "image"],
			limit_page_length=0,
		):
			if it.image:
				anh[it.name] = it.image

	for d in ds:
		mon = theo_don.get(d["name"], [])
		d["so_mon"] = len(mon)
		d["so_luong_mon"] = sum(flt(m.so_luong) for m in mon)
		d["anh"] = ""
		for m in mon:
			if anh.get(m.ma_hang):
				d["anh"] = anh[m.ma_hang]
				break
		d["mon_chinh"] = (mon[0].ten or mon[0].ma_hang or "") if mon else ""
		d["mon_tat"] = " · ".join(
			"%s%s%s" % (
				("%g× " % flt(m.so_luong)) if flt(m.so_luong) != 1 else "",
				m.ten or m.ma_hang or "",
				" (tặng)" if m.tang else "",
			)
			for m in mon[:6]
		) + (" ..." if len(mon) > 6 else "")


@frappe.whitelist()
def bo_loc(ngay=None):
	"""Cac gia tri co that trong ngay de dung menu loc: khung gio, phuong,
	chuyen, va so don con thieu the khung gio (sales phai gan them ben Pancake).
	"""
	_kiem_quyen_xem()
	ds = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate()},
		fields=["tag_gio", "buoi", "phuong", "chuyen", "shipper", "trang_thai", "ma_don"],
		limit_page_length=500,
	)
	gio, phuong, chuyen, thieu = {}, {}, {}, []
	for d in ds:
		if d.trang_thai in ("Huỷ",):
			continue
		if (d.tag_gio or "").strip():
			gio[d.tag_gio] = gio.get(d.tag_gio, 0) + 1
		elif d.trang_thai == "Chờ giao":
			thieu.append(d.ma_don)
		if (d.phuong or "").strip():
			phuong[d.phuong] = phuong.get(d.phuong, 0) + 1
		if (d.chuyen or "").strip():
			chuyen[d.chuyen] = chuyen.get(d.chuyen, 0) + 1
	sxg = sorted(gio.items(), key=lambda x: x[0])
	return {
		"khung_gio": [{"v": k, "n": v} for k, v in sxg],
		"phuong": [{"v": k, "n": v} for k, v in sorted(phuong.items(), key=lambda x: -x[1])],
		"chuyen": [{"v": k, "n": v} for k, v in sorted(chuyen.items(), reverse=True)],
		"thieu_the_gio": thieu[:80],
		"so_thieu_the_gio": len(thieu),
		"tong": len(ds),
	}


def _qr_svg(noi_dung):
	"""Ma QR dang SVG noi thang vao HTML - khong can tep anh, in ra net.

	Dung pyqrcode co san trong Frappe (module xac thuc hai lop dung no).
	Khong co thi tra chuoi rong, phieu van in binh thuong.
	"""
	try:
		import pyqrcode
	except Exception:
		return ""
	try:
		qr = pyqrcode.create(noi_dung, error="M")
		luoi = qr.code  # list cac hang, 1 la o den
	except Exception:
		frappe.log_error(frappe.get_traceback(), "van_don: dung ma QR loi")
		return ""
	vien = 2
	n = len(luoi) + vien * 2
	o = []
	for y, hang in enumerate(luoi):
		x = 0
		while x < len(hang):
			if hang[x]:
				x2 = x
				while x2 + 1 < len(hang) and hang[x2 + 1]:
					x2 += 1
				o.append('<rect x="%d" y="%d" width="%d" height="1"/>' % (x + vien, y + vien, x2 - x + 1))
				x = x2 + 1
			else:
				x += 1
	return (
		'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges">'
		'<rect width="%d" height="%d" fill="#ffffff"/><g fill="#000000">%s</g></svg>'
	) % (n, n, n, n, "".join(o))


@frappe.whitelist()
def phieu_in(names):
	"""Du lieu day du de in phieu giao hang cho cac van don duoc chon.

	Ngoai truong cua van don, keo them danh sach mon tu hoa don ban hang de
	shipper doi chieu hop banh truoc khi roi tiem, va ten nguoi tao don.
	"""
	_kiem_quyen_xem()
	if isinstance(names, str):
		names = json.loads(names)
	if not names:
		frappe.throw("Chưa chọn vận đơn nào để in.")
	ra = []
	for nm in names[:60]:
		d = frappe.db.get_value(
			"Van Don", nm,
			TRUONG_DS + ["hoa_don", "ngay_giao", "ghi_chu", "owner", "la_dieu_chuyen",
				"chung_tu_goc", "tt_chung_tu", "kho_xuat", "kho_nhan", "dia_chi_lay",
				"nguoi_giao", "sdt_giao", "so_kien", "bao_quan", "phut_ngoai_lanh"],
			as_dict=True)
		if not d:
			continue
		# To in cua don dieu chuyen phai mang duoc ma vach so phieu, de kho
		# nhan quet thay vi go tay. Dung lai ham da co cua phieu nhap kho,
		# da kiem bang may quet that hoi 23/08 - dung khai @font-face.
		if cint(d.get("la_dieu_chuyen")) and d.get("chung_tu_goc"):
			d["ten_kho_xuat"] = _ten_kho_ngan(d.get("kho_xuat"))
			d["ten_kho_nhan"] = _ten_kho_ngan(d.get("kho_nhan"))
			try:
				from vagabond.ma_vach import code39_img

				d["ma_vach"] = code39_img(d["chung_tu_goc"], cao_mm=11, don_vi_mm=0.26)
			except Exception:
				d["ma_vach"] = ""
		d["ten_shipper"] = frappe.db.get_value("User", d.shipper, "full_name") if d.shipper else ""
		d["nguoi_tao"] = frappe.db.get_value("User", d.owner, "full_name") or d.owner or ""
		# Uu tien bang mon cua chinh van don: don keo tu Pancake ve thuong chua
		# co hoa don ban hang, lay theo hoa don la phieu in ra trang tron.
		d["mon"] = [
			{"item_code": m.ma_hang, "item_name": m.ten, "qty": m.so_luong,
				"amount": flt(m.so_luong) * flt(m.gia), "ghi_chu": m.ghi_chu,
				"tang": m.tang}
			for m in frappe.get_all(
				"Van Don Mon",
				filters={"parent": d.name},
				fields=["ma_hang", "ten", "so_luong", "gia", "ghi_chu", "tang"],
				order_by="idx asc",
				limit_page_length=100,
			)
		]
		if not d["mon"] and d.hoa_don:
			d["mon"] = frappe.get_all(
				"Sales Invoice Item",
				filters={"parent": d.hoa_don},
				fields=["item_code", "item_name", "qty", "amount"],
				order_by="idx asc",
				limit_page_length=100,
			)
		d["duong_dan"] = "%s/bep?vd=%s" % (frappe.utils.get_url().rstrip("/"), d.name)
		d["qr"] = _qr_svg(d["duong_dan"])
		ra.append(d)
	# giu dung thu tu tuyen de shipper cam xap giay la chay theo thu tu
	ra.sort(key=lambda x: (x.get("chuyen") or "", x.get("thu_tu") or 999, x.get("tag_gio") or ""))
	return ra


@frappe.whitelist()
def chuyen_cua_toi(ngay=None):
	"""Man hinh cua shipper: chuyen duoc giao hom nay, da sap dung thu tu.

	Thay cho to A4 in san dau ngay - shipper mo dien thoai la thay het."""
	_kiem_quyen_xem()
	toi = frappe.session.user
	ds = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate(), "shipper": toi},
		fields=TRUONG_DS,
		order_by="thu_tu asc, tag_gio asc, creation asc",
		limit_page_length=200,
	)
	gom = {}
	for d in ds:
		g = gom.setdefault(d.chuyen or "(chưa gộp chuyến)", {"chuyen": d.chuyen or "", "don": []})
		g["don"].append(d)
	ra = []
	for ten, g in gom.items():
		don = g["don"]
		ra.append({
			"chuyen": ten,
			"so_don": len(don),
			"con_lai": len([x for x in don if x.trang_thai in ("Chờ giao", "Đang giao")]),
			"tong_cod": sum(flt(x.tien_thu_ho) for x in don if x.trang_thai != "Đã giao"),
			"link_chi_duong": _maps_tu_don(don),
			"don": don,
		})
	return sorted(ra, key=lambda x: x["chuyen"])


def _maps_tu_don(don):
	"""Link Google Maps ca chuyen theo dung thu tu, mo mot phat di het tuyen."""
	from vagabond.xep_tuyen import _diem_lay_cf

	toa = [d for d in don if flt(d.lat) and flt(d.lng) and d.trang_thai in ("Chờ giao", "Đang giao")]
	if not toa:
		return ""
	c = cfg()
	d0 = _diem_lay_cf(c, "Bếp")
	diem = ["%s,%s" % (d0["lat"], d0["lng"])] + ["%s,%s" % (d.lat, d.lng) for d in toa]
	u = "https://www.google.com/maps/dir/?api=1&travelmode=driving&origin=%s&destination=%s" % (diem[0], diem[-1])
	giua = diem[1:-1]
	if giua:
		u += "&waypoints=" + "|".join(giua)
	return u


@frappe.whitelist()
def nhan_don(name):
	"""Shipper nhan don ve minh, chuyen Dang giao."""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	if doc.trang_thai not in ("Chờ giao", "Đang giao"):
		frappe.throw("Đơn đang ở trạng thái %s, không nhận được." % doc.trang_thai)
	doc.shipper = frappe.session.user
	doc.trang_thai = "Đang giao"
	doc.flags.ignore_permissions = True
	doc.save()
	return doc.name


@frappe.whitelist()
def giao_xong(name, file_url=None):
	"""Shipper bao giao thanh cong, kem anh da upload (file_url).
	Tu day trang thai da nhan sang Pancake neu co pancake_id."""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	if doc.trang_thai in ("Đã giao", "Huỷ"):
		frappe.throw("Đơn đã ở trạng thái %s." % doc.trang_thai)
	doc.trang_thai = "Đã giao"
	doc.giao_luc = now_datetime()
	if not doc.shipper and _la_shipper():
		doc.shipper = frappe.session.user
	# Don pickup khong co shipper nao ca. Nguoi bam hoan tat chinh la nguoi
	# dung tai quay trao hop banh cho khach, va do la nguoi duy nhat tra loi
	# duoc "ai dua hang cho khach" khi sau nay co khieu nai.
	if doc.diem_pickup and not doc.nguoi_trao:
		doc.nguoi_trao = frappe.session.user
	if file_url:
		doc.anh_giao = file_url
	bao = False
	if doc.pancake_id:
		bao = _day_trang_thai_pancake(doc.pancake_id, 3)
		doc.da_bao_pancake = 1 if bao else 0
		if not bao:
			doc.ghi_chu = ((doc.ghi_chu or "") + "\nChưa đẩy được trạng thái sang Pancake, sales kiểm lại.").strip()
	doc.flags.ignore_permissions = True
	doc.save()
	return {"name": doc.name, "da_bao_pancake": bao}


@frappe.whitelist()
def giao_loi(name, ly_do):
	"""Danh dau KHONG GIAO DUOC (khach khong nghe may, sai dia chi...).
	Khong dung den trang thai Pancake - sales tu xu ly don goc."""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	doc.trang_thai = "Không giao được"
	doc.ly_do_loi = ly_do
	doc.flags.ignore_permissions = True
	doc.save()
	return doc.name


@frappe.whitelist()
def huy_van_don(name):
	if not _la_sales():
		frappe.throw("Chỉ sales huỷ được vận đơn.")
	frappe.db.set_value("Van Don", name, "trang_thai", "Huỷ")
	return name


# ---------------------------------------------------------------- Gop chuyen

@frappe.whitelist()
def ds_shipper():
	"""Danh sach user co role Shipper de gan chuyen."""
	_kiem_quyen_xem()
	ds = frappe.get_all(
		"Has Role",
		filters={"role": "Shipper", "parenttype": "User"},
		fields=["parent"],
	)
	ra = []
	for r in ds:
		if r.parent in ("Administrator", "Guest"):
			continue
		if not frappe.db.get_value("User", r.parent, "enabled"):
			continue
		ra.append({"user": r.parent, "ten": frappe.db.get_value("User", r.parent, "full_name") or r.parent})
	return ra


# Don vi giao hang ngoai. Co API thi app tu goi xe duoc, khong co API thi
# chi danh dau de nhan vien tu dat tren app cua ho roi ghi nhan lai.
KENH_NGOAI = {
	"Ahamove": {"api": 1},
	"GreenSM": {"api": 1},
	"Grab": {"api": 0},
	"BE": {"api": 0},
	"Lalamove": {"api": 0},
}


@frappe.whitelist()
def gan_shipper(name, shipper=None, kenh=None, diem=None):
	"""Sales chi dinh nguoi giao cho MOT van don.

	- shipper = email nhan vien: don hien ngay tren man hinh shipper do,
	  va he thong gui email bao cho ban ay.
	- kenh = ten don vi ngoai (Ahamove, GreenSM, Grab, BE, Lalamove): danh dau
	  don di app ngoai. Don vi co API thi de trang thai Cho giao cho sales bam
	  Goi xe; don vi khong co API thi chuyen thang Dang giao vi nhan vien tu
	  dat tren app cua ho.
	- diem = ma diem pickup (SALES / TCV / NVHTN): khach ra tan noi lay,
	  khong ai chay xe. Xem vagabond/pickup.py.
	- ca ba rong: go ra, tra ve Cho giao.

	Ba loai loai tru nhau. Gan cai nay thi XOA cai kia, khong de mot don vua
	mang ten shipper vua mang ten diem - hai nguoi cung tuong don la cua minh
	la co ngay mot hop banh di hai duong.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales chỉ định người giao được.")
	doc = frappe.get_doc("Van Don", name)
	if doc.trang_thai in ("Đã giao", "Huỷ"):
		frappe.throw("Đơn đã ở trạng thái %s, không đổi người giao được." % doc.trang_thai)
	# Van don dieu chuyen: doc lai phieu goc NGAY LUC gan nguoi giao, khong
	# tin o `tt_chung_tu` da luu. Phieu co the bi huy sau luc lap van don, va
	# cho nay la cai cong cuoi truoc khi mot nguoi that su chay xe di lay hang.
	if cint(doc.get("la_dieu_chuyen")) and doc.get("chung_tu_goc"):
		ds_goc = frappe.db.get_value("Stock Entry", doc.chung_tu_goc, "docstatus")
		if ds_goc is None or cint(ds_goc) == 2:
			frappe.db.set_value("Van Don", doc.name, "tt_chung_tu", "Đã huỷ", update_modified=False)
			frappe.throw(
				"Phiếu điều chuyển %s đã bị huỷ nên không phân công giao được. "
				"Hàng không còn rời kho theo phiếu này nữa." % doc.chung_tu_goc)
	cu = doc.shipper
	if kenh:
		if kenh not in KENH_NGOAI:
			frappe.throw("Không biết đơn vị giao hàng %s." % kenh)
		doc.shipper = None
		doc.chuyen = ""
		doc.thu_tu = 0
		doc.diem_pickup = ""
		doc.kenh = kenh
		doc.trang_thai = "Chờ giao" if KENH_NGOAI[kenh]["api"] else "Đang giao"
	elif diem:
		ds_pk = pickup.ds()
		if not pickup.hop_le(diem, ds_pk):
			frappe.throw(pickup.loi_ma_la(diem, ds_pk))
		doc.shipper = None
		doc.chuyen = ""
		doc.thu_tu = 0
		doc.diem_pickup = pickup.chuan_ma(diem)
		doc.kenh = "Khách tự lấy"
		doc.trang_thai = pickup.TRANG_THAI
	elif shipper:
		doc.shipper = shipper
		doc.diem_pickup = ""
		doc.trang_thai = "Đang giao"
		if doc.kenh != "Shipper nội bộ":
			doc.kenh = "Shipper nội bộ"
	else:
		doc.shipper = None
		doc.chuyen = ""
		doc.thu_tu = 0
		doc.diem_pickup = ""
		doc.trang_thai = "Chờ giao"
	doc.flags.ignore_permissions = True
	doc.save()
	if doc.shipper and doc.shipper != cu:
		_mail_phan_cong(doc)
	return {"name": doc.name, "shipper": doc.shipper, "kenh": doc.kenh,
		"diem_pickup": doc.diem_pickup, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def ds_diem_pickup():
	"""Ba diem khach ra lay hang, cho o Phan cong tren app."""
	_kiem_quyen_xem()
	return pickup.ds()


def _mail_phan_cong(doc):
	"""Bao cho shipper biet vua co don moi. Hong thi bo qua, khong chan viec gan."""
	try:
		from vagabond.nhan_su import thu_phan_cong_html

		email = frappe.db.get_value("User", doc.shipper, "email") or doc.shipper
		ten = frappe.db.get_value("User", doc.shipper, "full_name") or ""
		frappe.sendmail(
			recipients=email,
			subject="Đơn giao mới: %s - %s" % (doc.ma_don or doc.name, doc.khach or ""),
			message=thu_phan_cong_html(ten, doc),
			delayed=False,
			retry=2,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: mail phan cong loi")


@frappe.whitelist()
def chuyen_dang_chay(ngay=None):
	"""Cac chuyen con don Dang giao trong ngay - de chen don moi vao
	chuyen dang chay thay vi tao chuyen moi."""
	_kiem_quyen_xem()
	rows = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate(), "trang_thai": "Đang giao", "chuyen": ["!=", ""]},
		fields=["chuyen", "shipper"],
		limit_page_length=300,
	)
	gom = {}
	for r in rows:
		g = gom.setdefault(r.chuyen, {"chuyen": r.chuyen, "shipper": r.shipper, "so_don": 0})
		g["so_don"] += 1
	ra = sorted(gom.values(), key=lambda x: x["chuyen"], reverse=True)
	for g in ra:
		g["ten_shipper"] = frappe.db.get_value("User", g["shipper"], "full_name") or g["shipper"] or ""
	return ra


@frappe.whitelist()
def gop_chuyen(names, shipper, chuyen=None):
	"""Gop nhieu van don thanh mot chuyen cho shipper noi bo - thao tac
	mot phat cho nhanh vi don hay phat sinh chen ngang (y Loan Anh).

	names: json list ten Van Don. chuyen bo trong = tao chuyen moi;
	truyen ma chuyen dang chay = chen them don vao chuyen do."""
	if not _la_sales():
		frappe.throw("Chỉ sales gộp chuyến được.")
	if isinstance(names, str):
		names = json.loads(names)
	if not names:
		frappe.throw("Chưa chọn đơn nào.")
	if not shipper:
		frappe.throw("Chưa chọn shipper.")
	if not chuyen:
		d = now_datetime().strftime("%d%m")
		n = 1
		while True:
			chuyen = "CH-%s-%d" % (d, n)
			if not frappe.db.exists("Van Don", {"chuyen": chuyen}):
				break
			n += 1
	bo_qua = []
	gan = 0
	for nm in names:
		doc = frappe.get_doc("Van Don", nm)
		if doc.trang_thai not in ("Chờ giao", "Đang giao"):
			bo_qua.append("%s (%s)" % (doc.ma_don or nm, doc.trang_thai))
			continue
		doc.shipper = shipper
		doc.chuyen = chuyen
		doc.diem_pickup = ""
		doc.trang_thai = "Đang giao"
		if doc.kenh != "Shipper nội bộ":
			doc.kenh = "Shipper nội bộ"
		doc.flags.ignore_permissions = True
		doc.save()
		gan += 1
	return {"chuyen": chuyen, "so_don": gan, "bo_qua": bo_qua}


# ---------------------------------------------------------------- Doi soat COD

@frappe.whitelist()
def doi_soat_cod(ngay=None):
	"""Tong COD da giao theo tung shipper trong ngay, tach phan chua
	doi soat de ke toan thu tien shipper nop ve cuoi ngay."""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ sales hoặc kế toán xem đối soát COD.")
	rows = frappe.get_all(
		"Van Don",
		filters={"ngay_giao": ngay or nowdate(), "trang_thai": "Đã giao"},
		fields=["name", "ma_don", "khach", "shipper", "kenh", "tien_thu_ho",
			"da_doi_soat", "chuyen", "pancake_id", "hoa_don"],
		order_by="shipper asc, creation asc",
		limit_page_length=500,
	)

	# Doc phuong thuc thanh toan cua tung don MOT LAN roi tra cuu trong bo nho,
	# chu khong hoi co so du lieu trong vong lap: 500 don la 500 luot hoi.
	ma_pancake = [r.pancake_id for r in rows if r.pancake_id]
	pt_theo_don = {}
	if ma_pancake:
		for si in frappe.get_all(
			"Sales Invoice",
			filters={"custom_pancake_id": ["in", ma_pancake], "docstatus": ["<", 2]},
			fields=["custom_pancake_id", "vgb_pt_thanh_toan"],
			limit_page_length=0,
		):
			pt_theo_don[si.custom_pancake_id] = si.vgb_pt_thanh_toan or ""

	gom = {}
	for r in rows:
		ai = r.shipper or ("(app ngoài: %s)" % (r.kenh or "?") if r.kenh != "Shipper nội bộ" else "(chưa gán shipper)")
		g = gom.setdefault(ai, {
			"shipper": ai, "ten": "", "so_don": 0, "tong_cod": 0,
			"chua_doi_soat": 0, "so_don_chua": 0, "so_don_chua_ro": 0, "don": [],
		})
		pt = pt_theo_don.get(r.pancake_id or "", "")
		thu = _pt_thu_tien_mat(pt)
		# Chua chon phuong thuc thi KHONG ket luan ho: bay co vang de sales
		# vao sua hoa don, chu doan bua rang do la COD la lai dung cai loi
		# vua sua (anh Viet 13/08/2026).
		chua_ro = thu is None

		# Tinh COD DONG chu khong tin so da luu tren van don. Nhip dong bo chi
		# cap nhat don con "Cho giao" hay "Dang giao", nen don da giao hom nay
		# se giu mai so cu sai. Tinh lai o day thi man doi soat dung ngay, khoi
		# phai di sua du lieu cu - va sua du lieu cu la viec anh Viet da dan
		# khong dung toi.
		cod = 0.0 if thu is False else flt(r.tien_thu_ho)
		lech = abs(cod - flt(r.tien_thu_ho)) >= 1

		g["so_don"] += 1
		g["tong_cod"] += cod
		if chua_ro:
			g["so_don_chua_ro"] += 1
		if not r.da_doi_soat:
			g["chua_doi_soat"] += cod
			g["so_don_chua"] += 1
		g["don"].append({
			"name": r.name, "ma_don": r.ma_don, "khach": r.khach,
			"cod": cod, "cod_tren_van_don": flt(r.tien_thu_ho), "lech": 1 if lech else 0,
			"da_doi_soat": r.da_doi_soat, "chuyen": r.chuyen,
			"pt": pt, "chua_ro": 1 if chua_ro else 0,
			"thu_tien_mat": 1 if thu else 0,
		})
	for ai, g in gom.items():
		if "@" in ai:
			g["ten"] = frappe.db.get_value("User", ai, "full_name") or ai
		else:
			g["ten"] = ai
	return sorted(gom.values(), key=lambda x: -x["tong_cod"])


@frappe.whitelist()
def xac_nhan_cod(shipper, ngay=None):
	"""Xac nhan DA NHAN DU tien COD shipper nop ve cho ngay do.
	Danh dau da_doi_soat len toan bo don Da giao cua shipper trong ngay.

	Sales duoc bam tu 13/08/2026 (anh Viet): cuoi ngay chinh cac ban Sales
	ngoi dem tien shipper nop ve, bat cho ke toan bam la viec ket lai den
	hom sau. Dau vet ai bam van luu trong nhat ky chung tu.
	"""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ sales hoặc kế toán xác nhận được tiền COD.")
	rows = frappe.get_all(
		"Van Don",
		filters={
			"ngay_giao": ngay or nowdate(), "trang_thai": "Đã giao",
			"shipper": shipper, "da_doi_soat": 0,
		},
		fields=["name", "tien_thu_ho", "pancake_id"],
		limit_page_length=500,
	)
	tong = 0
	for r in rows:
		frappe.db.set_value("Van Don", r.name, "da_doi_soat", 1)
		# Cong dung so ma man doi soat bay ra, khong cong so cu tren van don.
		pt = frappe.db.get_value(
			"Sales Invoice",
			{"custom_pancake_id": r.pancake_id or "", "docstatus": ["<", 2]},
			"vgb_pt_thanh_toan",
		) if r.pancake_id else None
		if _pt_thu_tien_mat(pt) is not False:
			tong += flt(r.tien_thu_ho)
	# Dau vet ai xac nhan: tien mat qua tay nguoi nen phai biet ai chot.
	if rows:
		try:
			frappe.get_doc({
				"doctype": "Comment", "comment_type": "Info",
				"reference_doctype": "Van Don", "reference_name": rows[0].name,
				"content": "Xác nhận đủ COD %s đ của %s ngày %s, bởi %s"
				% (tong, shipper, ngay or nowdate(), frappe.session.user),
			}).insert(ignore_permissions=True)
		except Exception:
			pass
	return {"so_don": len(rows), "tong": tong}


# ---------------------------------------------------------------- Book xe

def _diem_lay(c):
	return {
		"lat": flt(c.kitchen_lat), "lng": flt(c.kitchen_lng),
		"dia_chi": c.kitchen_address or "", "ten": "The Vagabond Patisserie",
	}


def _ahamove_dat_don(doc, service_id=None, them_reqs=None):
	from vagabond.dia_chi import geocode
	from vagabond.giao_hang import _token as _aha_token

	c = cfg()
	if not (key(c, "ahamove_api_key") and c.ahamove_base and c.ahamove_mobile):
		frappe.throw("Chưa cấu hình Ahamove trong Vagabond Settings.")
	if not (doc.dia_chi or "").strip():
		frappe.throw("Vận đơn chưa có địa chỉ giao.")
	toa = geocode(c, doc.dia_chi)
	if not toa or not toa.get("lat"):
		frappe.throw("Không tìm được toạ độ cho địa chỉ này, vui lòng sửa lại địa chỉ.")
	dv = (service_id or c.ma_dich_vu or "").strip()
	if them_reqs is None:
		reqs = []
		if c.dung_dich_vu_de_vo:
			reqs.append({"_id": dv + "-FRAGILE"})
	else:
		reqs = [{"_id": r} for r in them_reqs if r]
	body = {
		"order_time": 0,
		"path": [
			dict(_diem_lay(c), mobile=c.ahamove_mobile, name="The Vagabond", address=c.kitchen_address or ""),
			{
				"lat": toa["lat"], "lng": toa["lng"], "address": doc.dia_chi,
				"name": doc.khach or "Khách", "mobile": doc.sdt or c.ahamove_mobile,
				"cod": flt(doc.tien_thu_ho) or 0,
			},
		],
		# TAO don dung service_id (chuoi) + requests o cap cao nhat.
		# HOI PHI (/v3/orders/estimates) moi dung services: [{_id, requests}].
		# Truyen nham kieu cua endpoint hoi phi sang endpoint tao don thi Ahamove
		# tra 404 SERVICE_NOT_FOUND "Service does not exist" - loi anh Viet gap
		# 02/08/2026, du ma SGN-BIKE hoan toan hop le.
		"service_id": dv,
		"requests": reqs,
		"payment_method": "BALANCE",
		"remarks": "Đơn %s - %s" % (doc.ma_don or doc.name, doc.tag_gio or doc.gio_giao or ""),
	}
	body["path"][0].pop("dia_chi", None)
	body["path"][0].pop("ten", None)
	r = _mang().post(
		(c.ahamove_base or "").rstrip("/") + "/v3/orders",
		json=body,
		headers={"Authorization": "Bearer " + _aha_token(c)},
		timeout=TIMEOUT,
	)
	if r.status_code != 200:
		frappe.log_error(title="Vagabond: Ahamove dat don loi", message=r.text[:1000])
		frappe.throw("Ahamove từ chối đơn: %s" % r.text[:200])
	d = r.json() or {}
	oid = d.get("order_id") or (d.get("order") or {}).get("_id") or ""
	don = d.get("order") or {}
	phi = flt(don.get("total_fee") or don.get("total_pay") or 0)
	return oid, ("https://cloud.ahamove.com/share-order/%s" % oid if oid else ""), phi


def _greensm_token(c):
	"""OAuth2 client credentials, scope express.trips (sandbox.express.trips)."""
	ck = "vgb:gsm:token"
	hit = cache_get(ck)
	if hit:
		return hit
	scope = "sandbox.express.trips" if c.get("greensm_sandbox") else "express.trips"
	r = _mang().post(
		(c.greensm_token_url or "").strip(),
		data={
			"grant_type": "client_credentials",
			"client_id": c.greensm_client_id,
			"client_secret": key(c, "greensm_client_secret"),
			"scope": scope,
		},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	tok = (r.json() or {}).get("access_token")
	if not tok:
		frappe.throw("GreenSM không trả access_token, kiểm lại client_id/secret.")
	cache_set(ck, tok, 1500)
	return tok


def _greensm_base(c):
	if c.get("greensm_sandbox"):
		return "https://api-sandbox.vn.gsm-api.net/v1/sandbox/express"
	return "https://api-partner.vn.gsm-api.net/v1/express"


def _greensm_dat_don(doc):
	"""Khung tao don GreenSM Express. Payload chi tiet ho chua cong bo
	(trang create-order dang 'being prepared'), co key + spec thi chinh
	MAP_GSM ben duoi la chay."""
	c = cfg()
	if not (c.get("greensm_client_id") and key(c, "greensm_client_secret") and c.get("greensm_token_url")):
		frappe.throw(
			"GreenSM chưa có API key (đang chờ ký NDA). Khung đã dựng sẵn: "
			"ký xong anh điền Client ID, Client Secret, Token URL vào Vagabond Settings "
			"và nhớ đăng ký IP server với GreenSM (họ bắt whitelist IP)."
		)
	from vagabond.dia_chi import geocode

	toa = geocode(c, doc.dia_chi or "")
	diem = _diem_lay(c)
	MAP_GSM = {
		"pickup": {"lat": diem["lat"], "lng": diem["lng"], "address": diem["dia_chi"], "contact_name": "The Vagabond", "contact_phone": c.ahamove_mobile or ""},
		"dropoff": {"lat": (toa or {}).get("lat"), "lng": (toa or {}).get("lng"), "address": doc.dia_chi, "contact_name": doc.khach or "Khách", "contact_phone": doc.sdt or ""},
		"cod_amount": flt(doc.tien_thu_ho) or 0,
		"note": "Đơn %s - %s" % (doc.ma_don or doc.name, doc.gio_giao or ""),
	}
	r = _mang().post(
		_greensm_base(c) + "/create-order",
		json=MAP_GSM,
		headers={"Authorization": "Bearer " + _greensm_token(c)},
		timeout=TIMEOUT,
	)
	if r.status_code not in (200, 201):
		frappe.log_error(title="Vagabond: GreenSM dat don loi", message=r.text[:1000])
		frappe.throw("GreenSM từ chối đơn: %s" % r.text[:200])
	d = r.json() or {}
	oid = str(d.get("id") or d.get("order_id") or "")
	return oid, str(d.get("tracking_url") or ""), flt(d.get("total_fee") or 0)


@frappe.whitelist()
def book_xe(name, kenh, service_id=None, requests_them=None):
	"""Dat xe cho van don qua app ngoai.

	service_id va requests_them den tu man xac nhan trong app: nhan vien chon
	loai xe va tick add-on (giao tan tay, hang de vo...) roi moi bam Goi xe.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales book xe được.")
	doc = frappe.get_doc("Van Don", name)
	if doc.booking_id:
		frappe.throw("Đơn này đã book rồi (%s). Huỷ bên app kia trước nếu muốn book lại." % doc.booking_id)
	# Don khach tu lay khong co ai chay xe. Book xe cho no la mat tien that
	# cho mot cuoc xe khong ai di.
	if doc.diem_pickup:
		frappe.throw(
			"Đơn này đang để khách tự lấy tại điểm, không book xe được. "
			"Mở ô Phân công đổi sang shipper hoặc app ngoài trước nếu muốn giao tận nơi.")
	if isinstance(requests_them, str):
		requests_them = json.loads(requests_them or "[]")
	if kenh == "Ahamove":
		oid, link, phi = _ahamove_dat_don(doc, service_id, requests_them)
	elif kenh == "GreenSM":
		oid, link, phi = _greensm_dat_don(doc)
	elif kenh == "BE":
		frappe.throw("BE Delivery chưa cấp API (anh Việt đang xin). Có key là nối được, khung dùng chung với GreenSM.")
	else:
		frappe.throw("Kênh %s không book qua API được." % kenh)
	doc.kenh = kenh
	doc.booking_id = oid
	doc.tracking_url = link
	if phi:
		doc.phi_giao = phi
	doc.trang_thai = "Đang giao"
	doc.flags.ignore_permissions = True
	doc.save()
	return {"booking_id": oid, "tracking_url": link, "phi_giao": phi}


# ------------------------------------------------- Man xac nhan goi xe Ahamove

# Add-on bay ra nhieu, nhan vien khong can thay het. Day la nhung cai thuc su
# dung khi giao banh; con lai (SMS, khai gia, chung tu, quay dau...) an di.
AHA_ADDON_HIEN = ("D2D", "FRAGILE", "BULKY", "BAGA", "TIP")


def _aha_goi(c, duong_dan, phuong_thuc="GET", body=None):
	from vagabond.giao_hang import _token as _aha_token

	url = (c.ahamove_base or "").rstrip("/") + duong_dan
	dau = {"Authorization": "Bearer " + _aha_token(c)}
	if phuong_thuc == "POST":
		r = _mang().post(url, json=body or {}, headers=dau, timeout=TIMEOUT)
	else:
		r = _mang().get(url, headers=dau, timeout=TIMEOUT)
	if r.status_code != 200:
		frappe.log_error(title="Vagabond: Ahamove %s loi" % duong_dan, message=r.text[:1000])
		frappe.throw("Ahamove trả lỗi: %s" % r.text[:200])
	return r.json()


@frappe.whitelist()
def aha_dich_vu():
	"""Loai xe va add-on that cua Ahamove tai TPHCM, de app dung man goi xe."""
	if not _la_sales():
		frappe.throw("Chỉ sales gọi xe được.")
	c = cfg()
	if not (key(c, "ahamove_api_key") and c.ahamove_base):
		frappe.throw("Chưa cấu hình Ahamove trong Vagabond Settings.")
	ck = "vgb:aha:dichvu2"
	hit = cache_get(ck)
	if hit:
		# Phai nho ca goi {dich_vu, mac_dinh}, khong nho moi danh sach dich vu:
		# nho thieu thi lan goi sau app nhan ve mang tran, doc .dich_vu ra rong
		# va bao "Ahamove khong tra ve loai xe nao".
		return json.loads(hit)
	ds = _aha_goi(c, "/v3/services?city_id=SGN") or []
	ra = []
	for sv in ds:
		ma = sv.get("_id") or ""
		if "TRUCK" in ma:
			continue
		addon = []
		for rq in sv.get("requests") or []:
			duoi = (rq.get("_id") or "").replace(ma + "-", "")
			if duoi not in AHA_ADDON_HIEN:
				continue
			addon.append({
				"id": rq.get("_id"),
				"ten": (rq.get("name") or "").strip(),
				"gia": flt(rq.get("price") or 0),
			})
		ra.append({"id": ma, "ten": sv.get("name") or ma, "addon": addon})
	mac_dinh = (c.ma_dich_vu or "SGN-BIKE").strip()
	ra.sort(key=lambda x: 0 if x["id"] == mac_dinh else 1)
	goi = {"dich_vu": ra, "mac_dinh": mac_dinh}
	cache_set(ck, json.dumps(goi), 3600)
	return goi


@frappe.whitelist()
def aha_bao_gia(name, service_id=None, requests_them=None):
	"""Gia that cua Ahamove cho dung don nay, kem add-on da tick.

	Endpoint hoi phi dung `services: [{_id, requests}]`, KHAC endpoint tao don
	(dung service_id + requests o cap cao nhat). Truyen nham la 404.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales gọi xe được.")
	from vagabond.dia_chi import geocode

	if isinstance(requests_them, str):
		requests_them = json.loads(requests_them or "[]")
	c = cfg()
	doc = frappe.get_doc("Van Don", name)
	if not (doc.dia_chi or "").strip():
		frappe.throw("Vận đơn chưa có địa chỉ giao.")
	toa = geocode(c, doc.dia_chi)
	if not toa or not toa.get("lat"):
		frappe.throw("Không tìm được toạ độ cho địa chỉ này, vui lòng sửa lại địa chỉ.")
	diem = _diem_lay(c)
	body = {
		"order_time": 0,
		"path": [
			{"lat": diem["lat"], "lng": diem["lng"], "address": c.kitchen_address or ""},
			{"lat": toa["lat"], "lng": toa["lng"], "address": doc.dia_chi,
				"cod": flt(doc.tien_thu_ho) or 0},
		],
		"services": [{
			"_id": (service_id or c.ma_dich_vu or "SGN-BIKE").strip(),
			"requests": [{"_id": r} for r in (requests_them or []) if r],
		}],
		"payment_method": "BALANCE",
	}
	kq = _aha_goi(c, "/v3/orders/estimates", "POST", body)
	# Endpoint nay tra ve MANG: [{service_id, data:{...}, error}].
	# Truoc day doc thang .get() nen no van ra AttributeError 'list' object.
	if isinstance(kq, list):
		dau = (kq[0] if kq else {}) or {}
		loi = dau.get("error")
		if loi:
			frappe.throw("Ahamove: %s" % (loi if isinstance(loi, str) else str(loi))[:200])
		d = dau.get("data") or {}
	else:
		d = (kq or {}).get("data") or kq or {}
	# total_pay bang 0 khi tai khoan tra sau, nen lay total_fee lam gia chinh.
	tong = flt(d.get("total_fee") or d.get("total_pay") or 0)
	return {
		"tong": tong,
		"km": flt(d.get("distance") or 0),
		"phut": int(flt(d.get("duration") or 0) / 60),
		"phi_duong": flt(d.get("distance_fee") or 0),
		"phi_them": flt(d.get("request_fee") or 0),
		"giam": flt(d.get("discount") or 0),
	}


@frappe.whitelist(allow_guest=True)
def aha_webhook():
	"""Ahamove bao trang thai don. Quan tam nhat la tai xe huy.

	Khong xac thuc duoc bang chu ky nen chi tin phan doc: tra cuu lai don theo
	booking_id da luu, khong lay so lieu tien tu webhook.
	"""
	try:
		d = frappe.local.form_dict or {}
		if isinstance(d.get("data"), dict):
			d = d["data"]
		oid = str(d.get("_id") or d.get("order_id") or "").strip()
		tt = (d.get("status") or "").upper()
		if not oid:
			return {"ok": 0}
		name = frappe.db.get_value("Van Don", {"booking_id": oid}, "name")
		if not name:
			return {"ok": 0}
		if tt in ("CANCELLED", "CANCELED", "FAILED"):
			doc = frappe.get_doc("Van Don", name)
			if doc.trang_thai in ("Đã giao", "Huỷ"):
				return {"ok": 1}
			doc.booking_id = ""
			doc.tracking_url = ""
			doc.trang_thai = "Chờ giao"
			doc.ly_do_loi = "Tài xế Ahamove huỷ đơn"
			doc.flags.ignore_permissions = True
			doc.save()
			frappe.db.commit()
			_mail_tai_xe_huy(doc)
		return {"ok": 1}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: aha webhook loi")
		return {"ok": 0}


def _mail_tai_xe_huy(doc):
	"""Bao sales de phan cong lai ngay, khong de don nam im."""
	try:
		ds = frappe.get_all(
			"Has Role",
			filters={"role": "Sales User", "parenttype": "User"},
			fields=["parent"],
		)
		nhan = [r.parent for r in ds if r.parent not in ("Administrator", "Guest")
			and frappe.db.get_value("User", r.parent, "enabled")]
		if not nhan:
			return
		from vagabond.nhan_su import thu_tai_xe_huy_html

		frappe.sendmail(
			recipients=nhan,
			subject="Tài xế huỷ đơn: %s - %s" % (doc.ma_don or doc.name, doc.khach or ""),
			message=thu_tai_xe_huy_html(doc),
			delayed=False,
			retry=2,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: mail tai xe huy loi")


# ---------------------------------------------------------------- Chi phi shipper

@frappe.whitelist()
def tao_chi_phi(loai, so_tien, ngay=None, so_hoa_don=None, nha_cung_cap=None, ghi_chu=None, file_url=None):
	if not (_la_shipper() or _la_sales() or _la_ke_toan()):
		frappe.throw("Tài khoản chưa được cấp quyền khai chi phí.")
	doc = frappe.get_doc(
		{
			"doctype": "Chi Phi Shipper",
			"shipper": frappe.session.user,
			"ngay": ngay or nowdate(),
			"loai": loai,
			"so_tien": flt(so_tien),
			"so_hoa_don": so_hoa_don,
			"nha_cung_cap": nha_cung_cap,
			"ghi_chu": ghi_chu,
			"anh_hoa_don": file_url,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def gan_anh(doctype, name, fieldname, file_url):
	"""Gan anh vua upload vao truong Attach (anh_giao / anh_hoa_don)."""
	_kiem_quyen_xem()
	if doctype not in ("Van Don", "Chi Phi Shipper") or fieldname not in ("anh_giao", "anh_hoa_don", "chu_ky"):
		frappe.throw("Không hợp lệ.")
	frappe.db.set_value(doctype, name, fieldname, file_url)
	return name


# ------------------------------------------------- go tep dinh nham


# Truoc buoc nao thi con go duoc anh ra. Da doi soat COD roi thi to anh giao
# la can cu cua mot lan doi tien that, va chu ky la bang chung khach da nhan
# hang - go ra la lam thung ho so (QT-20, va luat khong dung vao du lieu qua
# khu anh Viet chot 13/08/2026).
TT_GO_DUOC_ANH = ("Chờ giao", "Đang giao")


@frappe.whitelist()
def go_anh(name=None, truong=None, tep=None):
	"""Go anh giao hang hoac chu ky dinh nham khoi van don. KHONG xoa tep.

	Anh Viet 24/08/2026 yeu cau moi hinh thu nho phai co nut X. Man nay
	truoc do khong go duoc gi: shipper chup nham don khac la tam anh do nam
	lai vinh vien, va sales van tai dung tam do gui khach.

	`truong` chi nhan hai o that: anh_giao va chu_ky. Nhan rong hon la mo
	duong cho mot cai bam nham xoa mat o khac tren cung van don.
	"""
	_kiem_quyen_xem()
	truong = str(truong or "").strip()
	if truong not in ("anh_giao", "chu_ky"):
		frappe.throw("Chỉ gỡ được ảnh giao hàng hoặc chữ ký.")
	if not frappe.db.exists("Van Don", name):
		frappe.throw("Không tìm thấy vận đơn %s. Vui lòng tải lại danh sách." % name)

	d = frappe.db.get_value(
		"Van Don", name, ["trang_thai", "da_doi_soat", "anh_giao", "chu_ky"], as_dict=True
	)
	if cint(d.get("da_doi_soat")):
		frappe.throw(
			"Vận đơn %s đã đối soát COD nên không gỡ ảnh ra được nữa. Tấm này là "
			"căn cứ của một lần đối tiền thật." % name
		)
	if truong == "chu_ky" and (d.get("trang_thai") or "") not in TT_GO_DUOC_ANH:
		frappe.throw(
			"Vận đơn %s đang ở \"%s\" nên không gỡ chữ ký ra được. Chữ ký là bằng "
			"chứng khách đã nhận hàng. Ký nhầm thì mời khách ký lại, bản mới đè lên "
			"bản cũ." % (name, d.get("trang_thai") or "")
		)

	# Man hinh chi giu duong dan chu khong giu ma File, nen cho phep tim theo
	# duong dan dang nam trong chinh o do. Van khoa theo dung van don nay, nen
	# khong mo duong doc chui sang don khac.
	loc = {"attached_to_doctype": "Van Don", "attached_to_name": name}
	if tep:
		loc["name"] = tep
	else:
		if not (d.get(truong) or "").strip():
			frappe.throw("Vận đơn %s chưa có %s nào để gỡ." % (name, truong))
		loc["file_url"] = d.get(truong)
	f = frappe.db.get_value("File", loc, ["name", "file_name", "file_url"], as_dict=True)
	if not f:
		# Tep cu tai len truoc khi co o attached_to co the khong con ban ghi
		# File nao. Van phai xoa duong dan trong o, khong thi man hinh ve mai
		# mot tam anh khong ai go duoc.
		if (d.get(truong) or "").strip():
			dat = {truong: None}
			if truong == "chu_ky":
				dat["ky_luc"] = None
			frappe.db.set_value("Van Don", name, dat, update_modified=False)
			frappe.db.commit()
			return {"ok": 1, "name": name, "truong": truong, "khong_thay_tep": 1}
		frappe.throw(
			"Tệp này không nằm trên vận đơn %s. Vui lòng tải lại trang rồi bấm lại." % name
		)
	frappe.db.set_value("File", f.name, {
		"attached_to_doctype": None, "attached_to_name": None,
	}, update_modified=False)
	# O tren van don tro toi tep vua go thi phai xoa theo, khong thi man hinh
	# van ve mot duong dan khong con ai giu.
	if (d.get(truong) or "") == (f.get("file_url") or ""):
		dat = {truong: None}
		if truong == "chu_ky":
			dat["ky_luc"] = None
		frappe.db.set_value("Van Don", name, dat, update_modified=False)
	try:
		frappe.get_doc("Van Don", name).add_comment(
			"Comment", "Gỡ %s (%s) khỏi vận đơn." % (truong, f.file_name or f.name)
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "van_don: ghi vet go anh")
	frappe.db.commit()
	return {"ok": 1, "name": name, "truong": truong}


CP_TRUONG = [
	"name", "shipper", "ngay", "loai", "so_tien", "so_hoa_don", "nha_cung_cap",
	"anh_hoa_don", "ghi_chu", "trang_thai", "ghi_chu_duyet", "ngay_hoan_ung",
]
CP_TRANG_THAI = ["Chờ duyệt", "Đã duyệt", "Từ chối", "Đã hoàn ứng"]
CP_LOAI = ["Đổ xăng", "Bảo trì xe", "Gửi xe", "Rửa xe", "Vá/thay vỏ xe", "Khác"]


def _chi_phi_quet(tu_ngay=None, den_ngay=None):
	"""Doc tho theo khoang ngay. Loc theo trang thai va loai lam o tren app
	de con so tren tung chip la con so that cua ca khoang."""
	loc = {}
	if tu_ngay and den_ngay:
		loc["ngay"] = ["between", [str(tu_ngay), str(den_ngay)]]
	elif tu_ngay:
		loc["ngay"] = [">=", str(tu_ngay)]
	elif den_ngay:
		loc["ngay"] = ["<=", str(den_ngay)]
	if _la_shipper() and not _la_ke_toan():
		loc["shipper"] = frappe.session.user
	return frappe.get_all(
		"Chi Phi Shipper",
		filters=loc,
		fields=CP_TRUONG,
		order_by="ngay desc, creation desc",
		limit_page_length=0,
	)


@frappe.whitelist()
def chi_phi_danh_sach(trang_thai=None, tu_ngay=None, den_ngay=None, loai=None):
	"""Ke toan / thu mua thay het; shipper chi thay cua minh.

	Chi Dung 13/08/2026 xin chip loc, chip trang thai va nut xuat Excel cho
	man nay de theo doi. Nen ham tra ve them phan DEM theo trang thai, theo
	loai va theo nguoi khai - de moi chip mang dung con so cua no.
	"""
	if not (_la_shipper() or _la_ke_toan() or _la_sales()):
		frappe.throw("Không có quyền.")
	ds = _chi_phi_quet(tu_ngay, den_ngay)
	dem_tt, dem_loai, dem_nguoi = {}, {}, {}
	tien_tt, tien_loai = {}, {}
	for r in ds:
		tt = (r.trang_thai or "Chờ duyệt").strip()
		lo = (r.loai or "Khác").strip()
		ng = (r.shipper or "").strip()
		dem_tt[tt] = dem_tt.get(tt, 0) + 1
		tien_tt[tt] = tien_tt.get(tt, 0) + flt(r.so_tien)
		dem_loai[lo] = dem_loai.get(lo, 0) + 1
		tien_loai[lo] = tien_loai.get(lo, 0) + flt(r.so_tien)
		if ng:
			dem_nguoi[ng] = dem_nguoi.get(ng, 0) + 1

	ra = ds
	if trang_thai:
		ra = [r for r in ra if (r.trang_thai or "") == trang_thai]
	if loai:
		ra = [r for r in ra if (r.loai or "") == loai]
	return {
		"rows": ra,
		"tong_dong": len(ra),
		"tong_tien": sum(flt(r.so_tien) for r in ra),
		"tat_ca": len(ds),
		"dem_trang_thai": dem_tt,
		"tien_trang_thai": tien_tt,
		"dem_loai": dem_loai,
		"tien_loai": tien_loai,
		"nguoi": sorted(dem_nguoi.keys()),
		"trang_thai_co": CP_TRANG_THAI,
		"loai_co": CP_LOAI,
		"la_ke_toan": 1 if _la_ke_toan() else 0,
	}


@frappe.whitelist()
def chi_phi_xuat_excel(tu_ngay=None, den_ngay=None, trang_thai=None, loai=None):
	"""Xuat danh sach chi phi ra .xlsx cho chi Dung theo doi.

	Tra base64 chu khong ghi file len may chu: so lieu song, luu file lai
	chi to cho nham lan giua ban cu va ban moi.
	"""
	if not (_la_ke_toan() or _la_sales()):
		frappe.throw("Chỉ kế toán, thu mua hoặc sales xuất được.")
	ds = _chi_phi_quet(tu_ngay, den_ngay)
	if trang_thai:
		ds = [r for r in ds if (r.trang_thai or "") == trang_thai]
	if loai:
		ds = [r for r in ds if (r.loai or "") == loai]

	bang = [
		["CHI PHÍ XĂNG XE - SỬA XE"],
		["Từ %s đến %s%s%s" % (
			tu_ngay or "đầu kỳ", den_ngay or "hôm nay",
			(" · %s" % trang_thai) if trang_thai else "",
			(" · %s" % loai) if loai else "",
		)],
		["Số khoản", len(ds), "Tổng tiền", sum(flt(r.so_tien) for r in ds)],
		[],
		["Mã", "Ngày", "Người khai", "Loại", "Số tiền", "Số hoá đơn",
		 "Nơi chi", "Trạng thái", "Ngày hoàn ứng", "Ghi chú", "Ghi chú duyệt"],
	]
	for r in ds:
		bang.append([
			r.name, str(r.ngay or ""), r.shipper or "", r.loai or "",
			flt(r.so_tien), r.so_hoa_don or "", r.nha_cung_cap or "",
			r.trang_thai or "", str(r.ngay_hoan_ung or ""),
			r.ghi_chu or "", r.ghi_chu_duyet or "",
		])
	bang.append([])
	bang.append(["TỔNG", "", "", "", sum(flt(r.so_tien) for r in ds)])

	import base64
	import io

	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, "Chi phi xe")
	noi_dung = tep.getvalue() if isinstance(tep, io.BytesIO) else tep
	return {
		"ten_file": "chi-phi-xe-%s-%s.xlsx" % (tu_ngay or "dau", den_ngay or nowdate()),
		"b64": base64.b64encode(noi_dung).decode(),
	}


@frappe.whitelist()
def duyet_chi_phi(name, hanh_dong, ghi_chu=None):
	"""hanh_dong: duyet / tu_choi / hoan_ung. Chi Thu mua / Ke toan."""
	if not _la_ke_toan():
		frappe.throw("Chỉ Thu mua hoặc Kế toán duyệt được.")
	doc = frappe.get_doc("Chi Phi Shipper", name)
	if hanh_dong == "duyet":
		doc.trang_thai = "Đã duyệt"
	elif hanh_dong == "tu_choi":
		doc.trang_thai = "Từ chối"
	elif hanh_dong == "hoan_ung":
		doc.trang_thai = "Đã hoàn ứng"
		doc.ngay_hoan_ung = nowdate()
	else:
		frappe.throw("Hành động không hợp lệ.")
	doc.nguoi_duyet = frappe.session.user
	if ghi_chu:
		doc.ghi_chu_duyet = ghi_chu
	doc.flags.ignore_permissions = True
	doc.save()
	return doc.trang_thai


# ---------------------------------------------------------------- Don dep anh

def don_dep_anh_giao():
	"""Cron chay hang ngay: xoa anh giao hang cua van don qua 30 ngay.

	CHI dong vao o `anh_giao`. Anh hoa don chi phi nam o doctype khac nen
	khong lien quan.

	SUA NGAY 24/08/2026 - nhip nay dang xoa ca CHU KY
	-------------------------------------------------
	Bo loc cu chi co `attached_to_doctype = "Van Don"`, khong loc theo o. Ma
	chu ky khach ky tay cung la mot tep dinh vao Van Don (xem luu_chu_ky),
	nen moi chu ky qua 30 ngay deu bi `delete_doc(force=True)` xoa VAT LY.

	Chinh docstring cua luu_chu_ky viet "Chu ky la chung tu giao nhan nen
	KHONG nam trong dien don dep anh sau 30 ngay" - loi hua do da bi chinh
	ham nay pha, im lang, suot tu luc dat nhip.

	Chu ky la chung tu giao nhan: mat no la mat bang chung khach da nhan
	hang, dung dieu QT-20 cam. Nay loc theo dung o `anh_giao`, va con mot
	lop chan thu hai o vong lap phong khi tep cu chua kip mang ten o.
	"""
	moc = add_days(nowdate(), -30)
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Van Don",
			"attached_to_field": "anh_giao",
			"creation": ["<", moc],
		},
		fields=["name", "attached_to_name", "file_url"],
		limit_page_length=500,
	)
	for f in files:
		try:
			vd, ky = frappe.db.get_value(
				"Van Don", f.attached_to_name, ["anh_giao", "chu_ky"]
			) or (None, None)
			# Lop chan thu hai: tep dang la chu ky cua don thi khong dung toi,
			# du bo loc tren da le ra loai no ra roi.
			if ky and ky == f.file_url:
				continue
			frappe.delete_doc("File", f.name, ignore_permissions=True, force=True)
			if vd and vd == f.file_url:
				frappe.db.set_value("Van Don", f.attached_to_name, "anh_giao", None)
		except Exception:
			frappe.log_error(title="Vagabond: don dep anh giao loi", message=frappe.get_traceback())
	frappe.db.commit()


@frappe.whitelist()
def mon_van_don(name=None):
	"""Danh sach mon day du cua mot van don, cho man chi tiet.

	Bang mon trong van don la nguon chinh. Chua co dong nao (van don keo ve
	tu truoc khi co bang nay) thi tu nap mot lan tu Pancake roi luu lai, lan
	sau khoi phai goi ra ngoai nua.
	"""
	_kiem_quyen_xem()
	d = frappe.db.get_value("Van Don", name, ["name", "pancake_id", "hoa_don"], as_dict=True)
	if not d:
		frappe.throw("Không thấy vận đơn %s" % name)
	mon = frappe.get_all(
		"Van Don Mon",
		filters={"parent": d.name},
		fields=["ma_hang", "ten", "so_luong", "gia", "tang", "ghi_chu"],
		order_by="idx asc",
		limit_page_length=0,
	)
	if mon:
		return mon
	nap = _mon_tu_pancake(_don_pancake(d.pancake_id)) if d.pancake_id else []
	if not nap:
		nap = _mon_tu_hoa_don(d.hoa_don)
	if nap:
		_ghi_mon(d.name, nap)
	return nap


@frappe.whitelist()
def nap_mon_thieu(ngay=None, gioi_han=60, lam_lai=0):
	"""Nap bu danh sach mon cho cac van don cu chua co.

	Chay tay mot lan cho du lieu cu. Moi don goi Pancake mot lan nen co gioi
	han so don moi luot, chay lai vai luot la het.
	"""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ sales và kế toán nạp được danh sách món.")
	loc = {}
	if ngay:
		loc["ngay_giao"] = ngay
	ds = frappe.get_all("Van Don", filters=loc, fields=["name", "pancake_id", "hoa_don"],
		order_by="ngay_giao desc", limit_page_length=500)
	xong, bo_qua = 0, 0
	for d in ds:
		if xong >= int(gioi_han or 60):
			break
		if not cint(lam_lai) and frappe.db.exists("Van Don Mon", {"parent": d.name}):
			continue
		nap = _mon_tu_pancake(_don_pancake(d.pancake_id)) if d.pancake_id else []
		if not nap:
			nap = _mon_tu_hoa_don(d.hoa_don)
		if nap:
			_ghi_mon(d.name, nap)
			xong += 1
		else:
			bo_qua += 1
	frappe.db.commit()
	return {"da_nap": xong, "khong_co_du_lieu": bo_qua, "tong_xet": len(ds)}


@frappe.whitelist()
def luu_chu_ky(name=None, anh=None, nguoi_ky=None):
	"""Luu chu ky khach ky tay tren man hinh cam ung vao van don.

	Anh gui len la data URL PNG cua the canvas. Luu thanh TEP dinh kem chu
	khong nhet chuoi base64 vao truong Data - de con mo lai, in ra, va de
	khong phinh bang du lieu.

	Chu ky la chung tu giao nhan nen KHONG nam trong dien don dep anh sau 30
	ngay (cron chi dong vao anh_giao).
	"""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	if not anh or "," not in anh:
		frappe.throw("Chưa có nét ký nào.")
	dau, phan = anh.split(",", 1)
	if "image/png" not in dau:
		frappe.throw("Chữ ký phải là ảnh PNG.")
	if len(phan) > 900000:
		frappe.throw("Chữ ký nặng quá, vui lòng ký lại.")

	tep = frappe.get_doc({
		"doctype": "File",
		"file_name": "chu-ky-%s.png" % doc.name,
		"attached_to_doctype": "Van Don",
		"attached_to_name": doc.name,
		"attached_to_field": "chu_ky",
		"is_private": 0,
		"content": phan,
		"decode": True,
	})
	tep.flags.ignore_permissions = True
	tep.insert(ignore_permissions=True)

	doc.chu_ky = tep.file_url
	doc.nguoi_ky = (nguoi_ky or doc.nguoi_nhan or doc.khach or "").strip()
	doc.ky_luc = now_datetime()
	doc.khong_ky = ""
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "chu_ky": doc.chu_ky, "nguoi_ky": doc.nguoi_ky, "ky_luc": str(doc.ky_luc)}


@frappe.whitelist()
def khach_khong_ky(name=None, ly_do=None):
	"""Khach khong ky duoc (gui bao ve, giao qua cua, khach ban tay).

	Van cho hoan thanh don - chan shipper lai vi mot chu ky la ket ca tuyen.
	Chi ghi lai ly do de sau con doi chieu.
	"""
	_kiem_quyen_xem()
	doc = frappe.get_doc("Van Don", name)
	doc.khong_ky = (ly_do or "Khách không ký").strip()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "khong_ky": doc.khong_ky}


# ------------------------------------------ Canh bao phuong thuc thanh toan


@frappe.whitelist()
def canh_bao_thanh_toan(so_ngay=7, ke_ca_nhap_lieu=0):
	"""Soát hoá đơn ghi sai hoặc thiếu phương thức thanh toán.

	Anh Việt 14/08/2026 hỏi: *"em có biện pháp gì cảnh báo với các hoá đơn
	chọn sai phương thức thanh toán chưa?"*

	Trước đây lỗi này chỉ lộ ra lúc đối soát COD cuối ngày, tức là sau khi
	shipper đã đi rồi. Đơn Oshima 1.480.000 hôm 13/08 là đúng kiểu đó: hoá
	đơn chưa chọn phương thức nên máy mặc định coi là thu tiền mặt, vận đơn
	mang COD, shipper đi đòi tiền của khách đã hẹn chuyển khoản.

	Ba loại lỗi soát ở đây, xếp theo mức nguy hiểm:
	  1. chua_chon  - hoá đơn chưa chọn phương thức. Nguy nhất vì máy đoán.
	  2. lech_cod   - hoá đơn ghi không thu tiền mặt mà vận đơn vẫn treo COD.
	  3. no_khong_khach - ghi Công nợ mà không gán khách, sau này không đòi ai.
	"""
	if not (_la_sales() or _la_ke_toan()):
		frappe.throw("Chỉ Sales và kế toán xem được cảnh báo thanh toán.")
	tu = add_days(nowdate(), -int(so_ngay or 7))
	hd = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "posting_date": [">=", tu]},
		fields=[
			"name", "posting_date", "customer", "grand_total", "outstanding_amount",
			"vgb_pt_thanh_toan", "vgb_khach_no", "custom_nguon", "owner",
		],
		limit_page_length=0,
		order_by="posting_date desc",
	)
	if not hd:
		return {"rows": [], "dem": {}, "tong": 0, "so_ngay": int(so_ngay or 7)}

	# COD dang treo tren van don, tra mot lan cho ca lo.
	cod = {}
	for v in frappe.get_all(
		"Van Don",
		filters={"hoa_don": ["in", [x["name"] for x in hd]], "docstatus": ["<", 2]},
		fields=["name", "hoa_don", "tien_thu_ho", "trang_thai"],
		limit_page_length=0,
	):
		if (v.get("trang_thai") or "") in ("Da huy", "Huy"):
			continue
		o = cod.setdefault(v["hoa_don"], {"tien": 0.0, "vd": []})
		o["tien"] += flt(v.get("tien_thu_ho"))
		o["vd"].append(v["name"])

	rows = []
	dem = {"chua_chon": 0, "lech_cod": 0, "no_khong_khach": 0}
	bo_qua_nhap = 0
	for r in hd:
		# Bo qua to nhap tu dot chuyen du lieu Fabi/m-invoice: 366 to trong
		# thang deu do Administrator dung len ngay 06 va 07/08, khong co
		# nguon don, va tat nhien khong co phuong thuc vi ben Fabi khong co
		# truong do. De chung vao thi man canh bao ra 368 dong, Sales mo len
		# mot lan roi thoi - canh bao ma keu suot thi thanh khong canh bao.
		if not cint(ke_ca_nhap_lieu):
			if r.get("owner") == "Administrator" and not (r.get("custom_nguon") or ""):
				bo_qua_nhap += 1
				continue
		pt = (r.get("vgb_pt_thanh_toan") or "").strip()
		c = cod.get(r["name"]) or {}
		tien_cod = flt(c.get("tien"))
		loi = None
		nhac = ""
		if not pt:
			loi = "chua_chon"
			nhac = (
				"Chưa chọn phương thức. Máy đang coi như thu tiền mặt, "
				"vận đơn sẽ mang COD %s đ." % "{:,.0f}".format(tien_cod)
			) if tien_cod else "Chưa chọn phương thức thanh toán."
		elif pt == "Công nợ" and not (r.get("vgb_khach_no") or r.get("customer")):
			loi = "no_khong_khach"
			nhac = "Ghi Công nợ mà chưa gán khách, sau này không biết đòi ai."
		elif tien_cod > 0 and _pt_thu_tien_mat(pt) is False:
			loi = "lech_cod"
			nhac = (
				"Hoá đơn ghi %s nhưng vận đơn vẫn treo COD %s đ. "
				"Shipper sẽ đi đòi tiền khách đã trả rồi." % (pt, "{:,.0f}".format(tien_cod))
			)
		if not loi:
			continue
		dem[loi] += 1
		rows.append({
			"hoa_don": r["name"],
			"ngay": str(r["posting_date"] or ""),
			"khach": r.get("vgb_khach_no") or r.get("customer") or "",
			"tong": flt(r["grand_total"]),
			"con_no": flt(r.get("outstanding_amount")),
			"pt": pt,
			"nguon": r.get("custom_nguon") or "",
			"cod": tien_cod,
			"van_don": ", ".join(c.get("vd") or []),
			"loi": loi,
			"nhac": nhac,
		})
	uu_tien = {"chua_chon": 0, "lech_cod": 1, "no_khong_khach": 2}
	rows.sort(key=lambda x: (uu_tien.get(x["loi"], 9), x["ngay"]), reverse=False)
	return {
		"rows": rows,
		"dem": dem,
		"tong": len(rows),
		"so_ngay": int(so_ngay or 7),
		"so_hoa_don_soat": len(hd),
		"bo_qua_nhap_lieu": bo_qua_nhap,
	}


# =====================================================================
# VAN DON DIEU CHUYEN NOI BO (anh Viet 04/09/2026)
# =====================================================================
#
# Anh Viet: *"Phan PDC va YCDC khi tao ben man Van Don bi thieu cac truong
# thong tin, dieu chuyen tu kho nao den kho nao, hang hoa la gi, noi file
# phieu dieu chuyen sang van don de in an ra"*.
#
# HIEN TRANG TRUOC BAN NAY. Khong he co duong noi nao giua phieu dieu chuyen
# va van don. Nguoi ta mo man Van don, bam dau cong, GO TAY so phieu vao o
# "So don" va go ten kho vao o "Khach". Ket qua do duoc tren du lieu that
# ngay 04/09:
#
#   - 146 van don dieu chuyen, TAT CA deu dang "Cho giao", KHONG to nao co
#     shipper. Man do la mot cho chua giay chu khong phai hang doi viec.
#   - Hai to tro vao phieu DA BI HUY (PDC-2026-00151, PDC-2026-00154). Phieu
#     goc huy roi ma van don van nam cho giao.
#   - O "Khach" va o "Dia chi" cung mang mot chuoi la ten kho NHAN. Kho XUAT
#     khong nam o dau ca, nen shipper khong biet di lay hang cho nao.
#   - Bang hang rong, nen to in ra khong co gi de doi chieu.
#
# QUYET DINH CUA ANH VIET 04/09/2026:
#   - CHI phieu dieu chuyen (Stock Entry) moi sinh van don. Yeu cau dieu
#     chuyen (Material Request) thi KHONG: no moi la loi de nghi, hang chua
#     roi kho. Ca 19 yeu cau dang co van don deu da "Transferred" bang phieu
#     khac roi, tuc van don do vua thieu tin vua het han dung.
#   - 146 to cu bo qua, chi lam cho tuong lai.

DC_BAO_QUAN = ("Thường", "Mát", "Đông")

# Tran thoi gian ngoai lanh, phut. Con so nay khong phai de trang tri: bo
# ghi len to in de shipper biet minh co bao lau, va de nguoi nhan biet luc
# nao thi phai tu choi lo hang.
DC_PHUT_NGOAI_LANH = {"Thường": 0, "Mát": 120, "Đông": 45}

# Dia chi that cua tung noi. Kho o he nay KHONG co o dia chi nao duoc dien
# (da kiem ca 22 kho ngay 04/09, address_line_1 va city deu rong), nen phai
# suy tu TEN kho. Suy theo ten thi mong manh, vi vay thu tu uu tien la:
# doc o dia chi cua chinh kho truoc, khong co moi suy theo ten.
DC_DIA_CHI = (
	("D1", "9 Trần Cao Vân, Quận 1"),
	("TRẦN CAO VÂN", "9 Trần Cao Vân, Quận 1"),
	("NVHTN", "21 Phạm Ngọc Thạch, Quận 3"),
	("PHẠM NGỌC THẠCH", "21 Phạm Ngọc Thạch, Quận 3"),
)
DC_DIA_CHI_MAC_DINH = "307/1 Nguyễn Văn Trỗi, Phường 1, Quận Tân Bình"


def dia_chi_kho(ten_kho, dia_chi_khai=""):
	"""Dia chi that de shipper toi lay hoac giao. THUAN.

	`dia_chi_khai` la o dia chi khai tren chinh phieu kho. Co thi dung ngay -
	ai do dien tay bao gio cung dung hon may suy theo ten. Khong co thi do
	ten kho; do khong ra thi ve xuong 307, vi phan lon kho nam o xuong.
	"""
	dc = str(dia_chi_khai or "").strip()
	if dc:
		return dc
	ten = str(ten_kho or "").upper()
	for khoa, dia in DC_DIA_CHI:
		if khoa in ten:
			return dia
	return DC_DIA_CHI_MAC_DINH


def doan_bao_quan(cac_ma_hang):
	"""Lo hang nay phai di lanh khong. THUAN, tra ve (bao_quan, so_phut).

	Doan theo tien to ma hang: hang dong lanh va hang mat deu bat dau bang
	NVLD / NVLM neu co, con lai coi la hang thuong. Chi la GOI Y ban dau,
	nguoi lap van don sua duoc tren man hinh - may doan sai mot lo bo thi
	mat tien that, nen khong bao gio khoa cung.
	"""
	ma = [str(x or "").upper() for x in (cac_ma_hang or [])]
	if any(x.startswith("NVLD") for x in ma):
		return "Đông", DC_PHUT_NGOAI_LANH["Đông"]
	if any(x.startswith("NVLM") for x in ma):
		return "Mát", DC_PHUT_NGOAI_LANH["Mát"]
	return "Thường", DC_PHUT_NGOAI_LANH["Thường"]


def _kho_chan(doc):
	"""Phieu nay co sinh van don duoc khong. Tra ve ly do neu khong."""
	if (doc.get("purpose") or "") != "Material Transfer":
		return "Phiếu %s không phải phiếu điều chuyển kho." % doc.name
	if cint(doc.get("docstatus")) != 1:
		return (
			"Phiếu %s chưa ghi sổ hoặc đã huỷ. Chỉ phiếu đã ghi sổ mới lập được "
			"vận đơn, vì hàng phải rời kho thật rồi mới có gì để chở." % doc.name)
	if not doc.get("from_warehouse") or not doc.get("to_warehouse"):
		return (
			"Phiếu %s không ghi rõ kho xuất hoặc kho nhận nên không biết chở từ "
			"đâu tới đâu." % doc.name)
	if doc.get("from_warehouse") == doc.get("to_warehouse"):
		return "Kho xuất và kho nhận trùng nhau, không có gì để chở."
	return ""


def van_don_cua_phieu(phieu):
	"""Phieu nay da co van don chua. Tra ve so van don, khong co thi rong.

	MOT PHIEU CHI MOT VAN DON. Bam hai lan thi mo lai to cu chu khong de hai
	to cung so chay song song, roi hai shipper cung di lay mot lo hang.

	DO THEO CA HAI O, khong chi o `chung_tu_goc`. Ly do: 146 van don lap
	truoc ban v411 deu duoc go tay, chung chi co so phieu nam trong o
	`ma_don` chu khong co o noi goc. Do bang mot o thi may khong thay chung,
	va bam nut se sinh to thu hai cho cung mot phieu.

	Do that ngay 04/09/2026 sau khi deploy v411: trong 30 phieu bay ra cho
	nguoi ta bam, 27 phieu DA CO van don go tay tu truoc. Tuc neu chi do o
	noi goc thi gan nhu bam cai nao cung ra to trung.
	"""
	if not phieu:
		return ""
	for loc in ({"chung_tu_goc": phieu}, {"ma_don": phieu}):
		loc["trang_thai"] = ["!=", "Huỷ"]
		ten = frappe.db.get_value("Van Don", loc, "name")
		if ten:
			return ten
	return ""


@frappe.whitelist()
def tao_van_don_dieu_chuyen(phieu=None, ngay_giao=None, ghi_chu=""):
	"""Sinh MOT van don day du tu MOT phieu dieu chuyen da ghi so.

	Day la duong dung. Truoc ban nay nguoi ta go tay so phieu va ten kho vao
	man tao van don khach le, nen khong co cho nao chua kho xuat, chung tu
	goc, hay danh sach hang.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales hoặc quản lý kho lập được vận đơn điều chuyển.")
	phieu = (phieu or "").strip()
	if not phieu or not frappe.db.exists("Stock Entry", phieu):
		frappe.throw("Không tìm thấy phiếu điều chuyển %s." % (phieu or ""))

	doc = frappe.get_doc("Stock Entry", phieu)
	vi_sao = _kho_chan(doc)
	if vi_sao:
		frappe.throw(vi_sao)

	cu = van_don_cua_phieu(phieu)
	if cu:
		return {"name": cu, "da_co": 1,
			"nhan": "Phiếu %s đã có vận đơn %s rồi." % (phieu, cu)}

	ma_hang = [d.item_code for d in doc.items]
	bao_quan, phut = doan_bao_quan(ma_hang)
	dc_lay = dia_chi_kho(doc.from_warehouse, doc.get("vgb_dia_chi_kho_xuat"))
	dc_giao = dia_chi_kho(doc.to_warehouse, doc.get("vgb_dia_chi_kho_nhan"))

	vd = frappe.new_doc("Van Don")
	vd.ma_don = doc.name
	vd.la_dieu_chuyen = 1
	vd.chung_tu_goc = doc.name
	vd.tt_chung_tu = "Đã ghi sổ"
	vd.kho_xuat = doc.from_warehouse
	vd.kho_nhan = doc.to_warehouse
	vd.dia_chi_lay = dc_lay
	vd.dia_chi = dc_giao
	# O "Khach" tren van don la thu bay ra dau danh sach. Voi don noi bo thi
	# thu can nhin nhat la CHIEU di, khong phai mot cai ten kho tro tren.
	vd.khach = "%s → %s" % (_ten_kho_ngan(doc.from_warehouse), _ten_kho_ngan(doc.to_warehouse))
	vd.ngay_giao = ngay_giao or nowdate()
	vd.trang_thai = "Chờ giao"
	vd.kenh = "Shipper nội bộ"
	vd.tien_thu_ho = 0
	vd.bao_quan = bao_quan
	vd.phut_ngoai_lanh = phut
	vd.so_kien = 0
	vd.ghi_chu = (ghi_chu or "").strip() or (doc.remarks or "")

	for d in doc.items:
		vd.append("mon", {
			"ma_hang": d.item_code,
			"ten": d.item_name,
			"so_luong": flt(d.qty),
			"gia": 0,
			"ghi_chu": (d.uom or ""),
		})

	vd.flags.ignore_permissions = True
	vd.insert(ignore_permissions=True)
	return {
		"name": vd.name, "da_co": 0,
		"nhan": "Đã lập vận đơn %s cho phiếu %s, %d món." % (vd.name, doc.name, len(doc.items)),
	}


def _ten_kho_ngan(ten):
	"""Bo duoi cong ty cho ten kho ngan lai. THUAN."""
	t = str(ten or "").strip()
	for duoi in (" - TVD", " - TV"):
		if t.endswith(duoi):
			return t[: -len(duoi)]
	return t


@frappe.whitelist()
def phieu_dieu_chuyen_lap_duoc(so_ngay=7):
	"""Cac phieu dieu chuyen da ghi so ma CHUA co van don.

	De man kho bay ra mot danh sach ngan cho nguoi ta bam, khoi phai nho so
	phieu. Chi nhin lai vai ngay gan day: phieu cu hon thi hang da di roi.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales hoặc quản lý kho xem được danh sách này.")
	from frappe.utils import add_days

	ds = frappe.get_all(
		"Stock Entry",
		filters={
			"purpose": "Material Transfer",
			"docstatus": 1,
			"posting_date": [">=", add_days(nowdate(), -int(so_ngay or 7))],
		},
		fields=["name", "posting_date", "from_warehouse", "to_warehouse"],
		order_by="posting_date desc, creation desc",
		limit_page_length=60,
	)
	if not ds:
		return []
	# Do ca hai o vi cung ly do o `van_don_cua_phieu`: van don go tay truoc
	# ban v411 chi mang so phieu trong `ma_don`.
	ten_ds = [x.name for x in ds]
	da_co = set()
	for o in ("chung_tu_goc", "ma_don"):
		for r in frappe.get_all(
			"Van Don",
			filters={o: ["in", ten_ds], "trang_thai": ["!=", "Huỷ"]},
			fields=[o], limit_page_length=0,
		):
			if r.get(o):
				da_co.add(r[o])
	return [
		{
			"phieu": x.name,
			"ngay": str(x.posting_date or ""),
			"kho_xuat": x.from_warehouse,
			"kho_nhan": x.to_warehouse,
			"chieu": "%s → %s" % (_ten_kho_ngan(x.from_warehouse), _ten_kho_ngan(x.to_warehouse)),
		}
		for x in ds if x.name not in da_co
	]


def dong_van_don_khi_huy_phieu(doc, method=None):
	"""Phieu dieu chuyen bi huy thi van don di kem phai tat theo.

	Hai to PDC-2026-00151 va PDC-2026-00154 dang nam "Cho giao" trong khi
	phieu goc da huy tu truoc. Khong ai bat duoc chuyen do vi van don khong
	biet gi ve phieu goc. Nay biet roi thi phai tu tat.

	Khong bao gio nem loi: huy mot phieu kho ma chet vi cai van don thi mat
	mot thao tac kho that vi mot to giay.
	"""
	try:
		for nm in frappe.get_all(
			"Van Don",
			filters={"chung_tu_goc": doc.name, "trang_thai": ["in", ["Chờ giao", "Đang giao"]]},
			pluck="name",
		):
			frappe.db.set_value("Van Don", nm, {
				"trang_thai": "Huỷ",
				"tt_chung_tu": "Đã huỷ",
				"ly_do_loi": "Phiếu điều chuyển %s đã bị huỷ nên vận đơn tự đóng." % doc.name,
			}, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "van_don: dong van don khi huy phieu loi")


@frappe.whitelist()
def luu_dieu_chuyen(name=None, so_kien=None, nguoi_giao=None, sdt_giao=None,
		nguoi_nhan=None, sdt_nhan=None, bao_quan=None, phut_ngoai_lanh=None):
	"""Sua cac o rieng cua van don dieu chuyen ngay tren app.

	May doan dieu kien bao quan theo tien to ma hang, doan sai mot lo bo la
	mat tien that, nen nguoi lap luon sua duoc. So kien thi may khong bao gio
	biet: dem thung la viec cua nguoi dong hang.
	"""
	if not _la_sales():
		frappe.throw("Chỉ sales hoặc quản lý kho sửa được vận đơn điều chuyển.")
	doc = frappe.get_doc("Van Don", name)
	if not cint(doc.get("la_dieu_chuyen")):
		frappe.throw("Vận đơn %s không phải vận đơn điều chuyển nội bộ." % name)
	if doc.trang_thai in ("Đã giao", "Huỷ"):
		frappe.throw("Đơn đã ở trạng thái %s, không sửa được nữa." % doc.trang_thai)

	if so_kien is not None:
		doc.so_kien = max(0, cint(so_kien))
	if bao_quan is not None:
		bq = str(bao_quan).strip()
		if bq not in DC_BAO_QUAN:
			frappe.throw("Điều kiện bảo quản phải là một trong: %s." % ", ".join(DC_BAO_QUAN))
		doc.bao_quan = bq
		# Doi kieu bao quan ma quen doi tran thoi gian thi to in noi doi. Chi
		# tu dat lai khi nguoi dung KHONG go tay so phut trong cung lan luu.
		if phut_ngoai_lanh is None:
			doc.phut_ngoai_lanh = DC_PHUT_NGOAI_LANH.get(bq, 0)
	if phut_ngoai_lanh is not None:
		doc.phut_ngoai_lanh = max(0, cint(phut_ngoai_lanh))
	for o, v in (("nguoi_giao", nguoi_giao), ("sdt_giao", sdt_giao),
			("nguoi_nhan", nguoi_nhan), ("sdt_nhan", sdt_nhan)):
		if v is not None:
			doc.set(o, str(v).strip())

	doc.flags.ignore_permissions = True
	doc.save()
	return {"name": doc.name, "so_kien": cint(doc.so_kien), "bao_quan": doc.bao_quan,
		"phut_ngoai_lanh": cint(doc.phut_ngoai_lanh)}

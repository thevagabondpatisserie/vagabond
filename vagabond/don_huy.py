"""Đơn Pancake ĐÃ HUỶ mà tiền khách vẫn còn nằm ở công ty.

Việc thật, anh Việt giao 21/08/2026 kèm ảnh ba đơn: 92252 (705.000 đ,
Ms.Như Duyên), 92245 (920.000 đ, Mr.Khoa Lê), 92156 (750.000 đ, Ms.Vi Aibi).

VÌ SAO PHẢI CÓ MÀN RIÊNG, KHÔNG DÙNG LẠI MÀN CŨ
-----------------------------------------------
Nút "Huỷ đơn và hoàn tiền" của v259 treo trên THẺ ĐƠN NHÁP, nên nó chỉ với
tới đúng một ca hẹp: đơn giao trong ngày, đã đồng bộ thành hoá đơn nháp, rồi
khách mới huỷ. Ba đơn anh Việt gửi không thuộc ca đó.

Lý do nằm ở hai tầng lọc của luồng đồng bộ, ghi trong
`claude/lo-hong-huy-don-khong-ve-he.md`:

- `ban_hang.TT_DOANH_SO = {3, 16}`: chỉ đơn đã nhận hoặc đã thu tiền mới
  thành Sales Invoice. Đơn huỷ mang trạng thái 6, không bao giờ lọt.
- Khung quét là NGÀY GIAO chứ không phải ngày đặt. Khách đặt hôm nay giao
  thứ Bảy rồi huỷ ngay chiều nay thì hôm nay đơn còn chưa vào khung quét.

Ghép lại: **những đơn này chưa bao giờ có hoá đơn trong ERPNext, và sẽ không
bao giờ có.** Không phải hoá đơn nháp, là không có gì cả. Nên phải đi tìm
chúng ở chính Pancake, và phải dò tiền bằng đường khác.

CÁCH DÒ TIỀN KHI KHÔNG CÓ HOÁ ĐƠN NÀO ĐỂ BÁM
--------------------------------------------
`ban_hang._sepay_theo_don` buộc một giao dịch vào đúng một đơn bằng cách đọc
`tabBank Transaction` và dò mạch `S<shop>O<id>T` mà Pancake sinh trong mã QR,
dò cả mã hiển thị kiểu WOO2749. Phép đó KHÔNG cần Sales Invoice nào, nên
dùng lại được nguyên vẹn ở đây.

BÚT TOÁN, CHỊ DUNG CHỐT 21/08/2026
----------------------------------
1. Mọi tiền vào lập phiếu thu ngay: Nợ 112 / Có 131, theo đơn.
2. Hoàn thì đủ HAI CHÂN. Máy sinh sẵn cả phiếu thu (lúc tiền vào) lẫn phiếu
   chi (lúc hoàn), cả hai ở dạng NHÁP.
3. Chứng từ gốc hai chiều đều lấy từ e-banking: giấy báo Có cho chiều vào,
   uỷ nhiệm chi cho chiều ra. SePay KHÔNG đủ. Khoản nhỏ dùng sao kê chính
   thức theo kỳ.
4. Theo dõi 131 theo SỐ ĐƠN ghi trong diễn giải, trên mã dùng chung
   "Khách lẻ Online". Số dư của mã bằng tổng đơn đã thu chưa giao chưa hoàn.

Điều 2 là lý do máy không được tự ghi sổ: phiếu nháp chờ kế toán đính chứng
từ e-banking rồi mới ghi. Đúng luật chị Dung chốt 16/08 và giữ nguyên từ đó.

BẢNG ĐỆM TỰ DỌN SAU 30 NGÀY
---------------------------
Anh Việt chốt: giữ 30 ngày rồi tự xoá. Chỗ này phải cẩn thận vì QT-20 cấm
xoá vĩnh viễn dữ liệu nghiệp vụ. Nên cái bị dọn CHỈ LÀ BẢN SAO đọc từ
Pancake của những đơn chưa phát sinh phiếu hoàn. Đơn đã sinh phiếu hoàn thì
giữ vĩnh viễn, vì lúc đó bản ghi là một mắt xích tra cứu. Và dù có dọn thì
nguồn sự thật vẫn nằm ở Pancake, đồng bộ lại là có ngay.
"""

import re
from datetime import datetime, timedelta

import frappe
from frappe.utils import add_days, flt, now_datetime

# Trạng thái Pancake 6 là đã huỷ, 7 là đã xoá. Chỉ lấy 6: đơn bị XOÁ là đơn
# nhập nhầm, không có khách nào chuyển tiền cho nó.
TT_HUY = 6

DT = "Vagabond Don Huy"

# Số ngày giữ bản đệm của đơn CHƯA phát sinh phiếu hoàn.
NGAY_GIU = 30

CHO_HOAN = "Cho hoan"
DANG_HOAN = "Dang hoan"
DA_HOAN = "Da hoan"
KHONG_PHAI = "Khong phai hoan"
BO_QUA = "Bo qua"

NHAN_TT = {
	CHO_HOAN: "Chờ hoàn",
	DANG_HOAN: "Đang hoàn",
	DA_HOAN: "Đã hoàn",
	KHONG_PHAI: "Không phải hoàn",
	BO_QUA: "Bỏ qua",
}

# Trạng thái hồ sơ hoàn tiền nào thì coi là xong. Đọc từ hoan_tien để không
# đẻ ra danh sách thứ hai (bài học 21/08/2026: hop_qua tự chế danh sách vai
# riêng và bỏ sót Sales User, Loan Anh không tuỳ biến hộp được).
TT_XONG = ("Hoan thanh",)
TT_HUY_HO_SO = ("Da huy",)


# ---------------------------------------------------------------- phép thuần


def la_don_huy(don):
	"""Đơn Pancake này có phải đơn đã huỷ không."""
	try:
		return int((don or {}).get("status")) == TT_HUY
	except (TypeError, ValueError):
		return False


def trang_thai_don(da_nhan, ho_so_trang_thai=None, bo_qua=0):
	"""Chip trạng thái của một đơn huỷ. Đây là phép quyết định cả màn hình.

	Thứ tự các nhánh là cố ý:

	- Người đã bấm Bỏ qua thì tôn trọng, không lôi ra nữa dù có tiền.
	- Chưa thấy đồng nào thì KHÔNG PHẢI HOÀN. Khách huỷ trước khi chuyển
	  tiền là ca thường gặp nhất, lôi vào danh sách chờ hoàn thì Sales phải
	  lọc tay mỗi ngày và sẽ bỏ sót ca thật.
	- Có hồ sơ hoàn rồi thì trạng thái đọc theo hồ sơ đó, không tự đoán.
	"""
	if int(bo_qua or 0):
		return BO_QUA
	if flt(da_nhan) <= 0:
		return KHONG_PHAI
	tt = (ho_so_trang_thai or "").strip()
	if not tt:
		return CHO_HOAN
	if tt in TT_HUY_HO_SO:
		# Hồ sơ bị huỷ hoặc bị từ chối thì tiền vẫn còn ở mình, việc quay
		# lại hàng chờ chứ không được coi là xong.
		return CHO_HOAN
	if tt in TT_XONG:
		return DA_HOAN
	return DANG_HOAN


def muc_hoan(da_nhan):
	"""Số tiền máy điền sẵn vào form hoàn.

	Anh Việt chốt 21/08/2026: hoàn 100% số khách đã chuyển, để số sửa được.
	Phần giữ lại (nếu có thoả thuận trừ tiền nguyên liệu) là DOANH THU và
	phải xuất hoá đơn riêng, nên KHÔNG gộp vào đây. Xem mục "Chỗ nên có
	chính sách thành văn" trong claude/hoan-tien-khi-hoa-don-con-nhap.md.
	"""
	return flt(da_nhan) if flt(da_nhan) > 0 else 0.0


def dem_theo_chip(cac_dong):
	"""Đếm số đơn theo từng chip, để chip hiện số mà không phải gọi lại."""
	dem = {k: 0 for k in NHAN_TT}
	for d in cac_dong or ():
		tt = (d.get("trang_thai") or "").strip()
		if tt in dem:
			dem[tt] += 1
	dem["tat_ca"] = len(cac_dong or ())
	return dem


def tien_cho_hoan(cac_dong):
	"""Tổng tiền đang giữ hộ khách, chỉ tính đơn còn phải hoàn."""
	return sum(flt(d.get("da_nhan")) for d in (cac_dong or ())
		if (d.get("trang_thai") or "") in (CHO_HOAN, DANG_HOAN))


def dien_giai_don(ma_don, ma_hien_thi=None, ten_khach=None):
	"""Câu diễn giải đi vào phiếu thu và phiếu chi.

	Chị Dung chốt điều 4: theo dõi 131 theo SỐ ĐƠN ghi trong diễn giải, vì
	đơn online đổ chung vào mã "Khách lẻ Online". Nên số đơn phải nằm trong
	câu này, không được để nó chỉ nằm ở một trường phụ nào đó.
	"""
	ma = str(ma_don or "").strip()
	hien = str(ma_hien_thi or "").strip()
	ten = str(ten_khach or "").strip()
	phan = ["Don %s" % (hien or ma)]
	if hien and ma and hien != ma:
		phan.append("(ID %s)" % ma)
	if ten:
		phan.append("- %s" % ten)
	return " ".join(phan)


def noi_dung_chuyen_khoan(ma_don, ma_hien_thi=None):
	"""Nội dung chuyển khoản lúc trả tiền lại, theo cú pháp chốt 16/08/2026.

	Dòng sao kê chỉ có một ô nội dung, và ba tháng sau đó là thứ duy nhất kế
	toán đọc được.
	"""
	ma = str(ma_hien_thi or ma_don or "").strip()
	return ("THE VAGABOND HOAN TIEN %s" % ma).strip()


def _ngay(v):
	"""Đọc ngày từ chuỗi hoặc từ đối tượng ngày giờ. Trả None nếu không đọc được.

	Tự phân tích bằng `datetime` chuẩn chứ KHÔNG gọi `frappe.utils`: hàm này
	là phép thuần, phải chạy được ở máy chạy CI nơi không có Frappe. Bản giả
	lập Frappe của bộ kiểm thử không có `get_datetime`, và ca kiểm đã đỏ
	đúng vì chuyện đó (21/08/2026).
	"""
	if not v:
		return None
	if hasattr(v, "date") and not isinstance(v, str):
		try:
			return v.date()
		except Exception:
			return None
	s = str(v).strip().replace("T", " ")[:10]
	try:
		return datetime.strptime(s, "%Y-%m-%d").date()
	except ValueError:
		return None


def qua_han_don_dep(huy_luc, hom_nay, ngay_giu=NGAY_GIU):
	"""Bản đệm này đã quá hạn giữ chưa. Chỉ tính NGÀY, không tính giờ.

	Tính theo ngày để câu trả lời không đổi tuỳ giờ chạy: một bản ghi không
	thể còn hạn lúc 9 giờ sáng rồi hết hạn lúc 5 giờ chiều cùng ngày.
	"""
	moc, nay = _ngay(huy_luc), _ngay(hom_nay)
	if not (moc and nay):
		return False
	return (nay - moc).days > int(ngay_giu or NGAY_GIU)


# ------------------------------------------------------- phần chạm hệ thống


def _quyen():
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()


def _shop():
	from vagabond.lib import cfg

	c = cfg()
	return c, (c.pancake_shop_id or "").strip()


def khoang_quet(so_ngay=NGAY_GIU, moc_cuoi=None):
	"""Khoảng thời gian quét Pancake, trả về UNIX GIÂY chứ không phải chuỗi.

	Pancake nhận startDateTime và endDateTime là UNIX giây. Truyền chuỗi ISO
	thì nó trả về DANH SÁCH RỖNG và không báo lỗi gì cả: HTTP vẫn 200, "data"
	vẫn có, chỉ là không có phần tử nào. Nhìn từ ngoài y hệt "shop không có
	đơn huỷ nào", nên rất khó ngờ.

	Đã ngã đúng chỗ này hai lần. Lần một ở kiem_banh, đã ghi cảnh báo ngay
	đầu tệp đó. Lần hai ở chính màn này ngày 21/08/2026: deploy v264 xong,
	dong_bo chạy sạch không lỗi, trả về quet 0 trong khi Pancake đang có ba
	đơn huỷ 92252, 92245, 92156 mà anh Việt chụp màn hình gửi sang.

	Tham số `moc_cuoi` chỉ để ca kiểm thử đóng cứng thời điểm, chạy thật thì
	để trống.
	"""
	from zoneinfo import ZoneInfo

	tz = ZoneInfo("Asia/Ho_Chi_Minh")
	cuoi = moc_cuoi or datetime.now(tz)
	if cuoi.tzinfo is None:
		cuoi = cuoi.replace(tzinfo=tz)
	dau = cuoi - timedelta(days=int(so_ngay or NGAY_GIU))
	return int(dau.timestamp()), int(cuoi.timestamp())


def _keo_don_huy(so_ngay=NGAY_GIU):
	"""Kéo đơn Pancake bị huỷ trong khoảng ngày, quét theo NGÀY CẬP NHẬT.

	Quét theo `updated_at` chứ không theo ngày giao là mấu chốt: đơn đặt hôm
	nay giao thứ Bảy mà huỷ chiều nay thì ngày giao còn nằm ở tương lai, quét
	theo ngày giao là không bao giờ thấy nó. Chính chỗ này làm luồng đồng bộ
	cũ bỏ sót toàn bộ đơn huỷ.
	"""
	import requests

	from vagabond.lib import PANCAKE, TIMEOUT, key

	c, shop = _shop()
	if not shop:
		frappe.throw("Chưa khai mã shop Pancake trong Vagabond Settings.")
	k = key(c, "pancake_api_key")
	if not k:
		frappe.throw("Chưa khai khoá API Pancake trong Vagabond Settings.")
	dau, cuoi = khoang_quet(so_ngay)
	ra = []
	for trang in range(1, 11):
		r = requests.get(
			"%s/shops/%s/orders" % (PANCAKE, shop),
			params={
				"api_key": k,
				"updateStatus": "updated_at",
				"startDateTime": dau,
				"endDateTime": cuoi,
				"page_size": 100,
				"page_number": trang,
			},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
		ds_trang = (r.json() or {}).get("data") or []
		ra.extend([o for o in ds_trang if la_don_huy(o)])
		if len(ds_trang) < 100:
			break
	return ra


def _doc_don(o):
	"""Lấy đúng các trường mình cần từ một đơn Pancake, không ôm cả cục."""
	ma = str(o.get("id") or "").strip()
	return {
		"ma_don": ma,
		"ma_hien_thi": str(o.get("system_id") or o.get("display_id") or ma).strip(),
		"ten_khach": (o.get("bill_full_name")
			or ((o.get("customer") or {}).get("name")) or "").strip(),
		"sdt": (o.get("bill_phone_number")
			or ((o.get("shipping_address") or {}).get("phone_number")) or "").strip(),
		"tong_don": flt(o.get("total_price")),
		"ngay_dat": (o.get("inserted_at") or "")[:19] or None,
		"ngay_giao": (o.get("estimate_delivery_date") or "")[:19] or None,
		"huy_luc": (o.get("updated_at") or o.get("inserted_at") or "")[:19] or None,
		"ghi_chu_don": (o.get("note") or o.get("note_print") or "")[:500],
	}


def _tt_ho_so(ho_so):
	if not ho_so:
		return None
	return frappe.db.get_value("Vagabond Hoan Tien", ho_so, "trang_thai")


@frappe.whitelist()
def dong_bo(so_ngay=NGAY_GIU):
	"""Kéo đơn huỷ từ Pancake về bảng đệm và dò tiền cho từng đơn.

	Chạy lại bao nhiêu lần cũng không đổi gì thêm: đơn đã có thì cập nhật,
	chưa có thì tạo. KHÔNG bao giờ đụng vào trạng thái của bản ghi mà người
	ta đã bấm Bỏ qua.
	"""
	_quyen()
	from vagabond.ban_hang import _sepay_theo_don

	dons = [_doc_don(o) for o in _keo_don_huy(so_ngay)]
	dons = [d for d in dons if d["ma_don"]]
	if not dons:
		return {"quet": 0, "moi": 0, "cap_nhat": 0, "don_dep": don_ban_dem()}

	_c, shop = _shop()
	# Dò cả hai đường: ID nội bộ và mã hiển thị, y như bảng doanh số làm.
	ma_tim = []
	for d in dons:
		ma_tim.append(d["ma_don"])
		if d["ma_hien_thi"] and d["ma_hien_thi"] != d["ma_don"]:
			ma_tim.append(d["ma_hien_thi"])
	tien = _sepay_theo_don(shop, ma_tim) or {}

	moi = cap_nhat = 0
	for d in dons:
		t = tien.get(d["ma_don"]) or tien.get((d["ma_hien_thi"] or "").upper()) or {}
		d["da_nhan"] = flt(t.get("nhan"))
		d["ma_gd"] = (t.get("ma") or "")[:140]
		ten = frappe.db.exists(DT, {"ma_don": d["ma_don"]})
		if ten:
			doc = frappe.get_doc(DT, ten)
			cu = (doc.trang_thai or "").strip()
			for khoa, gia_tri in d.items():
				doc.set(khoa, gia_tri)
			doc.dong_bo_luc = now_datetime()
			doc.trang_thai = trang_thai_don(
				doc.da_nhan, _tt_ho_so(doc.ho_so_hoan), 1 if cu == BO_QUA else 0)
			doc.save(ignore_permissions=True)
			cap_nhat += 1
		else:
			doc = frappe.new_doc(DT)
			doc.update(d)
			doc.dong_bo_luc = now_datetime()
			doc.trang_thai = trang_thai_don(d["da_nhan"])
			doc.insert(ignore_permissions=True)
			moi += 1
	return {
		"quet": len(dons), "moi": moi, "cap_nhat": cap_nhat,
		"don_dep": don_ban_dem(),
	}


def don_ban_dem(ngay_giu=NGAY_GIU):
	"""Dọn bản đệm quá hạn. CHỈ dọn đơn chưa hề phát sinh phiếu hoàn.

	Đơn đã có hồ sơ hoàn thì giữ vĩnh viễn: lúc đó bản ghi là một mắt xích
	tra cứu chứ không còn là bản sao đọc chơi, và QT-20 cấm xoá vết. Đơn còn
	Chờ hoàn hoặc Đang hoàn cũng không dọn dù quá hạn, vì tiền của khách vẫn
	đang nằm ở mình.
	"""
	moc = add_days(now_datetime(), -int(ngay_giu or NGAY_GIU))
	cac = frappe.get_all(DT, filters={
		"huy_luc": ["<", moc],
		"ho_so_hoan": ["in", ["", None]],
		"trang_thai": ["in", [KHONG_PHAI, BO_QUA]],
	}, pluck="name")
	for ten in cac:
		frappe.delete_doc(DT, ten, ignore_permissions=True, force=1)
	return len(cac)


@frappe.whitelist()
def ds(trang_thai="", tim="", so_dong=200):
	"""Danh sách đơn huỷ cho màn hình, kèm số đếm từng chip.

	Số đếm tính trên TOÀN BỘ bảng chứ không phải trên trang đang xem, để chip
	"Chờ hoàn 3" nói đúng số việc còn tồn.
	"""
	_quyen()
	loc = {}
	tt = (trang_thai or "").strip()
	if tt and tt in NHAN_TT:
		loc["trang_thai"] = tt
	truong = ["name", "ma_don", "ma_hien_thi", "ten_khach", "sdt", "tong_don",
		"da_nhan", "ngay_dat", "ngay_giao", "huy_luc", "trang_thai",
		"ho_so_hoan", "hoa_don", "ghi_chu_don", "ma_gd"]
	dong = frappe.get_all(DT, filters=loc, fields=truong,
		order_by="huy_luc desc", limit_page_length=int(so_dong or 200))
	q = (tim or "").strip().lower()
	if q:
		dong = [d for d in dong if q in " ".join(
			str(d.get(c) or "") for c in
			("ma_don", "ma_hien_thi", "ten_khach", "sdt")).lower()]
	tat_ca = frappe.get_all(DT, fields=["trang_thai", "da_nhan"],
		limit_page_length=0)
	for d in dong:
		d["nhan_trang_thai"] = NHAN_TT.get(d["trang_thai"], d["trang_thai"])
		d["muc_hoan"] = muc_hoan(d["da_nhan"])
	return {
		"dong": dong,
		"dem": dem_theo_chip(tat_ca),
		"tien_cho_hoan": tien_cho_hoan(tat_ca),
		"nhan": dict(NHAN_TT),
		"ngay_giu": NGAY_GIU,
	}


@frappe.whitelist()
def dem_cho_hoan():
	"""Số việc còn tồn, cho huy hiệu trên chip và mục Việc cần làm."""
	return frappe.db.count(DT, {"trang_thai": ["in", [CHO_HOAN, DANG_HOAN]]})


@frappe.whitelist()
def bo_qua(ma_don, ly_do=""):
	"""Đánh dấu một đơn không cần hoàn nữa. Huỷ mềm, giữ nguyên vết (QT-20)."""
	_quyen()
	ten = frappe.db.exists(DT, {"ma_don": str(ma_don or "").strip()})
	if not ten:
		frappe.throw("Không tìm thấy đơn %s trong danh sách đã huỷ." % ma_don)
	doc = frappe.get_doc(DT, ten)
	if doc.ho_so_hoan:
		frappe.throw("Đơn này đã có hồ sơ hoàn tiền %s, xử lý hồ sơ đó chứ "
			"không bỏ qua ở đây." % doc.ho_so_hoan)
	doc.trang_thai = BO_QUA
	# Ghi AI bỏ qua và VÌ SAO ngay trong ghi chú: ba tháng sau chỉ còn dòng
	# này trả lời được câu "sao đơn 750 nghìn này không ai hoàn".
	cu = (doc.ghi_chu_don or "").strip()
	doc.ghi_chu_don = ("%s [Bỏ qua %s bởi %s] %s" % (
		cu, str(now_datetime())[:16], frappe.session.user,
		(ly_do or "").strip())).strip()[:500]
	doc.save(ignore_permissions=True)
	return {"ma_don": doc.ma_don, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def xuat_excel(trang_thai="", tim=""):
	"""Xuất danh sách ra Excel cho kế toán đối chiếu."""
	_quyen()
	kq = ds(trang_thai=trang_thai, tim=tim, so_dong=2000)
	cot = [
		("ma_hien_thi", "Ma don"),
		("ma_don", "ID Pancake"),
		("ten_khach", "Khach hang"),
		("sdt", "So dien thoai"),
		("tong_don", "Tong tien don"),
		("da_nhan", "Khach da chuyen"),
		("muc_hoan", "Phai hoan"),
		("nhan_trang_thai", "Trang thai"),
		("ho_so_hoan", "Ho so hoan tien"),
		("ngay_dat", "Ngay dat"),
		("ngay_giao", "Ngay giao du kien"),
		("huy_luc", "Huy luc"),
		("ma_gd", "Ma giao dich"),
	]
	return {
		"ten_tep": "don-huy-cho-hoan-%s.csv" % str(now_datetime())[:10],
		"cot": [n for _f, n in cot],
		"hang": [[d.get(f) for f, _n in cot] for d in kq["dong"]],
		"tong_dong": len(kq["dong"]),
		"tien_cho_hoan": kq["tien_cho_hoan"],
	}


# --------------------------------------------- sinh chứng từ, đủ HAI CHÂN


def _cong_ty():
	return (frappe.defaults.get_user_default("Company")
		or frappe.db.get_value("Company", {"name": ["!=", ""]}, "name"))


def _khach_le_online():
	"""Mã khách dùng chung cho đơn online, chị Dung chốt điều 4.

	Không dựng mã riêng cho từng người: chị Dung chốt theo dõi 131 bằng SỐ
	ĐƠN ghi trong diễn giải. Nên chỗ này chỉ đi tìm đúng mã đang dùng, và
	nếu không thấy thì DỪNG chứ không tự tạo khách mới - tạo bừa một mã
	khách là đẻ ra một dòng công nợ không ai đối chiếu được.
	"""
	for ten in ("Khách lẻ Online", "Khach le Online"):
		if frappe.db.exists("Customer", ten):
			return ten
	ten = frappe.db.get_value("Customer", {"customer_name": ["like", "%lẻ Online%"]}, "name")
	if ten:
		return ten
	frappe.throw("Chưa tìm thấy mã khách \"Khách lẻ Online\" để treo khoản này. "
		"Nhờ kế toán kiểm lại danh mục khách rồi thử lại.")


def _tk_ngan_hang(cong_ty):
	from vagabond.hoan_tien import tk_chi

	tk = tk_chi(cong_ty)
	if not tk:
		frappe.throw("Chưa khai tài khoản ngân hàng của công ty trong Vagabond Settings.")
	tk_ke_toan = frappe.db.get_value("Bank Account", tk, "account")
	if not tk_ke_toan:
		frappe.throw("Tài khoản ngân hàng %s chưa gắn tài khoản kế toán." % tk)
	return tk_ke_toan


def _phieu(loai, khach, cong_ty, tk_ke_toan, so_tien, dien_giai, tham_chieu, ho_so):
	"""Dựng một Payment Entry ở dạng NHÁP. Không ghi sổ, có lý do.

	Chị Dung chốt 16/08/2026 và nhắc lại 21/08/2026 điều 3: chứng từ gốc hai
	chiều đều phải tải từ e-banking, giấy báo Có cho chiều vào và uỷ nhiệm
	chi cho chiều ra. Dòng SePay KHÔNG đủ. Nên máy điền sẵn mọi ô, còn nút
	ghi sổ nằm trong tay kế toán sau khi đính chứng từ.
	"""
	from frappe.utils import nowdate

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = loai
	pe.party_type = "Customer"
	pe.party = khach
	pe.company = cong_ty
	pe.posting_date = nowdate()
	if loai == "Receive":
		pe.paid_to = tk_ke_toan
	else:
		pe.paid_from = tk_ke_toan
	pe.paid_amount = flt(so_tien)
	pe.received_amount = flt(so_tien)
	pe.reference_no = tham_chieu
	pe.reference_date = nowdate()
	# Qua chung_tu_tien de ERPNext khong dung lai o Dien giai trong validate.
	from vagabond.chung_tu_tien import dat_dien_giai

	dat_dien_giai(pe, dien_giai)
	if ho_so:
		pe.vgb_hoan_tien = ho_so
	pe.flags.ignore_permissions = True
	pe.insert(ignore_permissions=True)
	return pe


@frappe.whitelist()
def xem_hoan(ma_don):
	"""Màn hỏi TRƯỚC khi mở form: đơn này hoàn được bao nhiêu, vì sao."""
	_quyen()
	ten = frappe.db.exists(DT, {"ma_don": str(ma_don or "").strip()})
	if not ten:
		frappe.throw("Chưa có đơn %s trong danh sách. Bấm Đồng bộ rồi thử lại."
			% ma_don)
	d = frappe.get_doc(DT, ten)
	cu = d.ho_so_hoan and frappe.db.get_value(
		"Vagabond Hoan Tien", d.ho_so_hoan,
		["name", "trang_thai", "so_tien"], as_dict=True)
	duoc = 1 if (flt(d.da_nhan) > 0 and not d.ho_so_hoan) else 0
	return {
		"ma_don": d.ma_don,
		"ma_hien_thi": d.ma_hien_thi,
		"ten_khach": d.ten_khach,
		"sdt": d.sdt,
		"tong_don": flt(d.tong_don),
		"da_nhan": flt(d.da_nhan),
		"muc_hoan": muc_hoan(d.da_nhan),
		"trang_thai": d.trang_thai,
		"duoc": duoc,
		"da_co": cu or None,
		"noi_dung_ck": noi_dung_chuyen_khoan(d.ma_don, d.ma_hien_thi),
		"vi_sao": (
			("Đơn này đã có hồ sơ %s đang ở trạng thái \"%s\"." % (
				cu["name"], cu["trang_thai"])) if cu
			else ("Chưa thấy đồng nào của đơn này về tài khoản công ty. Nếu khách "
			      "có chuyển thật thì đối chiếu sao kê rồi bấm Đồng bộ lại."
			      if flt(d.da_nhan) <= 0 else "")
		),
	}


@frappe.whitelist()
def tao_hoan(ma_don, so_tien=0, ly_do="", ten_tk="", so_tk="", ngan_hang="",
		sdt_khach="", dien_giai="", otp=None):
	"""Lập hồ sơ hoàn tiền cho một đơn Pancake CHƯA BAO GIỜ về ERPNext.

	Sinh đủ HAI CHÂN như chị Dung chốt 21/08/2026 điều 2:

	  1. Phiếu thu (Receive), Nợ 112 / Có 131, ghi nhận khoản khách đã chuyển
	     vào lúc đặt đơn. Không gán vào hoá đơn nào vì không có hoá đơn nào.
	  2. Phiếu chi (Pay), cùng khách cùng số tiền, trả lại khoản giữ hộ.

	Cả hai để NHÁP. Số dư 131 của mã "Khách lẻ Online" sau khi kế toán ghi
	cả hai phiếu sẽ về đúng như trước, và tra theo số đơn trong diễn giải
	thì thấy được cặp bút toán khớp nhau.

	KHÔNG ghi sổ hộ, KHÔNG xuất hoá đơn nào. Đơn này chưa từng có doanh thu
	nên không có gì để khử.
	"""
	_quyen()
	from vagabond.ban_hang import _otp_kiem
	from vagabond.hoan_tien import DT as HT
	from vagabond.hoan_tien import LOAI_HUY_PANCAKE

	ten = frappe.db.exists(DT, {"ma_don": str(ma_don or "").strip()})
	if not ten:
		frappe.throw("Chưa có đơn %s trong danh sách. Bấm Đồng bộ rồi thử lại."
			% ma_don)
	d = frappe.get_doc(DT, ten)
	if d.ho_so_hoan:
		frappe.throw("Đơn %s đã có hồ sơ hoàn tiền %s rồi." % (d.ma_don, d.ho_so_hoan))
	if flt(d.da_nhan) <= 0:
		frappe.throw("Chưa thấy tiền của đơn %s về tài khoản công ty. Không lập "
			"phiếu hoàn cho một khoản chưa vào." % d.ma_don)

	tien = flt(so_tien) or muc_hoan(d.da_nhan)
	if tien <= 0:
		frappe.throw("Số tiền hoàn phải lớn hơn 0.")
	if tien > flt(d.da_nhan) + 0.5:
		frappe.throw("Không hoàn quá số khách đã chuyển. Khách chuyển %s đ."
			% "{:,.0f}".format(flt(d.da_nhan)))
	tk = re.sub(r"[^0-9]", "", str(so_tk or ""))
	if not (tk and (ten_tk or "").strip() and (ngan_hang or "").strip()):
		frappe.throw("Còn thiếu thông tin tài khoản nhận tiền. Điền đủ tên ngân "
			"hàng, số tài khoản và tên chủ tài khoản của khách rồi gửi lại.")

	# Cùng một lớp khoá với luồng hoàn tiền đang chạy: tiền ra thật, và
	# người bấm ở đây thường là Sales chứ không phải kế toán. Sếp tự thao
	# tác thì khỏi nhập mã.
	cach = _otp_kiem(otp, "hoàn tiền đơn Pancake đã huỷ")

	cong_ty = _cong_ty()
	khach = _khach_le_online()
	tk_ke_toan = _tk_ngan_hang(cong_ty)
	mo_ta = dien_giai_don(d.ma_don, d.ma_hien_thi, d.ten_khach)
	noi_dung = noi_dung_chuyen_khoan(d.ma_don, d.ma_hien_thi)
	ghi = ("[Huỷ đơn Pancake] %s. %s %s" % (
		mo_ta, (ly_do or "").strip(), (dien_giai or "").strip())).strip()

	ho_so = frappe.get_doc({
		"doctype": HT,
		"ma_don_pancake": d.ma_don,
		"khach": khach,
		"so_tien": tien,
		"loai_hoan": LOAI_HUY_PANCAKE,
		"ly_do": "Khac",
		"dien_giai": ghi,
		"trang_thai": "Cho chi",
		"ten_tk": (ten_tk or "").strip(),
		"so_tk": tk,
		"ngan_hang": (ngan_hang or "").strip() or None,
		"sdt": (sdt_khach or "").strip(),
		"nguoi_duyet": frappe.session.user,
		"cach_duyet": "Gui duyet tu man Don da huy (Pancake), duyet bang %s" % cach,
		"noi_dung_ck": noi_dung,
	})
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	# CHÂN MỘT: khoản khách đã chuyển vào. Ghi nhận trước, vì nếu chỉ lập
	# phiếu chi thì TK 131 của mã Khách lẻ Online dư Nợ, trông như khách còn
	# nợ mình đúng bằng số vừa trả.
	thu = _phieu("Receive", khach, cong_ty, tk_ke_toan, flt(d.da_nhan),
		"Khách chuyển trước cho %s. Đơn đã huỷ, chưa từng ghi doanh thu nên "
		"khoản này là tiền công ty giữ hộ, KHÔNG phải doanh thu. Chứng từ gốc: "
		"giấy báo Có tải từ e-banking." % mo_ta,
		(d.ma_gd or "").strip() or noi_dung, ho_so.name)

	# CHÂN HAI: trả lại.
	chi = _phieu("Pay", khach, cong_ty, tk_ke_toan, tien,
		"Trả lại tiền khách đã chuyển cho %s theo hồ sơ %s. Đơn huỷ trước khi "
		"về hệ nên KHÔNG có hoá đơn, KHÔNG có hoá đơn trả hàng, KHÔNG có hoá "
		"đơn điện tử. Nội dung chuyển khoản: %s. Chứng từ gốc: uỷ nhiệm chi "
		"tải từ e-banking." % (mo_ta, ho_so.name, noi_dung),
		noi_dung, ho_so.name)

	d.ho_so_hoan = ho_so.name
	d.trang_thai = DANG_HOAN
	d.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"so_tien": tien,
		"da_nhan": flt(d.da_nhan),
		"phieu_thu": thu.name if thu else None,
		"phieu_chi": chi.name if chi else None,
		"noi_dung_ck": noi_dung,
		"khach": khach,
		"nhac": ("Hai phiếu đang ở dạng NHÁP. Kế toán đính giấy báo Có và uỷ "
			"nhiệm chi tải từ e-banking rồi mới ghi sổ."),
	}

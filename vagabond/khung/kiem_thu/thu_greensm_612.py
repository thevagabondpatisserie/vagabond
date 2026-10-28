# -*- coding: utf-8 -*-
"""v612 (anh Việt 26/10/2026): nối GreenSM thật theo tài liệu công khai, đổi
nguồn phí giao trên web từ Ahamove sang GreenSM.

Gốc chuyện: hôm 21/10 sandbox GreenSM trả 400 vì mình gửi `pickup`/`dropoff`
số ít khi tài liệu chưa có. Đo lại 26/10 trên site với thân đúng tài liệu:
danh sách xe, báo giá, tạo đơn, xem đơn đều 200.

Bốn đường lỗi bộ ca này chặn:
  1. Thân yêu cầu sai hình (add-on thu hộ ở điểm giao phải là object, add-on
     của dịch vụ là mảng có `apply`; tạo đơn chỉ nhận mảng mã `addon_ids`).
  2. Giá môi trường thử (giá giả, mọi địa chỉ một giá) lọt ra trang đặt bánh.
  3. Gọi xe môi trường thử cho một vận đơn thật: vận đơn báo Đang giao mà
     không có tài xế nào.
  4. Tạo đơn bằng order_time, loại xe hay add-on khác lúc báo giá: GreenSM từ
     chối fee_id. Nên tạo đơn từ CHÍNH bản giá máy chủ đã giữ.

giao_hang nạp `requests` và dia_chi TRONG hàm (v612), nên ca này import
được trên máy CI tay không mà không cần requests giả. dia_chi (kéo requests
ở đầu tệp) được thay bằng mô đun giả chỉ có geocode trong ca gọi xe.
"""

import copy
import json
import sys
import types

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la

# Phản hồi thật đo trên sandbox ngày 26/10/2026 (rút gọn trường không dùng).
DICH_VU_THAT = {"data": [
	{"service": {"id": 2099, "display_name": "Van Express", "travel_mode": "Truck", "service_type": "EXPRESS-ONDEMAND",
		"enable": True}, "addons": []},
	{"service": {"id": 1878, "display_name": "Express for partner", "travel_mode": "Motorcycle",
		"service_type": "EXPRESS-ONDEMAND", "enable": True},
		"addons": [{"id": 10, "name": "Giao hàng tận tay"}, {"id": 4, "name": "COD"}, {"id": 13, "name": "Thu hộ COD"}]},
]}


def _gia(service_id=1878, tong=80000, fee="12a3a25c-79e3-4b91-8f37-9dd617070619", het_han=1793010956, km=5.33):
	return {"data": {"service_estimates": [{
		"fee_unavailable": False, "err_msg": "",
		"service": {"id": service_id, "display_name": "Express for partner", "service_type": "EXPRESS-ONDEMAND"},
		"estimate_info": {"fee_id": fee, "expires_at": het_han, "increase_price": False,
			"estimate": {"total_fee": tong, "total_pay": tong,
				"fee_breakdown": {"base_fee": 70000, "addons_fee": 10000, "discount": 0}},
			"trip": {"distance_estimate": km, "duration_estimate": 702}},
	}]}}


def _gsm():
	from vagabond import greensm

	return greensm


# ------------------------------------------------------------------ phần thuần


@ca("v612 GreenSM: số điện thoại về đúng dạng +84 mà GreenSM đòi")
def _():
	g = _gsm()
	la("0 đầu", g.so_quoc_te("0964 131 194"), "+84964131194")
	la("84 đầu", g.so_quoc_te("84964131194"), "+84964131194")
	la("đã có +84", g.so_quoc_te("+84964131194"), "+84964131194")
	la("rác", g.so_quoc_te("abc"), "")
	la("trống", g.so_quoc_te(None), "")


@ca("v612 GreenSM: thân báo giá đúng hình tài liệu, thu hộ gắn đúng hai chỗ")
def _():
	g = _gsm()
	lay = g.diem("PICK UP", 10.7975, 106.6712, "The Vagabond", "84964131194", "307/1 NVT", ghi_chu="Mã đơn X", hang=True)
	giao = g.diem("DROP OFF", 10.80, 106.71, "Khách", "0900000000", "208 NHC")
	t = g.than_bao_gia(1878, 1793007457, lay, giao, [10], 250000)
	la("một dịch vụ", [d["id"] for d in t["service_ids"]], [1878])
	add = t["service_ids"][0]["addons"]
	la("add-on có apply", [(a["id"], a["apply"]) for a in add], [(10, True), (4, True)])
	cod = [a for a in add if a["id"] == g.ADDON_COD][0]
	la("thu hộ: remain_cod và value 1", (cod["remain_cod"], cod["value"]), (250000, 1))
	la("điểm giao: addons là OBJECT", t["points"][1]["addons"], {"collect_cod": 250000, "currency_code": "VND"})
	dung("điểm lấy không mang addons", "addons" not in t["points"][0])
	la("điểm lấy có hàng", (t["points"][0]["package_size"], t["points"][0]["package_weight"], t["points"][0]["package_types"]),
		("SMALL", 2, ["food"]))
	dung("điểm giao không mang cân nặng", "package_weight" not in t["points"][1])
	la("loại điểm", [p["type"] for p in t["points"]], ["PICK UP", "DROP OFF"])
	la("số điện thoại quốc tế", t["points"][1]["phone_number"], "+84900000000")
	la("order_time giữ nguyên", t["order_time"], 1793007457)
	la("tiệm trả cước", t["payment_method"], "partner_pay")
	# Không thu hộ thì không có add-on 4 và không có object ở điểm giao.
	t2 = g.than_bao_gia(1878, 0, lay, giao, [], 0)
	dung("không thu hộ: không có khoá addons", "addons" not in t2["service_ids"][0])
	dung("không thu hộ: điểm giao không có addons", "addons" not in t2["points"][1])
	# Trình duyệt gửi lẻn mã 4 vào add-on: không được nhân đôi hay thu hộ 0đ.
	t3 = g.than_bao_gia(1878, 0, lay, giao, [4, "10"], 0)
	la("mã 4 từ trình duyệt bị bỏ", [a["id"] for a in t3["service_ids"][0]["addons"]], [10])


@ca("v612 GreenSM: đọc báo giá đúng số, dịch vụ không báo được thì có lời giải thích")
def _():
	g = _gsm()
	bg = g.doc_bao_gia(_gia(), 1878)
	la("tổng", bg["tong"], 80000)
	la("fee_id", bg["fee_id"], "12a3a25c-79e3-4b91-8f37-9dd617070619")
	la("km và phút", (bg["km"], bg["phut"]), (5.33, 11))
	la("phí add-on", bg["phi_them"], 10000)
	la("loại dịch vụ", bg["service_type"], "EXPRESS-ONDEMAND")
	ko = _gia()
	ko["data"]["service_estimates"][0]["fee_unavailable"] = True
	ko["data"]["service_estimates"][0]["err_msg"] = "Ngoài giờ phục vụ"
	la("không báo giá được", g.doc_bao_gia(ko, 1878), {"loi": "Ngoài giờ phục vụ"})
	dung("sai mã dịch vụ", "loi" in g.doc_bao_gia(_gia(), 2099))
	dung("phản hồi rỗng", "loi" in g.doc_bao_gia({}, None))
	khong_so = _gia(tong=0)
	dung("tổng 0 không bao giờ thành giá", "loi" in g.doc_bao_gia(khong_so, 1878))


@ca("v612 GreenSM: thân tạo đơn lấy lại y hệt order_time, điểm và add-on của lúc báo giá")
def _():
	g = _gsm()
	lay = g.diem("PICK UP", 10.7975, 106.6712, "The Vagabond", "84964131194", "307/1 NVT", hang=True)
	giao = g.diem("DROP OFF", 10.80, 106.71, "Khách", "0900000000", "208 NHC")
	than = g.than_bao_gia(1878, 1793007457, lay, giao, [10], 150000)
	goc = copy.deepcopy(than)
	bg = g.doc_bao_gia(_gia(), 1878)
	d = g.than_tao_don(bg, than, "VD-2026-00123-mot-ma-rat-dai-qua-32-ky-tu", 450000)
	la("order_time", d["order_time"], 1793007457)
	la("fee_id", d["fee_id"], bg["fee_id"])
	la("service_id và loại", (d["service_id"], d["service_type"]), (1878, "EXPRESS-ONDEMAND"))
	la("addon_ids là mảng số ở cấp ngoài", d["addon_ids"], [10, 4])
	dung("không có service_ids ở thân tạo đơn", "service_ids" not in d)
	la("thu hộ ở điểm giao giữ nguyên", d["points"][1]["addons"]["collect_cod"], 150000)
	la("người trả cước đánh dấu ở điểm lấy", [p["is_payment_check_point"] for p in d["points"]], [True, False])
	la("mã nội bộ tối đa 32 ký tự", len(d["partner_trip_id"]), 32)
	la("giá trị hàng", d["goods_value"], 450000)
	la("không sửa vào thân đã giữ", than, goc)


@ca("v612 GreenSM: loại xe máy lên đầu, add-on thu hộ ẩn khỏi màn tick")
def _():
	g = _gsm()
	ds = g.dich_vu_gon(DICH_VU_THAT)
	la("xe máy đứng đầu", [d["id"] for d in ds], [1878, 2099])
	la("chỉ còn Giao hàng tận tay", ds[0]["addon"], [{"id": 10, "ten": "Giao hàng tận tay"}])
	tat = copy.deepcopy(DICH_VU_THAT)
	tat["data"][1]["service"]["enable"] = False
	la("dịch vụ đang tắt bị bỏ", [d["id"] for d in g.dich_vu_gon(tat)], [2099])


@ca("v612 GreenSM: lỗi ghi nhật ký không lộ token hay client_secret")
def _():
	g = _gsm()
	s = g.che_loi('{"access_token":"eyJabc.def","client_secret":"sb_xyz"} Authorization: Bearer eyJ123')
	dung("không còn token", "eyJabc" not in s and "eyJ123" not in s)
	dung("không còn secret", "sb_xyz" not in s)


# ---------------------------------------------------------- phần chạm hệ (giả)


class _Mang(object):
	"""Thay greensm.goi: ghi lại mọi lần gọi, trả phản hồi đã soạn."""

	def __init__(self, gia=None):
		self.goi = []
		self.gia = gia or _gia()

	def __call__(self, c, duong_dan, body=None, phuong_thuc="POST"):
		self.goi.append((duong_dan, copy.deepcopy(body)))
		if duong_dan == "/list-available-services":
			return copy.deepcopy(DICH_VU_THAT)
		if duong_dan == "/estimate/order":
			return copy.deepcopy(self.gia)
		if duong_dan == "/create-order":
			return {"data": {"id": "01M5V144E998PACHGYWE3J09JP", "status": "FINDING",
				"tracking_url": "https://tracking.gsm/01M5V1"}}
		raise AssertionError("gọi lạ " + duong_dan)


class _Bo(object):
	"""Cài tạm cache dict và các hàm vá; gỡ sạch khi ra. Không cài requests
	giả: giao_hang và greensm nạp requests trong hàm, mọi đường gọi mạng ở
	đây đều đi qua greensm.goi đã thay."""

	def __init__(self):
		self.cache = {}
		self.va = []
		self.mod = {}

	def dat(self, obj, ten, gia_tri):
		self.va.append((obj, ten, getattr(obj, ten)))
		setattr(obj, ten, gia_tri)

	def mo_dun(self, ten, m):
		self.mod[ten] = sys.modules.get(ten)
		sys.modules[ten] = m

	def __enter__(self):
		from vagabond import lib

		rl = types.ModuleType("frappe.rate_limiter")
		rl.rate_limit = lambda **k: (lambda f: f)
		self.mo_dun("frappe.rate_limiter", rl)
		self.dat(lib, "cache_get", lambda k: self.cache.get(k))
		self.dat(lib, "cache_set", lambda k, v, ttl: self.cache.__setitem__(k, v))
		self.dat(lib, "key", lambda doc, f: str(doc.get(f) or "").strip())
		return self

	def __exit__(self, *a):
		for obj, ten, cu in reversed(self.va):
			setattr(obj, ten, cu)
		for ten, cu in self.mod.items():
			if cu is None:
				sys.modules.pop(ten, None)
			else:
				sys.modules[ten] = cu


def _cfg(**k):
	c = Doi({
		"greensm_client_id": "sb_id", "greensm_client_secret": "bi-mat", "greensm_token_url": "https://x/token",
		"greensm_sandbox": 0, "ahamove_mobile": "84964131194", "phu_thu": 20000,
		"kitchen_lat": 10.7975, "kitchen_lng": 106.6712, "kitchen_address": "307/1 Nguyễn Văn Trỗi",
		"store_lat": 10.7869, "store_lng": 106.6993, "store_address": "9 Trần Cao Vân",
		"ban_kinh_giao_km": 12, "nguon_phi_giao_web": "GreenSM",
		"ahamove_api_key": "aha", "ahamove_base": "https://partner-api.ahamove.com",
	})
	c.update(k)
	return c


def _web(bo, c, mang, lat=10.8019, lng=106.7124, luc_giao=None):
	from vagabond import greensm

	import vagabond.giao_hang as gh

	bo.dat(gh, "cfg", lambda: c)
	bo.dat(gh, "key", lambda doc, f: str(doc.get(f) or "").strip())
	bo.dat(gh, "cache_get", lambda k: None)
	bo.dat(gh, "cache_set", lambda k, v, ttl: None)
	bo.dat(greensm, "goi", mang)
	aha = []
	bo.dat(gh, "_hoi_ahamove", lambda *a: (aha.append(a), ({"total_fee": 41000, "distance": 6.8}, None))[1])
	kq = gh.phi_giao(addr="208 Nguyễn Hữu Cảnh", lat=lat, lng=lng, luc_giao=luc_giao)
	return kq, aha


@ca("v612 web: GreenSM thật báo phí cộng phụ thu, hỏi từ điểm lấy gần khách nhất")
def _():
	with _Bo() as bo:
		mang = _Mang()
		kq, aha = _web(bo, _cfg(), mang)
	la("báo được", kq["ok"], 1)
	la("phí gốc GreenSM", kq["phi_goc"], 80000)
	la("cộng phụ thu tiệm", kq["total_fee"], 100000)
	la("nguồn", kq["nguon"], "GreenSM")
	la("không hỏi Ahamove", aha, [])
	bao = [b for d, b in mang.goi if d == "/estimate/order"][0]
	# Khách ở Bình Thạnh: cửa hàng Trần Cao Vân gần hơn bếp Nguyễn Văn Trỗi.
	la("điểm lấy là cửa hàng", (bao["points"][0]["latitude"], bao["points"][0]["longitude"]), (10.7869, 106.6993))
	la("điểm giao là khách", (bao["points"][1]["latitude"], bao["points"][1]["longitude"]), (10.8019, 106.7124))
	la("xe máy", bao["service_ids"][0]["id"], 1878)


@ca("v612 web: GreenSM đang chạy thử thì KHÔNG đưa giá giả cho khách, không gọi mạng")
def _():
	with _Bo() as bo:
		mang = _Mang()
		kq, aha = _web(bo, _cfg(greensm_sandbox=1), mang)
	la("không báo số", kq, {"ok": 0, "ly_do": "greensm_dang_chay_thu"})
	la("không gọi GreenSM", mang.goi, [])
	la("không lùi về Ahamove", aha, [])


@ca("v612 web: thiếu khoá GreenSM thì nói rõ, ô nguồn trống coi như GreenSM, chọn Ahamove thì hỏi Ahamove")
def _():
	with _Bo() as bo:
		kq, _a = _web(bo, _cfg(greensm_client_secret=""), _Mang())
	la("thiếu khoá", kq, {"ok": 0, "ly_do": "chua_dien_khoa_greensm"})
	with _Bo() as bo:
		mang = _Mang()
		kq, aha = _web(bo, _cfg(nguon_phi_giao_web=None), mang)
	la("ô trống: GreenSM", (kq["nguon"], kq["phi_goc"], aha), ("GreenSM", 80000, []))
	with _Bo() as bo:
		mang = _Mang()
		kq, aha = _web(bo, _cfg(nguon_phi_giao_web="Ahamove", greensm_sandbox=1), mang)
	la("chọn Ahamove: phí Ahamove", (kq["nguon"], kq["phi_goc"]), ("Ahamove", 41000))
	la("chọn Ahamove: không gọi GreenSM", mang.goi, [])
	la("chọn Ahamove: hỏi Ahamove một lần", len(aha), 1)


@ca("v612 web: ngoài vùng giao vẫn chặn trước khi gọi GreenSM")
def _():
	with _Bo() as bo:
		mang = _Mang()
		kq, _a = _web(bo, _cfg(), mang, lat=11.20, lng=106.70)
	la("ngoài vùng", kq["ly_do"], "ngoai_vung_giao")
	la("không tốn lượt gọi", mang.goi, [])


@ca("v612 web: GreenSM lỗi thì không đoán số, Error Log chỉ ghi một lần mỗi ngày")
def _():
	from vagabond import greensm
	import frappe

	def hong(*a, **k):
		raise greensm.LoiGsm("GreenSM trả mã 500: lỗi")

	ghi = []
	with _Bo() as bo:
		bo.dat(frappe, "log_error", lambda *a, **k: ghi.append(k.get("title")))
		kq1, _a = _web(bo, _cfg(), hong)
		kq2, _a = _web(bo, _cfg(), hong)
	la("không có số", (kq1["ok"], kq1["ly_do"]), (0, "greensm_loi"))
	la("lần hai cũng không có số", kq2["ok"], 0)
	la("ghi nhật ký một lần", ghi, ["Vagabond: GreenSM không báo phí web"])


def _vd(bo, c, mang, doc):
	from vagabond import greensm, van_don
	import frappe

	dc = types.ModuleType("vagabond.dia_chi")
	dc.geocode = lambda c, addr: {"lat": 10.8019, "lng": 106.7124}
	bo.mo_dun("vagabond.dia_chi", dc)
	bo.dat(van_don, "cfg", lambda: c)
	bo.dat(van_don, "_la_sales", lambda: True)
	bo.dat(van_don, "cache_get", lambda k: bo.cache.get(k))
	bo.dat(van_don, "cache_set", lambda k, v, ttl: bo.cache.__setitem__(k, v))
	bo.dat(van_don.time, "time", lambda: 1793007000)
	bo.dat(frappe, "get_doc", lambda *a, **k: doc)
	bo.dat(greensm, "goi", mang)
	return van_don


def _don():
	d = Doi({"name": "VD-2026-00123", "ma_don": "91500", "khach": "Chị Lan", "sdt": "0901234567",
		"dia_chi": "208 Nguyễn Hữu Cảnh", "tien_thu_ho": 0, "gio_giao": "14h - 16h", "diem_pickup": None,
		"booking_id": None})
	return d


@ca("v612 gọi xe: Xem giá giữ bản giá ở máy chủ, Gọi xe tạo đơn từ chính bản đó")
def _():
	with _Bo() as bo:
		mang = _Mang()
		vd = _vd(bo, _cfg(), mang, _don())
		gia = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[10]")
		la("giá trả về màn", (gia["tong"], gia["dang_thu"]), (80000, False))
		oid, link, phi = vd._greensm_dat_don(_don(), "1878", [10], gia["ma_gia"])
		bao = [b for d, b in mang.goi if d == "/estimate/order"][0]
		tao = [b for d, b in mang.goi if d == "/create-order"][0]
		la("mã đơn GreenSM", oid, "01M5V144E998PACHGYWE3J09JP")
		la("link theo dõi", link, "https://tracking.gsm/01M5V1")
		la("phí ghi vào vận đơn", phi, 80000)
		la("order_time y hệt lúc báo giá", tao["order_time"], bao["order_time"])
		la("fee_id của bản giá", tao["fee_id"], "12a3a25c-79e3-4b91-8f37-9dd617070619")
		la("add-on y hệt", tao["addon_ids"], [10])
		la("điểm y hệt", [(p["latitude"], p["longitude"]) for p in tao["points"]],
			[(p["latitude"], p["longitude"]) for p in bao["points"]])
		la("người nhận là khách", (tao["points"][1]["name"], tao["points"][1]["phone_number"]), ("Chị Lan", "+84901234567"))
		la("mã nội bộ là vận đơn", tao["partner_trip_id"], "VD-2026-00123")
		dung("gọi xong thì bỏ bản giá, không gọi trùng", not bo.cache.get("vgb:gsm:gia:VD-2026-00123"))


@ca("v612 gọi xe: môi trường thử không bao giờ gọi xe cho vận đơn thật")
def _():
	import frappe

	with _Bo() as bo:
		mang = _Mang()
		vd = _vd(bo, _cfg(greensm_sandbox=1), mang, _don())
		gia = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		la("xem giá thử vẫn được, có cờ thử", gia["dang_thu"], True)
		try:
			vd._greensm_dat_don(_don(), "1878", [], gia["ma_gia"])
			bi_chan = False
		except frappe.ValidationError as e:
			bi_chan = "môi trường thử" in str(e)
	dung("bị chặn và nói rõ vì sao", bi_chan)
	la("không có lần tạo đơn nào", [d for d, b in mang.goi if d == "/create-order"], [])


@ca("v612 gọi xe: đổi xe, đổi add-on hoặc giá hết hạn thì bắt xem giá lại")
def _():
	import frappe

	def thu(f):
		try:
			f()
			return ""
		except frappe.ValidationError as e:
			return str(e)

	with _Bo() as bo:
		mang = _Mang()
		vd = _vd(bo, _cfg(), mang, _don())
		la("chưa xem giá", "hết hạn" in thu(lambda: vd._greensm_dat_don(_don(), "1878", [], "fee-cu")), True)
		gia = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[10]")
		la("bỏ add-on sau khi xem giá", "Loại xe hoặc dịch vụ thêm đã đổi" in thu(lambda: vd._greensm_dat_don(_don(), "1878", [], gia["ma_gia"])), True)
		la("đổi loại xe", "Loại xe hoặc dịch vụ thêm đã đổi" in thu(lambda: vd._greensm_dat_don(_don(), "2099", [10], gia["ma_gia"])), True)
	la("không tạo đơn nào", [d for d, b in mang.goi if d == "/create-order"], [])


@ca("v612 gọi xe: đơn có thu hộ thì GreenSM thu đúng số đó, đơn lấy tại quầy thì người nhận là quầy")
def _():
	with _Bo() as bo:
		mang = _Mang()
		d = _don()
		d["tien_thu_ho"] = 650000
		vd = _vd(bo, _cfg(), mang, d)
		gia = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		vd._greensm_dat_don(d, "1878", [], gia["ma_gia"])
		bao = [b for x, b in mang.goi if x == "/estimate/order"][0]
		tao = [b for x, b in mang.goi if x == "/create-order"][0]
	la("báo giá: remain_cod", [a.get("remain_cod") for a in bao["service_ids"][0]["addons"]], [650000])
	la("tạo đơn: addon_ids có mã thu hộ", tao["addon_ids"], [4])
	la("tạo đơn: collect_cod khớp", tao["points"][1]["addons"]["collect_cod"], 650000)
	# Đơn lấy tại quầy: _noi_giao trả quầy, thu hộ 0, số quầy.
	with _Bo() as bo:
		mang = _Mang()
		from vagabond import van_don

		bo.dat(van_don, "_noi_giao", lambda doc: {"dia_chi": "9 Trần Cao Vân", "ten": "The Vagabond TCV",
			"sdt": "84964131194", "cod": 0.0, "toi_diem": 1})
		d = _don()
		d["tien_thu_ho"] = 650000
		vd = _vd(bo, _cfg(), mang, d)
		vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		bao = [b for x, b in mang.goi if x == "/estimate/order"][0]
	la("quầy: người nhận", bao["points"][1]["name"], "The Vagabond TCV")
	dung("quầy: không thu hộ", "addons" not in bao["service_ids"][0])


@ca("v616 gọi xe (Codex #499 4373739954): đổi địa chỉ, tiền thu hộ, người nhận hoặc điểm khách lấy sau khi xem giá thì bắt xem giá lại")
def _():
	# Đúng chuỗi Codex mô tả: Xem giá với COD 650.000đ, đồng bộ Pancake đổi
	# vận đơn sang COD 0 và địa chỉ mới, rồi bấm Gọi xe. Không gọi thêm hàm
	# nào giữa hai bước (điều 18 bài học).
	import frappe

	def thu(f):
		try:
			f()
			return ""
		except frappe.ValidationError as e:
			return str(e)

	def doi(**k):
		d = _don()
		d["tien_thu_ho"] = 650000
		d.update(k)
		return d

	for ten, moi in (
		("đổi COD và địa chỉ", {"tien_thu_ho": 0, "dia_chi": "12 Lê Lợi, Quận 1"}),
		("chỉ đổi COD", {"tien_thu_ho": 0}),
		("chỉ đổi địa chỉ", {"dia_chi": "12 Lê Lợi, Quận 1"}),
		("đổi số người nhận", {"sdt": "0912000111"}),
	):
		with _Bo() as bo:
			mang = _Mang()
			d = doi()
			vd = _vd(bo, _cfg(), mang, d)
			gia = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
			loi = thu(lambda: vd._greensm_dat_don(doi(**moi), "1878", [], gia["ma_gia"]))
			la(ten + ": bắt xem giá lại", "Xem giá lại" in loi, True)
			la(ten + ": không tạo đơn", [x for x, b in mang.goi if x == "/create-order"], [])
			dung(ten + ": bỏ bản giá cũ", not bo.cache.get("vgb:gsm:gia:VD-2026-00123"))
	# Gán shipper chuyển sang khách lấy tại quầy sau khi xem giá.
	with _Bo() as bo:
		mang = _Mang()
		from vagabond import van_don

		vd = _vd(bo, _cfg(), mang, doi())
		gia = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		bo.dat(van_don, "_noi_giao", lambda doc: {"dia_chi": "9 Trần Cao Vân", "ten": "The Vagabond TCV",
			"sdt": "84964131194", "cod": 0.0, "toi_diem": 1})
		loi = thu(lambda: vd._greensm_dat_don(doi(), "1878", [], gia["ma_gia"]))
	la("đổi sang lấy tại quầy: bắt xem giá lại", "Xem giá lại" in loi, True)
	la("đổi sang lấy tại quầy: không tạo đơn", [x for x, b in mang.goi if x == "/create-order"], [])
	# Không đổi gì thì vẫn gọi được, giữ COD đúng.
	with _Bo() as bo:
		mang = _Mang()
		vd = _vd(bo, _cfg(), mang, doi())
		gia = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		oid, _l, _p = vd._greensm_dat_don(doi(), "1878", [], gia["ma_gia"])
		tao = [b for x, b in mang.goi if x == "/create-order"][0]
	la("không đổi: gọi được", oid, "01M5V144E998PACHGYWE3J09JP")
	la("không đổi: COD giữ nguyên", tao["points"][1]["addons"]["collect_cod"], 650000)


@ca("v616 gọi xe (Codex #499 4395850127): hai màn cùng Xem giá, màn đầu bấm Gọi xe thì bắt xem lại, không đặt theo cước của màn sau")
def _():
	# Đúng chuỗi Codex mô tả: lần đầu 80.000đ mã fee-A, lần sau (màn khác)
	# 123.000đ mã fee-B, rồi bấm Gọi xe ở màn đầu (gửi mã fee-A nó đang hiện).
	import frappe

	def thu(f):
		try:
			f()
			return ""
		except frappe.ValidationError as e:
			return str(e)

	with _Bo() as bo:
		mang = _Mang(gia=_gia(tong=80000, fee="fee-A"))
		vd = _vd(bo, _cfg(), mang, _don())
		g1 = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		mang.gia = _gia(tong=123000, fee="fee-B")
		g2 = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		la("màn nhận mã bản giá", (g1["ma_gia"], g2["ma_gia"]), ("fee-A", "fee-B"))
		loi = thu(lambda: vd._greensm_dat_don(_don(), "1878", [], g1["ma_gia"]))
		la("màn đầu: bắt xem giá lại", "Xem giá lại" in loi, True)
		la("màn đầu: không tạo đơn", [x for x, b in mang.goi if x == "/create-order"], [])
		dung("màn đầu: KHÔNG xoá bản giá của màn sau", bool(bo.cache.get("vgb:gsm:gia:VD-2026-00123")))
		la("thiếu mã bản giá (app cũ): cũng bắt xem lại", "Xem giá lại" in thu(lambda: vd._greensm_dat_don(_don(), "1878", [])), True)
		oid, _l, phi = vd._greensm_dat_don(_don(), "1878", [], g2["ma_gia"])
		tao = [b for x, b in mang.goi if x == "/create-order"][0]
	la("màn sau gọi được", oid, "01M5V144E998PACHGYWE3J09JP")
	la("đặt đúng bản giá màn sau đã thấy", (tao["fee_id"], phi), ("fee-B", 123000))

	# Đi qua đúng cửa app gọi (book_xe): mã bản giá phải được chuyển tới chỗ so.
	class _Vd(Doi):
		flags = Doi()

		def save(self):
			self["_da_luu"] = 1

	with _Bo() as bo:
		mang = _Mang(gia=_gia(tong=80000, fee="fee-A"))
		d = _Vd(_don())
		vd = _vd(bo, _cfg(), mang, d)
		g1 = vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		mang.gia = _gia(tong=123000, fee="fee-B")
		vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
		loi = thu(lambda: vd.book_xe("VD-2026-00123", "GreenSM", service_id="1878", requests_them="[]", ma_gia=g1["ma_gia"]))
		la("book_xe màn đầu: bắt xem lại", "Xem giá lại" in loi, True)
		la("book_xe màn đầu: không tạo đơn, không lưu vận đơn", ([x for x, b in mang.goi if x == "/create-order"], d.get("_da_luu")), ([], None))
		kq = vd.book_xe("VD-2026-00123", "GreenSM", service_id="1878", requests_them="[]", ma_gia="fee-B")
	la("book_xe màn sau: đặt và ghi phí đúng", (kq["phi_giao"], d.get("_da_luu")), (123000, 1))


@ca("v616 phép thuần: dấu dữ liệu giao bỏ khoảng trắng thừa, số COD viết khác vẫn là một")
def _():
	from vagabond import greensm

	a = greensm.dau_giao({"dia_chi": "208  Nguyễn Hữu Cảnh ", "ten": "Chị Lan", "sdt": "0901234567", "cod": 650000},
		{"dia_chi": "307/1 Nguyễn Văn Trỗi", "lat": 10.7975, "lng": 106.6712})
	b = greensm.dau_giao({"dia_chi": "208 Nguyễn Hữu Cảnh", "ten": "Chị Lan", "sdt": "0901234567", "cod": "650000.0"},
		{"dia_chi": "307/1 Nguyễn Văn Trỗi", "lat": 10.7975, "lng": 106.6712})
	la("giống nhau", a, b)
	c = greensm.dau_giao({"dia_chi": "208 Nguyễn Hữu Cảnh", "ten": "Chị Lan", "sdt": "0901234567", "cod": 0},
		{"dia_chi": "307/1 Nguyễn Văn Trỗi", "lat": 10.7975, "lng": 106.6712})
	dung("COD khác thì khác", a != c)
	d = greensm.dau_giao({"dia_chi": "208 Nguyễn Hữu Cảnh", "ten": "Chị Lan", "sdt": "0901234567", "cod": 650000},
		{"dia_chi": "9 Trần Cao Vân", "lat": 10.7869, "lng": 106.6993})
	dung("điểm lấy khác thì khác", a != d)


@ca("v612 gọi xe: thiếu số điện thoại người nhận thì chặn trước khi gọi GreenSM")
def _():
	import frappe

	with _Bo() as bo:
		mang = _Mang()
		d = _don()
		d["sdt"] = ""
		vd = _vd(bo, _cfg(), mang, d)
		try:
			vd.gsm_bao_gia("VD-2026-00123", service_id="1878", addon_ids="[]")
			loi = ""
		except frappe.ValidationError as e:
			loi = str(e)
	dung("nói rõ thiếu số", "số điện thoại" in loi)
	la("không gọi mạng", mang.goi, [])


@ca("v612: không còn khung GreenSM cũ đoán trường (lat/lng, contact_name) ở đâu nữa")
def _():
	# Dò chuỗi chỉ để chốt "không còn chỗ nào dựng thân kiểu cũ" (điều 16).
	import io
	import os

	goi = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	s = io.open(os.path.join(goi, "van_don.py"), encoding="utf-8").read()
	dung("không còn MAP_GSM", "MAP_GSM" not in s)
	dung("không còn _greensm_token riêng ở van_don", "def _greensm_token" not in s)
	dung("token GreenSM chỉ ở greensm.py", "vgb:gsm:token" not in s)

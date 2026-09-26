"""Đơn đặt bánh từ website: bản ghi bền giữ ở ERP TRƯỚC khi gửi Pancake (#367).

Vì sao có tệp này
-----------------
Trước 25/09/2026 `don_hang.tao_don` POST thẳng sang Pancake, và ERP không giữ
gì cả. Ba hệ quả thật:

1. Pancake chậm hay rớt mạng giữa chừng thì trình duyệt báo "Chưa gửi được
   đơn", khách bấm gửi lại, trong khi đơn đầu có thể ĐÃ vào Pancake. Hai đơn,
   bếp làm hai bánh. Không ai biết đơn nào là thật.
2. Không có một mã nào để dựng trang "Đặt hàng thành công" có đường dẫn riêng,
   mà bộ kiểm của Meta đòi phải có trước khi cho chạy quảng cáo.
3. Không đo được phễu: không biết đơn nào từ quảng cáo, đơn nào về tới hoá
   đơn thật.

Cách làm đã chốt trên issue #367 (Claude và Codex, anh Việt đồng ý 24/09):

- Mỗi lần khách bấm Gửi đơn là MỘT bản ghi `Vagabond Don Web`, ghi và commit
  trước khi gọi Pancake. Pancake mất phản hồi thì bản ghi sang Chờ đối soát,
  khách vẫn được báo "tiệm đã nhận, không cần đặt lại", và tác vụ 5 phút một
  lần tự đi tìm đơn bên Pancake để ghép.
- Chống trùng: cùng số điện thoại, cùng món, cùng giờ nhận, cùng nonce của
  một lần mở bước đặt, trong 15 phút thì trả lại ĐÚNG bản ghi cũ. Pancake
  không có cơ chế chống trùng công khai nào để dựa, nên KHÔNG tự gửi lại.
- Đường dẫn biên nhận mang token không đoán được. Máy chủ chỉ lưu BĂM của
  token. Token tính bằng HMAC từ khoá bí mật của site, muối riêng của bản ghi
  và nonce trình duyệt, nên lần gửi trùng trả lại được đúng token cũ mà vẫn
  không phải lưu token gốc.
- event_id gửi Meta là uuid riêng, KHÔNG dùng token làm event_id: token là
  chìa khoá mở trang, còn event_id đi ra ngoài.
- Sự kiện "GuiDon" khi bản ghi đã lưu; "Purchase" CHỈ khi Sales Invoice của
  đơn đó được ghi sổ, vì lúc khách bấm gửi chưa ai thu tiền.

Phần THUẦN nằm trên, phần chạm Frappe nằm dưới dòng `import frappe`.
"""

# phần thuần
import base64
import hashlib
import hmac
import json
import re
import secrets
import uuid

DOCTYPE = "Vagabond Don Web"

TRANG_THAI = ("Dang gui", "Da nhan", "Cho doi soat", "Da ghi so", "Da huy")
# Chữ khách đọc trên trang biên nhận. "Đang xác nhận" cho cả hai trạng thái
# chưa chắc đơn đã vào Pancake: khách không cần biết chuyện hệ thống bên trong.
NHAN_TRANG_THAI = {
	"Dang gui": "Đang xác nhận",
	"Cho doi soat": "Đang xác nhận",
	"Da nhan": "Đã nhận",
	"Da ghi so": "Đã nhận",
	"Da huy": "Đã huỷ",
}
TRANG_THAI_CON_HIEU_LUC = ("Dang gui", "Da nhan", "Cho doi soat", "Da ghi so")

PHUT_CHONG_TRUNG = 15
NGUONG_MIEN_PHI_MAC_DINH = 1000000
PHUT_BAO_SALES = 30
URL_TRANG = "https://order.thevagabondpatisserie.com/banh"
GRAPH_MAC_DINH = "v23.0"

RE_NONCE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
RE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")
RE_FB = re.compile(r"^fb\.[0-9]\.[0-9]{10,16}\.[A-Za-z0-9_.\-]{1,200}$")

# Pháp nhân in ở chân trang mọi trang khách. Không đổi theo cấu hình: đây là
# thông tin đăng ký kinh doanh, sai là sai với cơ quan nhà nước.
PHAP_NHAN = {
	"ten": "Công ty TNHH Patisserie Vagabond",
	"mst": "0318561568",
	"dia_chi": [
		{"ten": "Cửa hàng Sài Gòn", "dia_chi": "9 Trần Cao Vân, Phường Sài Gòn (Quận 1 cũ), TP. Hồ Chí Minh"},
		{"ten": "Bếp Tân Sơn Hoà", "dia_chi": "307/1 Nguyễn Văn Trỗi, Phường Tân Sơn Hoà (Tân Bình cũ), TP. Hồ Chí Minh"},
	],
}

# Tâm khu vực để báo PHÍ GIAO DỰ KIẾN ngay khi khách chọn quận, trước khi gõ
# địa chỉ (#367 mục 5). Toạ độ gần đúng ở giữa khu dân cư của từng quận cũ:
# chỉ dùng cho con số dự kiến, nhập đủ địa chỉ thì máy hỏi lại bằng toạ độ
# thật. Khách vẫn quen gọi theo quận cũ dù TP. HCM đã bỏ cấp quận từ 07/2025.
QUAN = [
	{"ma": "q1", "ten": "Quận 1", "lat": 10.7769, "lng": 106.7009},
	{"ma": "q3", "ten": "Quận 3", "lat": 10.7843, "lng": 106.6844},
	{"ma": "q4", "ten": "Quận 4", "lat": 10.7578, "lng": 106.7013},
	{"ma": "q5", "ten": "Quận 5", "lat": 10.7540, "lng": 106.6634},
	{"ma": "q6", "ten": "Quận 6", "lat": 10.7480, "lng": 106.6352},
	{"ma": "q7", "ten": "Quận 7", "lat": 10.7340, "lng": 106.7218},
	{"ma": "q8", "ten": "Quận 8", "lat": 10.7240, "lng": 106.6286},
	{"ma": "q10", "ten": "Quận 10", "lat": 10.7746, "lng": 106.6679},
	{"ma": "q11", "ten": "Quận 11", "lat": 10.7629, "lng": 106.6501},
	{"ma": "q12", "ten": "Quận 12", "lat": 10.8671, "lng": 106.6413},
	{"ma": "binh-thanh", "ten": "Bình Thạnh", "lat": 10.8106, "lng": 106.7091},
	{"ma": "phu-nhuan", "ten": "Phú Nhuận", "lat": 10.7992, "lng": 106.6803},
	{"ma": "tan-binh", "ten": "Tân Bình", "lat": 10.8015, "lng": 106.6526},
	{"ma": "tan-phu", "ten": "Tân Phú", "lat": 10.7901, "lng": 106.6282},
	{"ma": "go-vap", "ten": "Gò Vấp", "lat": 10.8387, "lng": 106.6653},
	{"ma": "binh-tan", "ten": "Bình Tân", "lat": 10.7652, "lng": 106.6039},
	{"ma": "thu-duc-q2", "ten": "Thủ Đức (Quận 2 cũ)", "lat": 10.7872, "lng": 106.7498},
	{"ma": "thu-duc-q9", "ten": "Thủ Đức (Quận 9 cũ)", "lat": 10.8428, "lng": 106.8287},
	{"ma": "thu-duc", "ten": "Thủ Đức (khu Thủ Đức cũ)", "lat": 10.8494, "lng": 106.7537},
	{"ma": "nha-be", "ten": "Nhà Bè", "lat": 10.6952, "lng": 106.7045},
]

TEN_THANH_TOAN = {"bank": "Chuyển khoản (mã VietQR)", "card": "Thẻ qua cổng OnePay"}
THU = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


def bam(s):
	"""SHA-256 dạng hex. Dùng cho băm token và băm dữ liệu gửi Meta."""
	return hashlib.sha256(str(s or "").encode("utf-8")).hexdigest()


def sinh_muoi():
	return secrets.token_hex(32)


def sinh_event_id():
	return str(uuid.uuid4())


def nonce_hop_le(n):
	return bool(RE_NONCE.match(str(n or "")))


def token_hop_le(t):
	return bool(RE_TOKEN.match(str(t or "")))


def sinh_token(khoa_bi_mat, muoi, nonce):
	"""Token 32 byte trên đường dẫn biên nhận, dạng base64url 43 ký tự.

	HMAC-SHA256 trên (muối của bản ghi, nonce trình duyệt) bằng khoá bí mật
	của site. Muối sinh ngẫu nhiên 32 byte ở máy chủ nên kể cả trình duyệt gửi
	nonce yếu thì token vẫn không đoán được. Cùng muối cùng nonce thì cùng
	token: lần gửi trùng lấy lại được đúng đường dẫn cũ.
	"""
	if isinstance(khoa_bi_mat, str):
		khoa_bi_mat = khoa_bi_mat.encode("utf-8")
	mac = hmac.new(khoa_bi_mat, ("%s:%s" % (muoi, nonce)).encode("utf-8"), hashlib.sha256).digest()
	return base64.urlsafe_b64encode(mac).decode("ascii").rstrip("=")


def _chu_so(s):
	return "".join(ch for ch in str(s or "") if ch.isdigit())


def khoa_chong_trung(sdt, hang, ngay_nhan, nonce):
	"""Khoá nhận ra hai lần bấm của CÙNG một lần đặt.

	`hang` là danh sách {"variation_id", "quantity"} đã làm sạch. Thứ tự dòng
	không được làm đổi khoá, nên xếp lại trước khi băm.
	"""
	mon = sorted("%s:%s" % (str(h.get("variation_id") or "").strip().upper(), int(h.get("quantity") or 0))
		for h in (hang or []))
	return bam("|".join([_chu_so(sdt)[-9:], ",".join(mon), str(ngay_nhan or ""), str(nonce or "")]))


def tinh_tien_banh(hang, gia):
	"""Tiền bánh máy chủ tự tính theo giá bán trên hồ sơ món. Trả (tổng, mã thiếu giá).

	Không tin con số trình duyệt gửi (QT-19). Mã nào không có giá thì tính 0
	và báo ra: tính 0 là phía an toàn, vì ngưỡng miễn phí giao chỉ có thể bị
	CHƯA đạt chứ không bao giờ bị đạt oan.
	"""
	tong, thieu = 0, []
	for h in hang or []:
		ma = str(h.get("variation_id") or "").strip()
		sl = int(h.get("quantity") or 0)
		g = int(round(float((gia or {}).get(ma) or 0)))
		if g <= 0:
			thieu.append(ma)
			continue
		tong += g * sl
	return tong, thieu


def quyet_phi_giao(tien_banh, nguong, tu_lay, bao_phi):
	"""Phí khách trả và phí tiệm chịu cho một đơn. THUẦN.

	Bốn trạng thái, đúng như đã chốt ở mục 4 của #367:
	  tu_lay    khách tự lấy: phí 0, KHÔNG tính là ưu đãi miễn phí giao.
	  mien_phi  tiền bánh từ ngưỡng trở lên: khách trả 0, tiệm chịu phí Ahamove.
	  chinh_xac có báo giá Ahamove: khách trả đúng số đó.
	  chua_ro   Ahamove không báo được: KHÔNG coi là 0, Sales báo phí khi gọi.

	Ngưỡng trống hoặc 0 là tắt miễn phí. Đủ ngưỡng mà Ahamove lỗi thì khách
	vẫn trả 0 (điều đó chắc chắn), chỉ phần tiệm chịu là chưa rõ.
	"""
	try:
		nguong = int(float(nguong or 0))
	except (TypeError, ValueError):
		nguong = 0
	tien_banh = int(tien_banh or 0)
	if tu_lay:
		return {"phi_khach": 0, "phi_ahamove": 0, "tiem_chiu": 0, "mien_phi": False, "trang_thai": "tu_lay"}
	phi = None
	if bao_phi and bao_phi.get("ok"):
		try:
			phi = int(bao_phi.get("total_fee") or 0)
		except (TypeError, ValueError):
			phi = None
		if not phi or phi <= 0:
			phi = None
	if nguong > 0 and tien_banh >= nguong:
		return {"phi_khach": 0, "phi_ahamove": phi, "tiem_chiu": phi or 0, "mien_phi": True, "trang_thai": "mien_phi"}
	if phi:
		return {"phi_khach": phi, "phi_ahamove": phi, "tiem_chiu": 0, "mien_phi": False, "trang_thai": "chinh_xac"}
	return {"phi_khach": None, "phi_ahamove": None, "tiem_chiu": 0, "mien_phi": False, "trang_thai": "chua_ro"}


def phan_loai_pancake(ma_http, du_lieu=None, loi_mang=False):
	"""Đọc phản hồi tạo đơn của Pancake ra một trong ba kết cục. THUẦN.

	da_nhan       có mã đơn: chắc chắn đơn đã vào Pancake.
	cho_doi_soat  mất phản hồi, lỗi máy chủ, hay trả về không đọc được: đơn CÓ
	              THỂ đã vào. Không tự gửi lại, để tác vụ đối soát đi tìm.
	tu_choi       Pancake nói rõ là không nhận (4xx, 429): chắc chắn chưa có
	              đơn, khách được báo gửi lại.
	"""
	if loi_mang:
		return {"ket_qua": "cho_doi_soat", "ly_do": "pancake_mat_phan_hoi"}
	try:
		ma_http = int(ma_http or 0)
	except (TypeError, ValueError):
		ma_http = 0
	if ma_http in (200, 201):
		if not isinstance(du_lieu, dict):
			return {"ket_qua": "cho_doi_soat", "ly_do": "pancake_tra_ve_la"}
		data = du_lieu.get("data") if isinstance(du_lieu.get("data"), dict) else du_lieu
		# Pancake tung doi ten truong ma don giua cac ban; API tao don tra
		# display_id duoi cai ten "id" (ghi chu cu trong don_hang.py).
		ma = data.get("id") or data.get("order_id") or data.get("system_id")
		if not ma:
			return {"ket_qua": "cho_doi_soat", "ly_do": "khong_ro_ma_don"}
		hien = data.get("display_id") or ma
		return {"ket_qua": "da_nhan", "pancake_id": str(ma), "pancake_display_id": str(hien)}
	if ma_http >= 500 or ma_http in (0, 408):
		return {"ket_qua": "cho_doi_soat", "ly_do": "pancake_loi_may_chu"}
	return {"ket_qua": "tu_choi", "ly_do": "pancake_tu_choi"}


def viet_tat_ten(ten):
	"""Tên trên trang biên nhận: chữ cái đầu của họ và tên đệm, giữ tên gọi.

	"Nguyễn Văn An" -> "N. V. An". Trang biên nhận mở được bằng đường dẫn, nên
	không in đủ họ tên, số điện thoại hay địa chỉ lên đó.
	"""
	ds = [x for x in str(ten or "").split() if x]
	if not ds:
		return ""
	if len(ds) == 1:
		return ds[0]
	return " ".join([x[0].upper() + "." for x in ds[:-1]] + [ds[-1]])


def khung_gio(ngay_nhan):
	"""("Thứ 5, 26/09", "13h - 15h") từ mốc ISO giờ bắt đầu khung. THUẦN."""
	t = str(ngay_nhan or "")
	m = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}))?", t)
	if not m:
		return "", ""
	import datetime as _dt

	try:
		d = _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
	except ValueError:
		return "", ""
	ngay = "%s, %02d/%02d" % (THU[d.weekday()], d.day, d.month)
	if m.group(4) is None:
		return ngay, ""
	gio = int(m.group(4))
	return ngay, "%dh - %dh" % (gio, gio + 2)


def dinh_tien(n):
	"""1250000 -> "1.250.000 đ"."""
	return "{:,}".format(int(n or 0)).replace(",", ".") + " đ"


def tom_tat_bien_nhan(ban_ghi, snapshot):
	"""Dữ liệu tối thiểu cho trang biên nhận. KHÔNG có số điện thoại, email
	hay địa chỉ giao: trang mở được bằng đường dẫn, ai cầm link là đọc được.
	"""
	ban_ghi = ban_ghi or {}
	snap = snapshot or {}
	tt = ban_ghi.get("trang_thai") or "Dang gui"
	phi = snap.get("phi") or {}
	tien_banh = int(ban_ghi.get("tien_banh") or 0)
	trang_thai_phi = phi.get("trang_thai") or ban_ghi.get("trang_thai_phi") or ""
	phi_khach = phi.get("phi_khach")
	if trang_thai_phi == "tu_lay":
		nhan_phi, tong = "Tự lấy, không tính phí", tien_banh
	elif trang_thai_phi == "mien_phi":
		nhan_phi, tong = "Miễn phí giao", tien_banh
	elif trang_thai_phi == "chinh_xac" and phi_khach:
		nhan_phi, tong = dinh_tien(phi_khach), tien_banh + int(phi_khach)
	else:
		nhan_phi, tong = "Sales báo phí khi xác nhận", None
	ngay, gio = khung_gio(snap.get("ngay_nhan"))
	if snap.get("tu_lay"):
		cach_nhan = "Tự lấy tại " + (snap.get("diem_lay_ten") or snap.get("dia_chi") or "cửa hàng")
	else:
		cach_nhan = "Giao tận nơi"
	cho = tt in ("Dang gui", "Cho doi soat")
	return {
		"ma": ban_ghi.get("name") or "",
		"trang_thai": NHAN_TRANG_THAI.get(tt, "Đang xác nhận"),
		"dang_xac_nhan": cho,
		"da_huy": tt == "Da huy",
		"cau": (
			"Tiệm đã nhận yêu cầu, Sales sẽ gọi xác nhận trong ít phút. Không cần đặt lại."
			if cho else (
				"Đơn này đã được huỷ. Anh chị cần đặt lại thì nhắn tiệm qua Zalo hoặc Messenger bên dưới."
				if tt == "Da huy" else
				"Tiệm đã nhận đơn. Sales sẽ gọi xác nhận rồi gửi cách thanh toán trong ít phút."
			)
		),
		"ten": viet_tat_ten((snap.get("nguoi_dat") or {}).get("ho_ten")),
		"mon": [
			{"ten": m.get("ten") or m.get("ma"), "sl": int(m.get("sl") or 0),
			 "thanh_tien": dinh_tien(int(m.get("gia") or 0) * int(m.get("sl") or 0)) if m.get("gia") else ""}
			for m in (snap.get("mon") or [])
		],
		"tien_banh": dinh_tien(tien_banh),
		"phi_giao": nhan_phi,
		"tong": dinh_tien(tong) if tong is not None else "Chờ Sales báo phí giao",
		"ngay_nhan": ngay,
		"khung_gio": gio,
		"cach_nhan": cach_nhan,
		"thanh_toan": TEN_THANH_TOAN.get(snap.get("thanh_toan") or "bank", TEN_THANH_TOAN["bank"]),
	}


def fb_hop_le(v):
	"""Cookie _fbp / _fbc có đúng dạng Meta không. Sai dạng thì bỏ, không gửi."""
	return bool(RE_FB.match(str(v or "")))


def sdt_quoc_te(sdt):
	"""0931224334 -> 84931224334, dạng Meta đòi trước khi băm. Không đọc được thì rỗng."""
	x = _chu_so(sdt)
	if x.startswith("84") and len(x) == 11:
		return x
	if x.startswith("0") and len(x) == 10:
		return "84" + x[1:]
	if len(x) == 9:
		return "84" + x
	return ""


def goi_su_kien(ten, event_id, luc_unix, gia_tri, ma_mon, sdt=None, email=None,
		fbp=None, fbc=None, trinh_duyet=None, ip=None, url=URL_TRANG):
	"""Một sự kiện Conversions API. THUẦN, không gửi gì.

	Số điện thoại và email BĂM trước khi rời máy chủ, đúng chuẩn Meta:
	điện thoại đủ mã nước không dấu cộng, email viết thường bỏ khoảng trắng.
	URL nguồn là trang đặt bánh, KHÔNG bao giờ là đường dẫn mang token.
	"""
	ud = {}
	ph = sdt_quoc_te(sdt)
	if ph:
		ud["ph"] = [bam(ph)]
	thu = str(email or "").strip().lower()
	if thu and "@" in thu:
		ud.update(em=[bam(thu)])
	if fb_hop_le(fbp):
		ud["fbp"] = str(fbp)
	if fb_hop_le(fbc):
		ud["fbc"] = str(fbc)
	if trinh_duyet:
		ud["client_user_agent"] = str(trinh_duyet)[:400]
	if ip:
		ud["client_ip_address"] = str(ip)[:64]
	ma = [str(x) for x in (ma_mon or []) if x]
	return {
		"event_name": ten,
		"event_time": int(luc_unix),
		"event_id": str(event_id),
		"action_source": "website",
		"event_source_url": url,
		"user_data": ud,
		"custom_data": {
			"value": int(gia_tri or 0),
			"currency": "VND",
			"content_ids": ma,
			"content_type": "product",
			"num_items": len(ma),
		},
	}


# Trạng thái Pancake bỏ qua, cùng nguồn với vagabond.lib.PANCAKE_BO_QUA (phần
# thuần không import lib để giữ tệp nạp được không cần Frappe).
PANCAKE_BO_QUA = frozenset({6, 7})


def _tt_pancake(tt):
	try:
		return int(tt)
	except (TypeError, ValueError):
		return None


def ghep_don_pancake(sdt, tao_luc, hang, dons, da_gan=(), truoc=600, sau=3600):
	"""Tìm đơn Pancake ứng với một bản ghi Chờ đối soát. THUẦN.

	Chỉ nhận khi có ĐÚNG MỘT đơn thoả cả ba: cùng số điện thoại, tạo trong
	khoảng [tao_luc - truoc, tao_luc + sau] giây, và cùng đúng danh sách món
	với số lượng. Hai đơn cùng thoả thì không đoán, để Sales ghép tay; ghép
	nhầm là gửi Purchase cho một đơn khác và gắn hoá đơn công ty nhầm khách.

	`dons` là đơn Pancake thô; `hang` là danh sách {"variation_id", "quantity"}
	theo MÃ HIỂN THỊ (BAWC00139), `da_gan` là mã đơn đã thuộc bản ghi khác.
	Trả (đơn, lý do): lý do là "khop", "khong_thay" hoặc "nhieu".
	"""
	from vagabond.ngay_pancake import unix_tu_iso

	muc = sorted("%s:%s" % (str(h.get("variation_id") or "").upper(), int(h.get("quantity") or 0)) for h in hang or [])
	so = _chu_so(sdt)[-9:]
	gan = set(str(x) for x in (da_gan or ()) if x)
	ung = []
	for o in dons or []:
		if not isinstance(o, dict):
			continue
		# Đơn Pancake đã huỷ hoặc đã xoá (6, 7) không phải ứng viên: ghép vào
		# là bản ghi thành Đã nhận, tắt báo Sales, cho một đơn không giao (Codex).
		if _tt_pancake(o.get("status")) in PANCAKE_BO_QUA:
			continue
		if str(o.get("id") or "") in gan or str(o.get("display_id") or "") in gan:
			continue
		if _chu_so(o.get("bill_phone_number"))[-9:] != so or not so:
			continue
		t = unix_tu_iso(o.get("inserted_at"))
		if t is None or not (tao_luc - truoc <= t <= tao_luc + sau):
			continue
		gom = {}
		for it in o.get("items") or []:
			vi = (it or {}).get("variation_info") or {}
			ma = str(vi.get("display_id") or "").strip().upper()
			if not ma:
				continue
			gom[ma] = gom.get(ma, 0) + int((it or {}).get("quantity") or 0)
		if sorted("%s:%s" % (k, v) for k, v in gom.items()) != muc:
			continue
		ung.append(o)
	if len(ung) == 1:
		return ung[0], "khop"
	return None, ("nhieu" if ung else "khong_thay")


def soan_tin_sales(ban_ghi, url=""):
	"""Tin Lark cho nhóm Sales khi một đơn web quá 30 phút chưa ghép được."""
	b = ban_ghi or {}
	dong = [
		"ĐƠN WEB CHƯA VÀO PANCAKE: %s" % (b.get("name") or ""),
		"Khách %s, điện thoại %s." % (b.get("ho_ten") or "không tên", b.get("dien_thoai") or "không có"),
		"Tiền bánh %s, nhận %s." % (dinh_tien(b.get("tien_banh")), " ".join(x for x in khung_gio(b.get("ngay_nhan")) if x) or "chưa rõ"),
		"Máy chưa tìm thấy đơn này bên Pancake sau %d phút. Sales gọi khách xác nhận, tạo đơn tay nếu cần, rồi điền mã đơn Pancake vào bản ghi." % PHUT_BAO_SALES,
	]
	if url:
		dong.append(url)
	return "\n".join(dong)



# Ô do máy sinh ra lúc gửi đơn: người sửa tay trên Desk không được đổi, vì
# đổi token_hash là khoá trang biên nhận của khách, đổi snapshot hay tiền là
# sửa lại lịch sử một đơn khách đã gửi.
KHONG_DOI = ("token_hash", "muoi", "khoa_chong_trung", "event_id_gui_don", "event_id_mua_hang",
	"snapshot", "tien_banh", "phi_khach", "phi_ahamove", "dien_thoai", "ho_ten", "ngay_nhan")


def gia_tri_giong(a, b):
	"""Hai giá trị của cùng một ô có như nhau không, bỏ qua cách viết. THUẦN.

	Form Desk gửi lại 650000 trong khi CSDL giữ 650000.0, và giờ có thể thêm
	phần lẻ của giây. So chuỗi thẳng thì người chỉ bấm Lưu cũng bị chặn oan.
	"""
	if a in (None, "") and b in (None, ""):
		return True
	if isinstance(a, (int, float)) or isinstance(b, (int, float)):
		try:
			return abs(float(a) - float(b)) < 0.0001
		except (TypeError, ValueError):
			return False
	sa, sb = str(a if a is not None else "").strip(), str(b if b is not None else "").strip()
	if re.match(r"^\d{4}-\d{2}-\d{2}", sa) and re.match(r"^\d{4}-\d{2}-\d{2}", sb):
		return sa.replace("T", " ")[:19] == sb.replace("T", " ")[:19]
	return sa == sb


def chuyen_hop_le(cu, moi, co_ma_pancake, may=False):
	"""Người sửa tay được chuyển trạng thái nào. THUẦN.

	Máy (luồng tạo đơn, đối soát, hook hoá đơn) đi mọi đường. Người thì chỉ:
	  Chờ đối soát hoặc Đang gửi -> Đã nhận, khi đã điền mã đơn Pancake;
	  mọi trạng thái chưa ghi sổ -> Đã huỷ.
	Không ai tay được đặt Đã ghi sổ: trạng thái đó chỉ đến từ hoá đơn thật,
	và kéo theo sự kiện Purchase gửi Meta.
	"""
	if cu == moi or may:
		return True
	if moi == "Da huy":
		return cu != "Da ghi so"
	if moi == "Da nhan":
		return cu in ("Cho doi soat", "Dang gui") and bool(co_ma_pancake)
	return False


# ---------------------------------------------------------------------------
import frappe
from frappe.utils import add_to_date, cint, get_datetime, now_datetime

try:
	from frappe.utils.synchronization import filelock
except Exception:  # pragma: no cover
	import contextlib

	@contextlib.contextmanager
	def filelock(ten, timeout=30, **kw):
		yield

from vagabond.lib import cfg, cfg_o, key


def _khoa_bi_mat():
	from frappe.utils.password import get_encryption_key

	return (get_encryption_key() + ":vagabond-don-web").encode("utf-8")


def nguong_mien_phi():
	"""Ngưỡng miễn phí giao đọc từ Vagabond Settings. Ô trống là tắt."""
	v = cfg_o("mien_phi_giao_tu")
	try:
		return int(float(v or 0))
	except (TypeError, ValueError):
		return 0


def lien_he():
	"""Số điện thoại, email, mạng xã hội cho chân trang. Anh Việt điền ở Settings."""
	dt = str(cfg_o("web_dien_thoai") or "").strip()
	zalo = str(cfg_o("web_zalo") or "").strip()
	if not zalo and _chu_so(dt):
		zalo = "https://zalo.me/" + _chu_so(dt)
	return {
		"dien_thoai": dt,
		"dien_thoai_so": _chu_so(dt),
		"email": str(cfg_o("web_email") or "").strip(),
		"zalo": zalo,
		"messenger": str(cfg_o("web_messenger") or "").strip(),
		"facebook": str(cfg_o("web_facebook") or "").strip(),
		"instagram": str(cfg_o("web_instagram") or "").strip(),
		"tiktok": str(cfg_o("web_tiktok") or "").strip(),
	}


def pixel_id():
	return re.sub(r"[^0-9]", "", str(cfg_o("meta_pixel_id") or ""))


@frappe.whitelist(allow_guest=True)
def cau_hinh_web():
	"""Cấu hình công khai cho trang đặt bánh. KHÔNG bao giờ có token CAPI."""
	from vagabond import noi_dung_web

	return {
		"pixel_id": pixel_id(),
		"mien_phi_tu": nguong_mien_phi(),
		"lien_he": lien_he(),
		"phap_nhan": PHAP_NHAN,
		"chinh_sach": noi_dung_web.chinh_sach_dang_hien(),
		"quan": [{"ma": q["ma"], "ten": q["ten"], "lat": q["lat"], "lng": q["lng"]} for q in QUAN],
	}


def tim_trung(khoa):
	"""Bản ghi còn hiệu lực cùng khoá trong 15 phút gần nhất, hoặc None."""
	tu = add_to_date(now_datetime(), minutes=-PHUT_CHONG_TRUNG)
	ds = frappe.get_all(
		DOCTYPE,
		filters={"khoa_chong_trung": khoa, "creation": [">=", tu], "trang_thai": ["in", list(TRANG_THAI_CON_HIEU_LUC)]},
		fields=["name"],
		order_by="creation desc",
		limit_page_length=1,
		ignore_permissions=True,
	)
	return frappe.get_doc(DOCTYPE, ds[0]["name"]) if ds else None


def khoa_ghi(khoa):
	"""Khoá tệp theo khoá chống trùng, để hai lần bấm cùng lúc không cùng lọt."""
	return filelock("vgb_don_web_" + str(khoa)[:24], timeout=20)


def tao_ban_ghi(nonce, truong):
	"""Ghi bản ghi trạng thái Đang gửi. Bên gọi commit ngay sau đó.

	`truong` là các ô nghiệp vụ; muối, token, event_id do hàm này tự sinh,
	không nhận từ bên ngoài.
	"""
	d = frappe.new_doc(DOCTYPE)
	d.update(truong)
	d.trang_thai = "Dang gui"
	d.muoi = sinh_muoi()
	d.event_id_gui_don = sinh_event_id()
	d.event_id_mua_hang = sinh_event_id()
	d.token_hash = bam(sinh_token(_khoa_bi_mat(), d.muoi, nonce))
	d.insert(ignore_permissions=True)
	return d


def token_cua(ban_ghi, nonce):
	return sinh_token(_khoa_bi_mat(), ban_ghi.muoi, nonce)


def cap_nhat_sau_pancake(ban_ghi, kq):
	"""Ghi kết cục của lần gọi Pancake lên bản ghi. Bên gọi commit."""
	ban_ghi.reload()
	if kq["ket_qua"] == "da_nhan":
		ban_ghi.trang_thai = "Da nhan"
		ban_ghi.pancake_id = kq.get("pancake_id")
		ban_ghi.pancake_display_id = kq.get("pancake_display_id")
		ban_ghi.ly_do = ""
	elif kq["ket_qua"] == "cho_doi_soat":
		ban_ghi.trang_thai = "Cho doi soat"
		ban_ghi.ly_do = kq.get("ly_do") or ""
	else:
		ban_ghi.trang_thai = "Da huy"
		ban_ghi.ly_do = kq.get("ly_do") or "pancake_tu_choi"
	# on_update cua doctype tu tao yeu cau hoa don cong ty khi sang Da nhan.
	ban_ghi.save(ignore_permissions=True)


def luu_hoa_don_cong_ty(ban_ghi):
	"""Yêu cầu hoá đơn công ty gắn với bản ghi đơn web (#367 mục 1).

	Trước đây `_luu_hoa_don` commit riêng ngay sau Pancake, không dính gì tới
	đơn; đơn mất phản hồi thì yêu cầu hoá đơn mất theo. Nay giữ trong ảnh chụp
	của bản ghi, và chỉ tạo `Vagabond Hoa Don` khi đã có mã đơn Pancake, vì kế
	toán tra yêu cầu theo đúng mã đó (`ban_hang._yeu_cau_xhd_dung_don`).
	"""
	if ban_ghi.hoa_don_cong_ty or not ban_ghi.pancake_display_id:
		return
	snap = json.loads(ban_ghi.snapshot or "{}")
	hd = snap.get("hoa_don") or None
	if not hd or not _chu_so(hd.get("tax_code")):
		return
	ma_don = str(ban_ghi.pancake_display_id)
	ten = frappe.db.get_value("Vagabond Hoa Don", {"ma_don": ma_don}, "name")
	if not ten:
		doc = frappe.new_doc("Vagabond Hoa Don")
		doc.ma_don = ma_don
		doc.ma_so_thue = _chu_so(hd.get("tax_code"))
		doc.ten_cong_ty = (hd.get("name") or "").strip()
		doc.dia_chi = (hd.get("address") or "").strip()
		doc.email = (hd.get("email") or "").strip()
		doc.tinh_trang = "Chua xuat"
		doc.insert(ignore_permissions=True)
		ten = doc.name
	frappe.db.set_value(DOCTYPE, ban_ghi.name, "hoa_don_cong_ty", ten, update_modified=False)


def phan_hoi(ban_ghi, nonce, trung=False):
	"""Câu trả lời cho trình duyệt sau khi gửi đơn."""
	snap = json.loads(ban_ghi.snapshot or "{}")
	phi = snap.get("phi") or {}
	return {
		"ok": 1,
		"trung": 1 if trung else 0,
		"ma_yeu_cau": ban_ghi.name,
		"duong_dan": "/banh/xong/" + token_cua(ban_ghi, nonce),
		"trang_thai": ban_ghi.trang_thai,
		"ma_don": ban_ghi.pancake_display_id or "",
		"phi_giao": phi.get("phi_khach"),
		"trang_thai_phi": phi.get("trang_thai") or "",
		"mien_phi": 1 if phi.get("mien_phi") else 0,
		"da_gui_hoa_don": 1 if snap.get("hoa_don") else 0,
	}


def xep_capi(ten, loai, ip=None, ua=None, sau_commit=False):
	"""Xếp việc gửi sự kiện Meta. Chưa cấu hình Pixel hay token thì thôi.

	Lỗi xếp hàng chỉ ghi nhật ký: đơn khách đã lưu rồi, không được hỏng theo.
	"""
	try:
		if getattr(frappe.flags, "vagabond_kiem_that", False):
			return
		if not pixel_id() or not key(cfg(), "meta_capi_token"):
			return
		# sau_commit=True khi goi tu giua mot giao dich (hook ghi so hoa don):
		# job chi duoc chay sau khi hoa don that su vao so. Goi tu tao_don thi
		# ban ghi DA commit roi, xep ngay; cho commit tiep theo la co the khong
		# bao gio toi, vi request co the ket thuc ma khong ghi them gi.
		frappe.enqueue("vagabond.don_web.gui_capi", queue="short", ten=ten, loai=loai, ip=ip, ua=ua,
			enqueue_after_commit=bool(sau_commit))
	except Exception:
		frappe.log_error(title="Don web: chua xep duoc su kien Meta",
			message="Ban ghi %s su kien %s. Kiem tra hang doi." % (ten, loai))


def _unix(dt):
	"""Mốc unix của một giờ Frappe. Frappe giữ giờ KHÔNG khai múi theo múi giờ
	hệ thống (Asia/Ho_Chi_Minh), còn tiến trình máy chủ có thể chạy UTC: gọi
	thẳng .timestamp() là lệch 7 tiếng, Meta từ chối event_time ở tương lai
	và phép ghép đơn Pancake trượt khung giờ."""
	from zoneinfo import ZoneInfo

	d = get_datetime(dt)
	if d.tzinfo is None:
		try:
			mui = frappe.utils.get_system_timezone() or "Asia/Ho_Chi_Minh"
		except Exception:
			mui = "Asia/Ho_Chi_Minh"
		d = d.replace(tzinfo=ZoneInfo(mui))
	return int(d.timestamp())


def gui_capi(ten, loai, ip=None, ua=None):
	"""Gửi một sự kiện Conversions API, thử lại ba lần giãn cách.

	Lỗi chỉ ghi Error Log với mã bản ghi và mã HTTP: KHÔNG ghi token, không
	ghi dữ liệu khách. Đã gửi một lần thì không gửi lại (cờ thời điểm).
	"""
	import time

	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	px = pixel_id()
	tk = key(cfg(), "meta_capi_token")
	if not (px and tk) or loai not in ("GuiDon", "Purchase"):
		return
	d = frappe.get_doc(DOCTYPE, ten)
	truong = "capi_gui_don_luc" if loai == "GuiDon" else "capi_mua_hang_luc"
	if d.get(truong):
		return
	snap = json.loads(d.snapshot or "{}")
	nguoi = snap.get("nguoi_dat") or {}
	ma_mon = [m.get("ma") for m in (snap.get("mon") or [])]
	if loai == "GuiDon":
		ev, luc, gia_tri = d.event_id_gui_don, _unix(d.creation), d.tien_banh
	else:
		ev, luc, gia_tri = d.event_id_mua_hang, _unix(d.ghi_so_luc or now_datetime()), d.gia_tri_ghi_so
	goi = goi_su_kien(loai, ev, luc, gia_tri, ma_mon, sdt=nguoi.get("dien_thoai"), email=nguoi.get("email"),
		fbp=d.fbp, fbc=d.fbc, trinh_duyet=ua or d.trinh_duyet, ip=ip)
	than = {"data": [goi]}
	ma_thu = str(cfg_o("meta_test_event_code") or "").strip()
	if ma_thu:
		than["test_event_code"] = ma_thu
	phien = str(cfg_o("meta_graph_phien_ban") or "").strip() or GRAPH_MAC_DINH
	url = "https://graph.facebook.com/%s/%s/events" % (phien, px)
	loi = ""
	import requests

	for cho in (0, 5, 20):
		if cho:
			time.sleep(cho)
		try:
			r = requests.post(url, params={"access_token": tk}, json=than, timeout=10)
		except Exception as e:
			loi = "không nối được (%s)" % type(e).__name__
			continue
		if r.status_code == 200:
			frappe.db.set_value(DOCTYPE, ten, {truong: now_datetime(), "capi_loi": ""}, update_modified=False)
			frappe.db.commit()
			return
		thong_bao = ""
		try:
			thong_bao = str(((r.json() or {}).get("error") or {}).get("message") or "")[:200]
		except Exception:
			pass
		loi = "HTTP %s %s" % (r.status_code, thong_bao)
		if 400 <= r.status_code < 500 and r.status_code != 429:
			break
	frappe.db.set_value(DOCTYPE, ten, "capi_loi", ("%s: %s" % (loai, loi))[:300], update_modified=False)
	frappe.log_error(title="Don web: chua gui duoc su kien Meta", message="Ban ghi %s, su kien %s: %s" % (ten, loai, loi))
	frappe.db.commit()


def khi_ghi_so_hoa_don(doc, method=None):
	"""Hook Sales Invoice on_submit: đơn web về tới hoá đơn thật thì báo Meta Purchase.

	Chỉ một câu truy vấn có chỉ mục, và nuốt mọi lỗi: ghi sổ hoá đơn quan
	trọng hơn đo quảng cáo nhiều lần, không được để hook này chặn ghi sổ.
	"""
	try:
		if getattr(frappe.flags, "vagabond_kiem_that", False):
			return
		# Hoa don tra hang mang lai ma Pancake cua don goc: khong phai mot lan
		# mua moi, khong duoc de len hoa don goc hay gui Purchase lan nua.
		if doc.get("is_return"):
			return
		ma = [str(x).strip() for x in (doc.get("custom_pancake_id"), doc.get("custom_pancake_display_id")) if str(x or "").strip()]
		if not ma:
			return
		ten = (frappe.db.get_value(DOCTYPE, {"pancake_display_id": ["in", ma]}, "name")
			or frappe.db.get_value(DOCTYPE, {"pancake_id": ["in", ma]}, "name"))
		if not ten or frappe.db.get_value(DOCTYPE, ten, "trang_thai") == "Da ghi so":
			return
		frappe.db.set_value(DOCTYPE, ten, {
			"trang_thai": "Da ghi so",
			"sales_invoice": doc.name,
			"ghi_so_luc": now_datetime(),
			"gia_tri_ghi_so": int(round(float(doc.get("grand_total") or 0))),
		}, update_modified=False)
		xep_capi(ten, "Purchase", sau_commit=True)
	except Exception:
		frappe.log_error(title="Don web: hook ghi so hoa don", message=frappe.get_traceback())


def bien_nhan_theo_token(token):
	"""Dữ liệu trang biên nhận, hoặc None nếu token sai hay không tồn tại."""
	if not token_hop_le(token):
		return None
	ds = frappe.get_all(DOCTYPE, filters={"token_hash": bam(token)},
		fields=["name", "trang_thai", "tien_banh", "trang_thai_phi", "snapshot",
			"event_id_gui_don", "creation"],
		limit_page_length=1, ignore_permissions=True)
	if not ds:
		return None
	b = ds[0]
	snap = json.loads(b.get("snapshot") or "{}")
	tt = tom_tat_bien_nhan(b, snap)
	return {
		"bien_nhan": tt,
		"su_kien": {
			"event_id": b.get("event_id_gui_don"),
			"gia_tri": int(b.get("tien_banh") or 0),
			"ma_mon": [m.get("ma") for m in (snap.get("mon") or []) if m.get("ma")],
			"ban": b.get("trang_thai") != "Da huy",
		},
	}


def _dang_cho():
	"""Bản ghi cần đối soát: Chờ đối soát, hoặc Đang gửi quá 2 phút (tiến
	trình chết giữa lúc gọi Pancake thì bản ghi kẹt ở Đang gửi mãi mãi)."""
	now = now_datetime()
	ds = frappe.get_all(DOCTYPE,
		filters={"trang_thai": ["in", ["Cho doi soat", "Dang gui"]], "creation": [">=", add_to_date(now, days=-2)]},
		fields=["name", "trang_thai", "creation", "dien_thoai", "ho_ten", "tien_banh", "ngay_nhan",
			"snapshot", "da_bao_sales_luc"],
		order_by="creation asc", limit_page_length=200, ignore_permissions=True)
	moc = add_to_date(now, minutes=-2)
	return [r for r in ds if r["trang_thai"] == "Cho doi soat" or get_datetime(r["creation"]) <= moc]


def doi_soat_tu_dong():
	"""Nhịp 5 phút: tìm đơn Pancake cho bản ghi chưa có mã, quá 30 phút báo Sales."""
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	try:
		ds = _dang_cho()
		if not ds:
			return
		from vagabond.kiem_banh import LoiPancake, _keo_don

		c = cfg()
		k = key(c, "pancake_api_key")
		if not (k and c.pancake_shop_id):
			return
		dau = min(_unix(r["creation"]) for r in ds) - 600
		cuoi = _unix(now_datetime()) + 60
		try:
			dons = _keo_don(c, k, "inserted_at", dau, cuoi)
		except LoiPancake as e:
			frappe.log_error(title="Don web: doi soat chua keo duoc Pancake", message=str(e)[:500])
			dons = []
		gan = set(frappe.get_all(DOCTYPE, filters={"pancake_display_id": ["is", "set"],
			"creation": [">=", add_to_date(now_datetime(), days=-3)]}, pluck="pancake_display_id",
			ignore_permissions=True))
		gan |= set(frappe.get_all(DOCTYPE, filters={"pancake_id": ["is", "set"],
			"creation": [">=", add_to_date(now_datetime(), days=-3)]}, pluck="pancake_id",
			ignore_permissions=True))
		for r in ds:
			# Mỗi bản ghi tự chịu lỗi của mình: một snapshot hỏng không được
			# chặn các bản ghi sau đó khỏi ghép hoặc báo Sales (Codex).
			try:
				_doi_soat_mot(r, dons, gan)
			except Exception:
				frappe.db.rollback()
				frappe.log_error(title="Don web: doi soat mot ban ghi",
					message="Ban ghi %s\n%s" % (r.get("name"), frappe.get_traceback()))
	except Exception:
		frappe.log_error(title="Don web: doi soat tu dong", message=frappe.get_traceback())


def _doi_soat_mot(r, dons, gan):
	"""Ghép một bản ghi Chờ đối soát với đơn Pancake, hoặc báo Sales khi quá giờ."""
	snap = json.loads(r.get("snapshot") or "{}")
	hang = [{"variation_id": m.get("ma"), "quantity": m.get("sl")} for m in snap.get("mon") or []]
	o, _ly_do = ghep_don_pancake(r["dien_thoai"], _unix(r["creation"]), hang, dons, gan)
	if o:
		d = frappe.get_doc(DOCTYPE, r["name"])
		d.trang_thai = "Da nhan"
		d.pancake_id = str(o.get("id") or "")
		d.pancake_display_id = str(o.get("display_id") or o.get("id") or "")
		d.ly_do = "doi_soat_tu_dong"
		d.save(ignore_permissions=True)
		gan.update([d.pancake_id, d.pancake_display_id])
		frappe.db.commit()
		return
	if not r.get("da_bao_sales_luc") and get_datetime(r["creation"]) <= add_to_date(now_datetime(), minutes=-PHUT_BAO_SALES):
		_bao_sales(r)


def _bao_sales(r):
	"""Báo nhóm Sales qua Lark (anh Việt chọn Lark 25/09/2026). Chỉ báo một lần
	khi đã gửi được; trả True khi Lark nhận."""
	from vagabond.gui_thu import ban_webhook

	url = str(cfg_o("webhook_don_web") or "").strip()
	if not url:
		# Chưa cấu hình webhook thì chưa coi là đã báo: điền URL xong nhịp sau
		# sẽ báo các bản ghi còn treo.
		return False
	cau = soan_tin_sales(r, frappe.utils.get_url_to_form(DOCTYPE, r["name"]))
	if not ban_webhook(cau, url=url):
		frappe.log_error(title="Don web: chua bao duoc nhom Sales qua Lark",
			message="Ban ghi %s. Kiem tra webhook nhom Sales don web. Se thu lai nhip sau." % r["name"])
		return False
	# Chỉ đóng dấu SAU khi Lark nhận, để lỗi mạng hay webhook sai còn được
	# thử lại ở nhịp sau, không tắt vĩnh viễn lối người xử lý (Codex).
	frappe.db.set_value(DOCTYPE, r["name"], "da_bao_sales_luc", now_datetime(), update_modified=False)
	frappe.db.commit()
	return True


def kiem_ban_ghi(doc):
	if doc.trang_thai not in TRANG_THAI:
		frappe.throw("Chọn một trạng thái hợp lệ cho đơn web.")
	if doc.is_new():
		return
	cu = doc.get_doc_before_save()
	if not cu:
		return
	may = bool(doc.flags.ignore_permissions)
	if not may:
		for o in KHONG_DOI:
			if not gia_tri_giong(cu.get(o), doc.get(o)):
				frappe.throw("Ô %s do máy ghi lúc khách gửi đơn, không sửa tay được. Ghi ghi chú vào ô Lý do." % doc.meta.get_label(o))
	if not chuyen_hop_le(cu.trang_thai, doc.trang_thai, doc.pancake_display_id, may):
		frappe.throw(
			"Không chuyển được từ %s sang %s. Đơn chờ đối soát: điền Mã đơn Pancake rồi chọn Đã nhận; "
			"đơn không làm nữa: chọn Đã huỷ." % (NHAN_TRANG_THAI.get(cu.trang_thai), NHAN_TRANG_THAI.get(doc.trang_thai)))


def sau_khi_luu(doc):
	"""Sales ghép tay xong (Đã nhận có mã Pancake) thì tạo luôn yêu cầu hoá đơn công ty."""
	if doc.trang_thai == "Da nhan" and doc.pancake_display_id and not doc.hoa_don_cong_ty:
		try:
			luu_hoa_don_cong_ty(doc)
		except Exception:
			frappe.log_error(title="Don web: chua tao duoc yeu cau hoa don", message=frappe.get_traceback())

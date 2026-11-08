# -*- coding: utf-8 -*-
"""Phần THUẦN của thanh toán ngay trên web cho đơn đặt bánh (v638).

Anh Việt 04/11/2026: khách đặt bánh trên web phải thanh toán NGAY trên web,
không phải nhắn Zalo chờ Sales gửi hướng dẫn. Trước bản này biên nhận ghi
"Chúng tôi chưa thu tiền ở bước này", câu cảnh báo ở bước đặt hứa "link OnePay /
VietQR sau xác nhận, 15 phút, quá hạn tự huỷ" mà máy chủ không làm gì cả.

Bốn cách ở bước đặt bánh:
  cash  tiền mặt khi nhận bánh (tại quầy hoặc trả người giao). Không thu online.
  card  thẻ tín dụng, ghi nợ quốc tế qua cổng OnePay (vpc_CardList=INTERNATIONAL).
  atm   thẻ ATM nội địa Napas qua cổng OnePay (vpc_CardList=DOMESTIC).
  bank  chuyển khoản mã VietQR đúng số tiền; máy tự xác nhận khi SePay báo tiền về.

Tệp này KHÔNG import Frappe: trang_khach (thuần) và don_web (phần thuần) dùng
chung các nhãn và phép tính tiền ở đây. Phần chạm hệ ở thanh_toan_web.py.
"""

import json
import re

PT_HOP_LE = ("bank", "card", "atm", "cash")
PT_MAC_DINH = "bank"
# Cách nào đi qua cổng OnePay, và loại thẻ gửi cổng (vpc_CardList).
CARD_LIST = {"card": "INTERNATIONAL", "atm": "DOMESTIC"}

# MỘT nguồn cho chữ cách thanh toán trên biên nhận (câu nghiệp vụ máy chủ trả,
# trang_khach.GIA_TRI_BIEN_NHAN đổi thành nhãn Editor theo bảng này).
NHAN_PT = {
	"bank": ("Chuyển khoản (mã VietQR)", "bien_nhan_chuyen_khoan"),
	"card": ("Thẻ tín dụng, ghi nợ quốc tế", "bien_nhan_the_qt"),
	"atm": ("Thẻ ATM nội địa", "bien_nhan_the_atm"),
	"cash": ("Tiền mặt khi nhận bánh", "bien_nhan_tien_mat"),
}
# Đơn cũ trước v638 ghi "card" mà chưa tách quốc tế, nội địa: vẫn đọc như thẻ quốc tế.

# Phương thức thanh toán (Mode of Payment) mà tiền online của đơn web đi vào.
PT_SO = {"bank": "Chuyển khoản", "card": "OnePay", "atm": "OnePay"}
# Codex PR #541 vòng 2: khách trả một phần chuyển khoản, phần còn lại bằng thẻ
# thì cách thu là "Nhiều cách"; hoá đơn để Sales chọn, Pancake ghi riêng từng ô.
CACH_NHIEU = "Nhiều cách"
NHAN_CACH_THU = {"Chuyển khoản": "Chuyển khoản", "OnePay": "Thẻ qua OnePay",
	CACH_NHIEU: "chuyển khoản và thẻ qua OnePay"}
# Loại dòng trong nhật ký giao dịch của đơn (vgb_tt_ma_gd) -> cách thu.
LOAI_CACH = {"ck": "Chuyển khoản", "the": "OnePay"}

TT_DA_THU = "Da thu"
TT_THIEU = "Thu thieu"

RE_TEN_DW = re.compile(r"^DW-([0-9]{4})-([0-9]{5})$")
RE_MA_DW = re.compile(r"^DW[0-9]{9}$")


def chuan_pt(v, the_dung=True):
	"""Cách thanh toán khách gửi lên. Giá trị lạ ép về chuyển khoản; cổng thẻ
	đang tắt (the_dung=False) thì hai cách thẻ cũng về chuyển khoản, vì trang
	khách có thể còn giữ danh sách cũ. THUẦN."""
	x = str(v or "").strip().lower()
	if x not in PT_HOP_LE:
		return PT_MAC_DINH
	if x in CARD_LIST and not the_dung:
		return PT_MAC_DINH
	return x


def nhan_pt(v):
	"""Câu cách thanh toán cho biên nhận. THUẦN."""
	return NHAN_PT.get(str(v or "").strip().lower(), NHAN_PT[PT_MAC_DINH])[0]


def chuan_gioi_thieu(v):
	"""Mã giới thiệu là số điện thoại nhân viên: chỉ giữ chữ số, 8 đến 12 số,
	sai thì bỏ (rỗng). THUẦN."""
	so = "".join(ch for ch in str(v or "") if ch.isdigit())
	return so if 8 <= len(so) <= 12 else ""


def dinh_tien(n):
	"""1250000 -> "1.250.000 đ". THUẦN."""
	return "{:,}".format(int(round(float(n or 0)))).replace(",", ".") + " đ"


def tien_don(tien_banh, giam, phi):
	"""MỘT phép tính tiền của đơn web cho biên nhận, số thu online, cổng thẻ và
	đối soát (ca kiểm chốt không chỗ nào tự tính). THUẦN.

	`phi` là dict quyết phí giao (don_web.quyet_phi_giao) đã lưu trong ảnh chụp.
	  tong     tổng khách trả; None khi phí giao chưa rõ (Ahamove không báo).
	  online   số thu ngay trên web: bằng tổng khi phí đã rõ (kể cả tự lấy,
	           miễn phí giao); phí chưa rõ thì chỉ tiền bánh sau ưu đãi, phí giao
	           khách trả khi nhận (Pancake tự tính COD phần còn lại).
	  phi_sau  True khi phí giao trả khi nhận bánh."""
	phi = phi or {}
	tien_banh = int(round(float(tien_banh or 0)))
	giam = min(max(int(round(float(giam or 0))), 0), tien_banh)
	sau_giam = tien_banh - giam
	tt = phi.get("trang_thai") or ""
	phi_khach = phi.get("phi_khach")
	try:
		phi_khach = int(round(float(phi_khach))) if phi_khach not in (None, "") else None
	except (TypeError, ValueError):
		phi_khach = None
	if tt in ("tu_lay", "mien_phi"):
		tong = sau_giam
	elif tt == "chinh_xac" and phi_khach and phi_khach > 0:
		tong = sau_giam + phi_khach
	else:
		tong = None
	return {"tien_banh": tien_banh, "giam": giam, "sau_giam": sau_giam, "trang_thai_phi": tt,
		"phi_khach": phi_khach, "tong": tong, "online": tong if tong is not None else sau_giam,
		"phi_sau": tong is None}


def tien_ban_ghi(ban_ghi, snapshot):
	"""tien_don đọc từ bản ghi Don Web và ảnh chụp lúc gửi đơn. THUẦN."""
	b = ban_ghi or {}
	snap = snapshot or {}
	phi = dict(snap.get("phi") or {})
	if not phi.get("trang_thai") and b.get("trang_thai_phi"):
		phi["trang_thai"] = b.get("trang_thai_phi")
	uu = snap.get("uu_dai") or {}
	return tien_don(b.get("tien_banh"), uu.get("giam"), phi)


def so_tien_online(ban_ghi, snapshot):
	"""Số tiền phải trả online của một đơn web. THUẦN, mọi nơi gọi hàm này."""
	return tien_ban_ghi(ban_ghi, snapshot)["online"]


def ma_dw(ten):
	"""DW-2611-00123 -> DW261100123 (mã giao dịch, nội dung chuyển khoản). THUẦN."""
	return re.sub(r"[^A-Z0-9]", "", str(ten or "").upper())


def ten_dw(ma):
	"""DW261100123 -> DW-2611-00123. Sai dạng thì rỗng. THUẦN."""
	m = re.fullmatch(r"DW([0-9]{4})([0-9]{5})", str(ma or "").strip().upper())
	return "DW-%s-%s" % m.groups() if m else ""


def la_ma_dw(ma):
	return bool(RE_MA_DW.match(str(ma or "").strip().upper()))


def _ma_hien_hop_le(did):
	return bool(re.fullmatch(r"[A-Za-z0-9]{3,20}", str(did or "").strip()))


def noi_dung_ck(shop_id, ten, did):
	"""Nội dung chuyển khoản in trên mã VietQR. THUẦN.

	Phải là chuỗi mà bộ khớp sẵn có `ban_hang._sepay_theo_don` nhận ra, để chốt
	chặn ghi sổ hoá đơn Chuyển khoản (`_soat_sepay`) chạy không phải sửa: đơn
	đã có mã Pancake số thì mạch S<shop>O<mã>T, mã chữ thì chính mã đó đứng
	riêng. Luôn nối thêm mã Don Web bỏ gạch: đơn chưa vào Pancake (đẩy lỗi) chỉ
	có mã này, và khách đã chuyển theo nội dung cũ thì vẫn khớp được."""
	phan = []
	did = str(did or "").strip()
	shop = str(shop_id or "").strip()
	if did.isdigit() and shop.isdigit():
		phan.append("S%sO%sT" % (shop, did))
	elif did and not did.isdigit() and _ma_hien_hop_le(did):
		phan.append(did.upper())
	phan.append(ma_dw(ten))
	return " ".join(phan)


def mau_khop(shop_id, ten, did):
	"""Biểu thức sơ lọc cho câu SQL REGEXP (chỉ chữ và số, không dấu nhìn quanh
	MariaDB không hỗ trợ). Lọc thật bằng mo_ta_khop. THUẦN."""
	phan = []
	did = str(did or "").strip()
	shop = str(shop_id or "").strip()
	if did.isdigit() and shop.isdigit():
		phan.append("S%sO%sT" % (shop, did))
	elif did and not did.isdigit() and _ma_hien_hop_le(did):
		phan.append(did.upper())
	if ma_dw(ten):
		phan.append(ma_dw(ten))
	return "|".join(phan)


def mo_ta_khop(mo_ta, shop_id, ten, did):
	"""Một dòng sao kê có phải tiền của đơn web này không. THUẦN.

	Cùng luật với ban_hang._sepay_theo_don: mạch S<shop>O<mã>T với mã số (T chặn
	"S1O9185T" ăn nhầm "S1O91853T"), mã chữ và mã Don Web phải đứng riêng
	(không dính chữ, số hai bên) để DW261100123 không ăn nhầm DW2611001234."""
	s = str(mo_ta or "")
	did = str(did or "").strip()
	shop = str(shop_id or "").strip()
	if did.isdigit() and shop.isdigit() and re.search(r"S%sO%sT" % (re.escape(shop), re.escape(did)), s, re.I):
		return True
	ma = []
	if did and not did.isdigit() and _ma_hien_hop_le(did):
		ma.append(did)
	if ma_dw(ten):
		ma.append(ma_dw(ten))
	return any(re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(m), s, re.I) for m in ma)


RE_DW_TRONG = re.compile(r"(?<![0-9A-Za-z])(DW[0-9]{9})(?![0-9A-Za-z])", re.I)


def ma_don_khac(mo_ta, shop_id, ten, did):
	"""Mã của đơn KHÁC có trong nội dung chuyển khoản (mã Don Web, mạch
	S<shop>O<mã>T). THUẦN. Nội dung đúng của chính đơn này (S..O<mã>T kèm mã
	Don Web của nó) ra rỗng."""
	s = str(mo_ta or "")
	cua = ma_dw(ten)
	ra = {m.upper() for m in RE_DW_TRONG.findall(s) if m.upper() != cua}
	shop = str(shop_id or "").strip()
	did = str(did or "").strip()
	if shop.isdigit():
		for x in re.findall(r"S%sO([0-9]+)T" % re.escape(shop), s, re.I):
			if x != did:
				ra.add("S%sO%sT" % (shop, x))
	return sorted(ra)


def tong_khop(gds, shop_id, ten, did, da_dung=None):
	"""Cộng tiền các dòng sao kê khớp đơn. Mỗi dòng tính một lần (theo tên), chỉ
	tiền vào. THUẦN. Trả {"nhan", "gd": [{"gd","ma","so"}], "mo_ho", "da_dung"}.

	Codex PR #541: một giao dịch mang mã của nhiều đơn thì KHÔNG tự cộng cho đơn
	nào (đưa vào "mo_ho" để Sales đối soát tay); giao dịch đã được đơn khác ghi
	nhận (da_dung: tên các dòng sao kê đơn khác đã giữ) cũng không cộng lần hai."""
	nhan, ds, da, mo_ho, bo = 0.0, [], set(), [], []
	da_dung = set(da_dung or [])
	for g in gds or []:
		ten_gd = str(g.get("name") or "")
		if not ten_gd or ten_gd in da:
			continue
		try:
			so = float(g.get("deposit") or 0) - float(g.get("withdrawal") or 0)
		except (TypeError, ValueError):
			continue
		if so <= 0 or not mo_ta_khop(g.get("description"), shop_id, ten, did):
			continue
		da.add(ten_gd)
		khac = ma_don_khac(g.get("description"), shop_id, ten, did)
		if khac:
			mo_ho.append({"gd": ten_gd, "ma_khac": khac})
			continue
		if ten_gd in da_dung:
			bo.append(ten_gd)
			continue
		nhan += so
		ds.append({"gd": ten_gd, "ma": str(g.get("reference_number") or "").strip(), "so": so})
	return {"nhan": nhan, "gd": ds, "mo_ho": mo_ho, "da_dung": bo}


def tin_ck_nhieu_don(ten, did, ma_khac):
	"""(tiêu đề, dòng) tin cho Sales khi một giao dịch mang mã nhiều đơn. Không
	ghi số tiền (luật tin bộ phận Bán hàng v613). THUẦN."""
	ma = str(did or "").strip() or str(ten or "")
	return ("Đơn web %s: một lần chuyển khoản ghi mã của nhiều đơn" % ma, [
		"Nội dung chuyển khoản có cả mã %s." % ", ".join(ma_khac),
		"Máy không tự ghi đơn nào đã thu. Sales kiểm sao kê, hỏi khách khoản này trả cho đơn nào rồi ghi tay trên Pancake.",
	])


def xet_thu(so_can, so_nhan):
	"""Trạng thái thu: đủ (lệch dưới 1 đồng), một phần, hay chưa. THUẦN.
	Thiếu tiền KHÔNG bao giờ được báo là đủ."""
	so_can = float(so_can or 0)
	so_nhan = float(so_nhan or 0)
	if so_can > 0 and so_nhan >= so_can - 1:
		return TT_DA_THU
	if so_nhan > 0.5:
		return TT_THIEU
	return ""


def doc_ds_gd(chuoi):
	try:
		v = json.loads(chuoi or "[]")
		return v if isinstance(v, list) else []
	except (TypeError, ValueError):
		return []


def khoi_bien_nhan(pt, tien, tt_thu, da_thu, cach_thu, huy):
	"""Khối thanh toán của biên nhận (phần thuần, chưa có tài khoản, mã QR, khoá
	trang thẻ). `tien` là kết quả tien_don. THUẦN.

	trang_thai: tien_mat | cho | thieu | da_thu | huy."""
	pt = chuan_pt(pt)
	so = int(tien.get("online") or 0)
	da_thu = float(da_thu or 0)
	if huy:
		tt = "huy"
	elif tt_thu == TT_DA_THU:
		tt = "da_thu"
	elif pt == "cash":
		tt = "tien_mat"
	elif tt_thu == TT_THIEU:
		tt = "thieu"
	else:
		tt = "cho"
	con = max(0, so - int(round(da_thu))) if tt in ("cho", "thieu") else 0
	return {
		"cach": pt,
		"trang_thai": tt,
		"so": so,
		"so_chu": dinh_tien(so),
		"con": con,
		"con_chu": dinh_tien(con),
		"phi_sau": bool(tien.get("phi_sau")) and pt != "cash",
		"da_thu_chu": dinh_tien(da_thu) if da_thu > 0.5 else "",
		"cach_thu": NHAN_CACH_THU.get(cach_thu or "", cach_thu or ""),
	}


def so_theo_cach(ds):
	"""{cách thu: số tiền} cộng từ nhật ký giao dịch của đơn. THUẦN."""
	ra = {}
	for g in ds or []:
		c = LOAI_CACH.get((g or {}).get("loai"))
		if not c:
			continue
		try:
			so = float(g.get("so") or 0)
		except (TypeError, ValueError):
			continue
		ra[c] = ra.get(c, 0.0) + so
	return ra


def cach_tu_ds(ds, mac=""):
	"""Cách thu của đơn theo nhật ký: một cách thì đúng cách đó, hai cách thì
	CACH_NHIEU, chưa có dòng có loại thì `mac`. THUẦN."""
	c = sorted(k for k, v in so_theo_cach(ds).items() if v > 0.5)
	if len(c) > 1:
		return CACH_NHIEU
	return c[0] if c else mac


def pt_cho_hoa_don(rec):
	"""Phương thức và mã tham chiếu cho hoá đơn đồng bộ từ Pancake của một đơn web
	đã trả online. Chỉ khi đã thu ĐỦ tổng đơn (phí giao đã rõ); trả một phần (phí
	giao trả khi nhận) thì để Sales chọn như đơn nhiều cách trả. THUẦN."""
	r = rec or {}
	if r.get("vgb_tt_trang_thai") != TT_DA_THU or r.get("phi_sau"):
		return "", ""
	pt = str(r.get("vgb_tt_cach") or "")
	if pt not in PT_SO.values():
		return "", ""
	ds = doc_ds_gd(r.get("vgb_tt_ma_gd"))
	if cach_tu_ds(ds, pt) != pt:
		# Nhật ký có cả chuyển khoản lẫn thẻ (hay khác cách ghi trên đơn): không
		# gán một phương thức cho cả tổng, Sales chọn như đơn nhiều cách trả.
		return "", ""
	ma = ""
	if pt == "OnePay":
		ma = next((str(g.get("gd") or "") for g in ds if g.get("loai") in ("the", None, "")), "")
	return pt, ma


# Ô tiền trên đơn Pancake mà máy ghi số khách đã trả. Chuyển khoản ghi ô
# transfer_money (Pancake trả về ô này, ban_hang.PT_KENH đọc được).
#
# Thẻ: v645 (anh Việt 08/11/2026, đơn 97077, 97098, 97113). Trước đây ghi RIÊNG
# ô prepaid thì Pancake tự xếp cả khoản vào Tiền mặt (lịch sử đơn: cash 0 thành
# số đã trả, người sửa là khoá API), rồi hoá đơn đồng bộ về ERP đoán ra Tiền
# mặt. Khi khách trả thẻ qua link thanh toán của chính Pancake, lịch sử đơn ghi
# ô charged_by_onepay CÙNG prepaid (đơn 96844, 97059). Nay ghi đúng cặp đó. Ô
# charged_by_onepay không có trong dữ liệu Pancake trả về khi đọc (đo 15/08 và
# 08/11/2026), nên đọc lại chỉ soát được prepaid và cash: xem the_vao_tien_mat.
O_THE = "charged_by_onepay"
O_PANCAKE = {"Chuyển khoản": "transfer_money", "OnePay": O_THE}


def _so_o(don, o):
	try:
		return float((don or {}).get(o) or 0)
	except (TypeError, ValueError):
		return 0.0


def than_pancake(cach_thu, so, don):
	"""Thân PUT ghi số đã trả lên đơn Pancake, hoặc None khi ô đó đã đủ (Sales
	ghi tay trước, hay lượt trước đã ghi). Không bao giờ hạ số đang có. THUẦN."""
	o = O_PANCAKE.get(cach_thu or "")
	if not o:
		return None
	try:
		so = int(round(float(so or 0)))
	except (TypeError, ValueError):
		return None
	if so <= 0:
		return None
	if o == O_THE:
		# Đọc không thấy ô thẻ: đã đủ khi prepaid đã mang số và Pancake không
		# xếp nó vào Tiền mặt (lượt trước ghi đúng, hay Sales đã chọn tay).
		cu = _so_o(don, "prepaid")
		if cu >= so - 0.5 and _so_o(don, "cash") < 0.5:
			return None
		return {O_THE: so, "prepaid": max(int(round(cu)), so)}
	if _so_o(don, o) >= so - 0.5:
		return None
	return {o: so}


def than_pancake_ds(ds, cach_thu, so, don):
	"""Thân PUT theo từng cách thu trong nhật ký: chuyển khoản vào transfer_money,
	thẻ vào charged_by_onepay kèm prepaid, mỗi ô đúng số của cách đó. Nhật ký chưa có loại (bản ghi cũ)
	thì như than_pancake. THUẦN."""
	theo = so_theo_cach(ds)
	if not theo:
		return than_pancake(cach_thu, so, don)
	than = {}
	for c in sorted(theo):
		t = than_pancake(c, theo[c], don)
		if t:
			than.update(t)
	return than or None


def da_ghi_pancake(don_doc_lai, than):
	"""Đọc lại đơn sau PUT: ô đã mang đúng số chưa (Pancake trả 200 mà bỏ qua ô
	thì vẫn là chưa ghi). Ô thẻ không đọc lại được nên soát qua prepaid đi
	cùng nó. THUẦN."""
	for o, so in (than or {}).items():
		if o == O_THE:
			continue
		try:
			if float((don_doc_lai or {}).get(o) or 0) < float(so) - 0.5:
				return False
		except (TypeError, ValueError):
			return False
	return bool(than)


def the_vao_tien_mat(truoc, sau, than):
	"""Sau PUT có ô thẻ: Pancake vẫn xếp khoản thẻ vào Tiền mặt (cash tăng đúng
	bằng số thẻ) thì COD đã giảm đúng nhưng hình thức sai, Sales phải đổi tay.
	THUẦN."""
	so = (than or {}).get(O_THE)
	if not so:
		return False
	return _so_o(sau, "cash") - _so_o(truoc, "cash") >= float(so) - 0.5


CAU_PANCAKE = {
	"da_ghi": "Đã ghi số đã trả lên đơn Pancake, COD giảm tương ứng.",
	"tien_mat": ("Đã ghi số đã trả lên đơn Pancake (COD giảm đúng) nhưng Pancake xếp vào Tiền mặt: "
		"Sales đổi hình thức thanh toán của đơn sang OnePay trên Pancake."),
	"da_co": "Đơn Pancake đã có sẵn số đã trả.",
	"tat": "Cài đặt đang tắt ghi lên Pancake: Sales ghi tay số đã trả trên đơn Pancake.",
	"cho_ma_don": "Đơn chưa vào Pancake: khi tạo hoặc ghép đơn, Sales ghi số đã trả để người giao không thu lại.",
	"loi": "CHƯA ghi được lên Pancake: Sales ghi tay số đã trả trên đơn Pancake để người giao không thu lại.",
}


def tin_da_tra(ten, ma_don, cach_thu, phi_sau, ket_qua_pancake):
	"""Tin Zalo nhóm Sales khi khách trả online thành công (bh_don_web_da_tra).
	Trả (tiêu đề, dòng). THUẦN.

	KHÔNG mang số tiền: luật v613 (anh Việt 27/10/2026) cấm tiền trong tin bộ phận
	Bán hàng, và cửa ghi sổ tin (kenh_zalo.bo_dong_tien) bỏ cả dòng có tiền. Số đã
	trả nằm trên bản ghi đơn web và trên đơn Pancake (COD đã giảm)."""
	tieu_de = "Đơn web %s đã thanh toán online" % (ma_don or ten)
	cach = NHAN_CACH_THU.get(cach_thu, cach_thu or "")
	dong = ["Mã yêu cầu %s%s." % (ten, (", đơn Pancake %s" % ma_don) if ma_don else "")]
	if phi_sau:
		dong.append("Khách đã trả tiền bánh qua %s; phí giao khách trả khi nhận." % cach)
	else:
		dong.append("Khách đã trả đủ qua %s; người giao không thu thêm." % cach)
	if CAU_PANCAKE.get(ket_qua_pancake):
		dong.append(CAU_PANCAKE[ket_qua_pancake])
	return tieu_de, dong

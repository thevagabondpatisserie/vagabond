# -*- coding: utf-8 -*-
"""Gọi món tại bàn qua mã QR (v638, anh Việt duyệt 04/11/2026).

Vì sao có tệp này
-----------------
Khách ngồi bàn ở District 1 hay NVHTN muốn gọi thêm ly trà thì phải đứng dậy
ra quầy, quầy đông là chờ. Anh Việt duyệt luồng: mỗi bàn dán một mã QR, khách
quét là vào tab TẠI QUẦY của trang đặt bánh ở chế độ gọi món của ĐÚNG quầy đó,
chọn món (đồ uống có đá, đường), bấm Gọi món. Quầy thấy dải "N đơn gọi món tại
bàn đang chờ nhận" trên màn Tính tiền, bấm Nhận đơn là máy thêm món vào phiếu
tạm tính của bàn và in phiếu pha chế. Thu tiền, chốt, ghi sổ đi ĐÚNG luồng tạm
tính sẵn có, không có luồng tiền mới.

Ba điều phải giữ
----------------
1. Máy chủ chốt số (QT-19). Giá lấy từ bảng giá điểm bán (giá riêng của điểm,
   không có thì giá chung), không bao giờ lấy giá trình duyệt gửi. Bánh trên
   tủ không cho gọi quá số "còn" của bảng kiểm kho, trừ cả đơn đang chờ nhận.
2. Mã QR là link ký HMAC bằng khoá mã hoá của site cho cặp (điểm, bàn), không
   có hạn: tờ QR dán bàn sống hàng năm. Đoán điểm hay đổi số bàn trên link mà
   không có khoá đúng thì chỉ xem như trang thường, không gọi được.
3. Một đơn chỉ được nhận MỘT lần dù hai thu ngân bấm cùng lúc: khoá hàng bản
   ghi (đọc hiện tại, for update), đổi trạng thái rồi commit ngay, sau đó mới
   lập phiếu (bài học PR476, v631: đọc sau khoá phải là đọc hiện tại).

Không làm gì với dữ liệu quá khứ. Phiếu tạm tính là bill NHÁP, chưa ghi sổ.
"""

import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta

from vagabond import so_do_ban

# ------------------------------------------------------------- phần thuần

DT = "Vagabond Goi Mon Ban"
# Nguồn đơn ghi trên hoá đơn tạm tính lập từ QR. KHÔNG nằm trong danh sách
# nguồn của điểm bán (không hiện thành nút trên màn Tính tiền). Phép chọn
# phương thức thanh toán đọc nó như "Tại chỗ" qua ban_hang.NGUON_CU.
NGUON_QR = "QR tại bàn"
NGUON_TAO = "Tại chỗ"

# Nhóm món nước của quầy. MỘT nguồn: màn Tính tiền đọc lại qua cấu hình bán
# hàng (cau_hinh_ban_hang.nhom_nuoc), bảng kiểm kho và tab Tại quầy dùng thẳng.
NHOM_NUOC = ("Trà", "Cà phê", "Matcha", "Cacao", "Ice Cream - Kem")
NHAN_DO_UONG = "Đồ uống"
# v639 (anh Việt duyệt mẫu 05/11/2026): topping chọn kèm ly nước (thạch, trân
# châu, sữa yến mạch) là MÓN trong nhóm này của danh mục, có giá riêng; đi
# vào hoá đơn thành dòng riêng ngay sau ly nước. Topping bánh không bán tại bàn.
NHOM_TOPPING = "Topping cho món nước"
TOPPING_TOI_DA_MOI_LY = 5
# Món đóng sẵn (chai, lon, hũ, set trà, hộp) không pha nên không hỏi đá, đường,
# cũng không thêm topping (Codex/anh Việt 05/11: Kombucha chai vẫn hỏi sữa yến
# mạch). Đọc theo TÊN món vì danh mục không có cờ riêng; quản lý muốn khác thì
# khai nhóm món cho từng nhóm lựa chọn ở Cài đặt bán hàng.
# "Chai" đứng đầu tên là trà chai (Chai Latte), không phải cái chai: chỉ bắt
# "chai", "lon", "hũ", "hộp" sau dấu phẩy hoặc đi kèm dung tích (lon 330).
MAU_KHONG_PHA = re.compile(r"(?:,\s*(?:chai|lon|hũ|hu|hộp|hop)\b|\b(?:chai|lon)\s*\d|\bset\s+tr[àa]\b)", re.I)

# v639: khách bấm chuông gọi nhân viên (nút dưới Nhắn Zalo khi mở từ QR bàn).
DT_TG = "Vagabond Goi Nhan Vien"
LY_DO_GOI = ("Gọi nhân viên tới bàn", "Xin tính tiền", "Xin thêm nước lọc, đá", "Xin thêm dao, nĩa, khăn giấy", "Việc khác")
TG_CHO = "Chờ xử lý"
TG_XONG = "Đã xong"
TG_HET_HAN = "Hết hạn"
TRANG_THAI_TG = (TG_CHO, TG_XONG, TG_HET_HAN)
PHUT_TG_HET_HAN = 30
GOI_TOI_DA_MOI_BAN = 3
PHUT_DEM_GOI = 10
DAI_CHI_TIET = 120

TT_CHO = "Chờ nhận"
TT_NHAN = "Đã nhận"
TT_TU_CHOI = "Từ chối"
TT_HET_HAN = "Hết hạn"
TRANG_THAI = (TT_CHO, TT_NHAN, TT_TU_CHOI, TT_HET_HAN)

PHUT_HET_HAN = 10
CHO_TOI_DA_MOI_BAN = 3
CHO_TOI_DA_MOI_DIEM = 30
BAN_TOI_DA = 99
TO_QR_TOI_DA = 99
SL_TOI_DA = 20
DONG_TOI_DA = 30
DAI_GHI_CHU = 300
DAI_TEN = 40
# Không đọc được giờ mở cửa trên thẻ Cửa hàng (marketing chưa điền) thì dùng
# khung này, để mã QR chụp lại mang về nhà lúc nửa đêm không réo nhóm Zalo.
GIO_MAC_DINH = "Mỗi ngày 7:00 - 22:00"
DUONG_TRANG = "/banh"
# Câu nói đơn đã có người xử lý (thu ngân thứ hai bấm sau).
CAU_DA_XU_LY = {TT_NHAN: "đã được nhận", TT_TU_CHOI: "đã bị từ chối", TT_HET_HAN: "đã hết hạn"}
LY_DO_TU_CHOI = ("Hết món", "Quầy quá đông", "Bàn không có khách", "Đơn trùng", "Khác")


def la_do_uong(nhom):
	"""Nhóm món này có phải món nước của quầy không. THUẦN."""
	return str(nhom or "").strip() in NHOM_NUOC


def chuan_diem(diem):
	"""Mã điểm bán trên link: chữ hoa, chỉ chữ và số. THUẦN."""
	return re.sub(r"[^A-Z0-9]", "", str(diem or "").upper())[:20]


def chuan_ban(ban):
	"""Tên bàn chuẩn (chuỗi), sai thì None. Nhận "5", 5, " 05 " (ra "5") và tên
	theo khu "a01", "VIP2" (ra "A1", "VIP2"). THUẦN.

	v647 (anh Việt 10/11/2026): bàn đặt tên theo khu. Bàn chỉ có số giữ đúng
	chuỗi cũ ("5"), nên khoá HMAC và link QR bàn số in trước v647 không đổi."""
	return so_do_ban.chuan_ten_ban(ban)


def khoa_ban(bi_mat, diem, ban):
	"""Khoá của một bàn: HMAC (điểm, bàn) bằng bí mật của site, 16 ký tự hex.
	Không lưu ở đâu, tính lại được, không có hạn. THUẦN."""
	if not bi_mat:
		raise ValueError("Site chưa có khoá mã hoá.")
	n = chuan_ban(ban)
	if n is None:
		raise ValueError("Số bàn không hợp lệ.")
	chuoi = "goi-mon-ban:%s:%s" % (chuan_diem(diem), n)
	return hmac.new(str(bi_mat).encode("utf-8"), chuoi.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def dung_khoa(bi_mat, diem, ban, k):
	"""Khoá trên link có đúng của (điểm, bàn) không. So thời gian hằng. THUẦN."""
	if not isinstance(k, str) or not re.fullmatch(r"[0-9a-f]{16}", k or ""):
		return False
	if chuan_ban(ban) is None or not chuan_diem(diem):
		return False
	try:
		return hmac.compare_digest(k, khoa_ban(bi_mat, diem, ban))
	except ValueError:
		return False


def duong_qr(diem, ban, k):
	"""Đường tương đối in thành QR. Tab TẠI QUẦY mở thẳng. THUẦN."""
	return "%s?diem=%s&ban=%s&k=%s#/in-store" % (DUONG_TRANG, chuan_diem(diem), chuan_ban(ban), k)


def ds_ban(tu, den):
	"""Danh sách bàn số cần in, từ tu tới den (đảo lại nếu gõ ngược). THUẦN.
	Trả [] khi số bàn sai; cắt ở TO_QR_TOI_DA tờ một lần in."""
	a, b = chuan_ban(tu), chuan_ban(den)
	if a is None or b is None or not (so_do_ban.la_so(a) and so_do_ban.la_so(b)):
		return []
	a, b = int(a), int(b)
	if a > b:
		a, b = b, a
	return [str(n) for n in range(a, min(b, a + TO_QR_TOI_DA - 1) + 1)]


def ds_ban_chon(ban, so_do):
	"""v647: các bàn người quản lý tích để in, theo thứ tự sơ đồ, bỏ trùng.
	Bàn theo khu phải có trong sơ đồ của điểm (co_ban). THUẦN.
	Trả (danh sách, [tên sai])."""
	if isinstance(ban, str):
		ban = [x for x in re.split(r"[\s,;]+", ban) if x]
	ra, sai = [], []
	for x in ban or []:
		t = chuan_ban(x)
		if t is None or not so_do_ban.co_ban(so_do, t):
			sai.append(str(x))
		elif t not in ra:
			ra.append(t)
	thu_tu = {t: i for i, t in enumerate(so_do_ban.ten_ban(so_do))}
	ra.sort(key=lambda t: (thu_tu.get(t, len(thu_tu)), int(re.sub(r"\D", "", t) or 0)))
	return ra[:TO_QR_TOI_DA], sai


def tuy_chon_cho(nhom_mon, ds_tc):
	"""Các nhóm lựa chọn (đá, đường) áp cho một nhóm món. Cùng luật màn Tính
	tiền (posMoTuyChon): nhóm lựa chọn không khai nhóm món là áp mọi món. THUẦN."""
	ra = []
	for n in ds_tc or []:
		ap = n.get("nhom_mon") or []
		if ap and nhom_mon not in ap:
			continue
		lc = [str(x).strip() for x in (n.get("lua_chon") or []) if str(x).strip()]
		if n.get("nhom") and lc:
			ra.append({"nhom": str(n["nhom"]).strip(), "lua_chon": lc})
	return ra


def khong_pha(ten):
	"""Món đóng sẵn theo tên (chai, lon, hũ, set trà, hộp): không hỏi đá đường,
	không topping. THUẦN."""
	return bool(MAU_KHONG_PHA.search(str(ten or "")))


def tuy_chon_mon(ten, nhom_mon, ds_tc):
	"""Lựa chọn pha chế của MỘT món: theo nhóm món, trừ món đóng sẵn. THUẦN."""
	return [] if khong_pha(ten) else tuy_chon_cho(nhom_mon, ds_tc)


def mo_ta_ngan(html, dai=200):
	"""Mô tả món trong danh mục (HTML của Item.description) -> một đoạn chữ
	trơn ngắn cho dòng món trên trang khách. THUẦN."""
	s = re.sub(r"<br\s*/?>|</p>|</div>|</li>", " ", str(html or ""), flags=re.I)
	s = re.sub(r"<[^>]+>", "", s)
	s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
		.replace("&lt;", "<").replace("&gt;", ">"))
	s = re.sub(r"\s+", " ", s).strip()
	if len(s) > dai:
		s = s[:dai].rsplit(" ", 1)[0].rstrip(",;:") + "..."
	return s


def loc_topping(rows, gia_diem):
	"""Topping bán kèm ly nước của một điểm: món đang dùng, là hàng bán, đúng
	nhóm Topping cho món nước, có giá (giá điểm thắng giá chung). THUẦN."""
	ra = []
	for r in rows or []:
		ma = str(r.get("item_code") or "").strip()
		if not ma or str(r.get("item_group") or "").strip() != NHOM_TOPPING:
			continue
		if int(r.get("disabled") or 0) or not int(r.get("is_sales_item") if r.get("is_sales_item") is not None else 1):
			continue
		if int(r.get("has_variants") or 0):
			continue
		gia = gia_mon(ma, gia_diem, r.get("standard_rate"))
		if gia <= 0:
			continue
		ra.append({"ma": ma, "ten": r.get("item_name") or ma, "gia": gia})
	ra.sort(key=lambda x: (x["gia"], x["ten"]))
	return ra


def tc_hien(d):
	"""Lựa chọn kèm topping của một dòng, để hiện cho quầy, khách và phiếu pha
	chế: ["Ít đá", "+ Trân châu ô long"]. THUẦN."""
	return (list(d.get("tc") or []) + [mo_ta_thanh_phan(x) for x in (d.get("thanh_phan") or [])]
		+ ["+ " + str(t.get("ten") or "") for t in (d.get("tp") or [])])


def mo_ta_thanh_phan(x):
	"""Một món trong combo để hiện: "2 Trà Lài Đào (M)", món 1 cái thì bỏ số. THUẦN."""
	sl = int(x.get("sl") or 0)
	return (("%d " % sl) if sl > 1 else "") + str(x.get("ten") or x.get("ma") or "")


def combo_ban_duoc(ds_combo, bang):
	"""Combo cố định bày trên trang bàn (v642, anh Việt 06/11/2026: "trang gọi
	món O2O phải đồng bộ được các combo quán đang chạy"). THUẦN.

	ds_combo: [{ma (mã hàng KMCB), ten, gia, goc, mo_ta, anh, dong: [{ma, ten, sl}]}]
	đã qua luật bán của hoá đơn (combo_mon.ly_do_khong_ban). bang: bảng món gọi
	được của điểm (bang_mon) trước khi thêm combo. Món thành phần nào không gọi
	được ở điểm (nước đang tắt, bánh không có trên tủ) thì combo không bày. "con"
	là số bộ gọi được theo bánh còn trên tủ (đồ uống pha theo ly, không giới hạn
	ngoài SL_TOI_DA); 0 bộ thì không bày."""
	ra = []
	for cb in ds_combo or []:
		dong = [x for x in cb.get("dong") or [] if x.get("ma") and int(x.get("sl") or 0) > 0]
		if not dong or int(cb.get("gia") or 0) <= 0:
			continue
		con, du = SL_TOI_DA, True
		for x in dong:
			m = (bang or {}).get(x["ma"])
			if not m or m.get("loai") not in ("nuoc", "banh"):
				du = False
				break
			if m.get("loai") == "banh":
				con = min(con, max(0, int(m.get("con") or 0)) // int(x["sl"]))
		if not du or con <= 0:
			continue
		ra.append({"ma": cb["ma"], "ten": cb.get("ten") or cb["ma"], "gia": int(cb["gia"]), "goc": int(cb.get("goc") or 0),
			"mo_ta": cb.get("mo_ta") or "", "anh": cb.get("anh") or "", "loai": "combo", "con": con,
			"thanh_phan": [{"ma": x["ma"], "ten": x.get("ten") or bang[x["ma"]]["ten"], "sl": int(x["sl"]),
				"loai": bang[x["ma"]]["loai"], "nhom": bang[x["ma"]].get("nhom_goc") or ""} for x in dong]})
	return ra


def dong_phieu_pha(dong):
	"""Dòng món của phiếu pha chế in khi quầy nhận đơn. Combo (v642) tách thành
	từng món thành phần, số lượng nhân theo số bộ, ghi "Combo <tên>" để bếp và
	pha chế làm đúng món, không phải đoán từ tên combo. THUẦN."""
	ra = []
	for x in dong or []:
		if x.get("thanh_phan"):
			for y in x["thanh_phan"]:
				ra.append({"item_code": y["ma"], "ten": y.get("ten") or y["ma"], "qty": int(x["sl"]) * int(y.get("sl") or 0),
					"nhom": y.get("nhom") or "", "tc": [], "gc": "Combo " + str(x.get("ten") or "")})
			continue
		ra.append({"item_code": x["ma"], "ten": x["ten"], "qty": x["sl"], "nhom": x.get("nhom") or "", "tc": tc_hien(x), "gc": ""})
	return ra


def gia_dong(d):
	"""Đơn giá một dòng kể cả topping. THUẦN."""
	return int(d.get("gia") or 0) + sum(int(t.get("gia") or 0) for t in (d.get("tp") or []))


def gia_mon(ma, gia_diem, gia_chung):
	"""Giá bán một món ở một điểm: giá riêng của điểm, không có thì giá chung
	danh mục. Cùng hai nguồn với màn quầy (diem_ban.ap_gia_diem). THUẦN."""
	g = (gia_diem or {}).get(ma)
	try:
		g = float(g) if g else 0.0
	except (TypeError, ValueError):
		g = 0.0
	if g > 0:
		return int(round(g))
	try:
		return int(round(float(gia_chung or 0)))
	except (TypeError, ValueError):
		return 0


def loc_do_uong(rows, gia_diem, tat):
	"""Danh sách đồ uống của một điểm: món đang dùng, là hàng bán, đúng nhóm
	nước, có giá. Món nhóm Topping không vào. THUẦN.

	rows: dòng Item (item_code, item_name, image, standard_rate, item_group,
	disabled, is_sales_item, has_variants); tat: {ma: {"tat", "den_ngay"}}."""
	ra = []
	for r in rows or []:
		ma = str(r.get("item_code") or "").strip()
		if not ma or not la_do_uong(r.get("item_group")):
			continue
		if int(r.get("disabled") or 0) or not int(r.get("is_sales_item") if r.get("is_sales_item") is not None else 1):
			continue
		if int(r.get("has_variants") or 0):
			continue
		gia = gia_mon(ma, gia_diem, r.get("standard_rate"))
		if gia <= 0:
			continue
		t = (tat or {}).get(ma) or {}
		ra.append({
			"ma": ma, "ten": r.get("item_name") or ma, "anh": r.get("image") or "", "gia": gia,
			"nhom_goc": r.get("item_group") or "", "ban_web": 0 if t.get("tat") else 1,
			"den_ngay": t.get("den_ngay") or "",
		})
	ra.sort(key=lambda x: (NHOM_NUOC.index(x["nhom_goc"]) if x["nhom_goc"] in NHOM_NUOC else 99, x["ten"]))
	return ra


def _tc_tu_gui(tc, cho_phep):
	"""Lựa chọn khách gửi -> danh sách chuỗi đã kiểm, theo thứ tự nhóm. Lựa
	chọn không có trong danh mục của món thì báo, không lặng lẽ bỏ. THUẦN."""
	if not tc:
		return []
	if isinstance(tc, list):
		gui = {}
		for x in tc:
			for n in cho_phep:
				if x in n["lua_chon"]:
					gui[n["nhom"]] = x
					break
			else:
				raise ValueError("Lựa chọn \"%s\" không có cho món này. Quý khách chọn lại." % str(x)[:40])
	elif isinstance(tc, dict):
		gui = tc
	else:
		raise ValueError("Lựa chọn của món không đọc được. Quý khách chọn lại.")
	ra = []
	for n in cho_phep:
		v = gui.get(n["nhom"])
		if v in (None, ""):
			continue
		if v not in n["lua_chon"]:
			raise ValueError("Lựa chọn \"%s\" không có cho món này. Quý khách chọn lại." % str(v)[:40])
		# v640: mức mặc định của nhóm ("Bình thường") là pha chuẩn, không ghi lên bill.
		if v == (n.get("mac_dinh") or ""):
			continue
		ra.append(v)
	la = set(gui) - {n["nhom"] for n in cho_phep}
	if any(gui.get(k) not in (None, "") for k in la):
		raise ValueError("Món này không có lựa chọn đó. Quý khách chọn lại.")
	return ra


def chuan_gio(gio, bang):
	"""Giỏ khách gửi -> các dòng đã chuẩn hoá và tạm tính. THUẦN, máy chủ chốt số.

	gio: [{"ma", "sl", "tc": {nhóm: lựa chọn}, "tp": [mã topping]}]
	bang: {ma: {"ten", "gia", "loai" ("nuoc"|"banh"|"topping"), "con" (bánh), "tc": [...]}}
	Giá, tên lấy từ bảng của máy chủ; "gia" khách gửi bị bỏ qua. Cùng món cùng
	lựa chọn cùng topping gộp một dòng. Bánh cộng mọi dòng của mã rồi so số
	còn. Topping (v639) chỉ đi kèm ly nước pha, mỗi ly tối đa 5 thứ, không gọi
	riêng. Sai thì ValueError với câu khách đọc được."""
	if isinstance(gio, str):
		try:
			gio = json.loads(gio or "[]")
		except ValueError:
			raise ValueError("Giỏ món không đọc được. Quý khách tải lại trang.")
	if not isinstance(gio, list) or not gio:
		raise ValueError("Giỏ chưa có món nào.")
	if len(gio) > DONG_TOI_DA:
		raise ValueError("Giỏ quá nhiều dòng. Quý khách gọi làm hai lần.")
	dong, theo_khoa, sl_ma = [], {}, {}
	for x in gio:
		if not isinstance(x, dict):
			raise ValueError("Giỏ món không đọc được. Quý khách tải lại trang.")
		ma = str(x.get("ma") or "").strip()
		m = (bang or {}).get(ma)
		if not m:
			raise ValueError("Có món vừa ngừng bán. Quý khách tải lại trang rồi chọn lại.")
		if m.get("loai") == "topping":
			raise ValueError("%s là topping, chọn kèm một ly nước chứ không gọi riêng." % m["ten"])
		try:
			sl = int(x.get("sl"))
		except (TypeError, ValueError):
			sl = 0
		if sl < 1 or sl > SL_TOI_DA:
			raise ValueError("Số lượng %s phải từ 1 tới %d." % (m["ten"], SL_TOI_DA))
		tc = _tc_tu_gui(x.get("tc"), m.get("tc") or []) if m.get("loai") == "nuoc" else []
		tp = _tp_tu_gui(x.get("tp"), m, bang)
		tp_combo = m.get("thanh_phan") if m.get("loai") == "combo" else None
		khoa = (ma, tuple(tc), tuple(t["ma"] for t in tp))
		if khoa in theo_khoa:
			theo_khoa[khoa]["sl"] += sl
		else:
			d = {"ma": ma, "ten": m["ten"], "sl": sl, "gia": int(m["gia"]), "tc": tc, "loai": m.get("loai") or "banh",
				"nhom": m.get("nhom_goc") or "", "tp": tp}
			if tp_combo is not None:
				# v642: combo mang theo món thành phần để quầy, phiếu pha chế thấy
				# món gì và để giữ bánh trên tủ (sl_dang_cho tách theo thành phần).
				d["thanh_phan"] = [{"ma": y["ma"], "ten": y["ten"], "sl": int(y["sl"]), "loai": y.get("loai") or "",
					"nhom": y.get("nhom") or ""} for y in tp_combo]
			theo_khoa[khoa] = d
			dong.append(d)
		if tp_combo is not None:
			# Bánh trong combo cộng chung với bánh gọi lẻ rồi mới so số còn: một
			# chiếc canelé cuối không nuôi được cả combo lẫn một dòng lẻ.
			for y in tp_combo:
				sl_ma[y["ma"]] = sl_ma.get(y["ma"], 0) + sl * int(y["sl"])
		else:
			sl_ma[ma] = sl_ma.get(ma, 0) + sl
	for ma, sl in sl_ma.items():
		m = bang[ma]
		if m.get("loai") == "banh" and sl > int(m.get("con") or 0):
			con = max(0, int(m.get("con") or 0))
			raise ValueError(("%s trên tủ chỉ còn %d. Quý khách giảm số lượng." % (m["ten"], con)) if con
				else ("%s vừa hết trên tủ. Quý khách bỏ món này ra khỏi giỏ." % m["ten"]))
	for d in dong:
		if d["sl"] > SL_TOI_DA:
			raise ValueError("Số lượng %s phải từ 1 tới %d." % (d["ten"], SL_TOI_DA))
	return dong, tinh_tam(dong)


def _tp_tu_gui(tp, m, bang):
	"""Topping khách chọn cho một ly -> [{ma, ten, gia}] đã kiểm theo bảng máy
	chủ, bỏ trùng, giữ thứ tự khách chọn. Chỉ ly nước pha mới được kèm. THUẦN."""
	if not tp:
		return []
	if not isinstance(tp, list):
		raise ValueError("Topping của món không đọc được. Quý khách chọn lại.")
	if m.get("loai") != "nuoc" or m.get("khong_pha"):
		raise ValueError("%s không thêm topping được." % m["ten"])
	ra, da = [], set()
	for x in tp:
		ma = str(x.get("ma") if isinstance(x, dict) else x or "").strip()
		if not ma or ma in da:
			continue
		t = (bang or {}).get(ma)
		if not t or t.get("loai") != "topping":
			raise ValueError("Có topping vừa ngừng bán. Quý khách tải lại trang rồi chọn lại.")
		# v640: menu của điểm khai topping nào đi với món nào (Biên tập menu).
		if m.get("tp_cho") is not None and ma not in m["tp_cho"]:
			raise ValueError("%s không kèm được %s. Quý khách tải lại trang rồi chọn lại." % (m["ten"], t["ten"]))
		da.add(ma)
		ra.append({"ma": ma, "ten": t["ten"], "gia": int(t["gia"])})
	if len(ra) > TOPPING_TOI_DA_MOI_LY:
		raise ValueError("Mỗi ly tối đa %d topping." % TOPPING_TOI_DA_MOI_LY)
	return ra


def tinh_tam(dong):
	"""Tạm tính của các dòng (giá kể cả topping x số lượng). THUẦN."""
	return int(sum(gia_dong(d) * int(d.get("sl") or 0) for d in dong or []))


def sl_dang_cho(ds_mon_json):
	"""{mã: số lượng} của các đơn đang chờ nhận, để trừ khỏi số bánh còn. THUẦN."""
	ra = {}
	for s in ds_mon_json or []:
		try:
			ds = json.loads(s or "[]")
		except (TypeError, ValueError):
			continue
		for d in ds if isinstance(ds, list) else []:
			if not isinstance(d, dict) or not d.get("ma"):
				continue
			if d.get("thanh_phan"):
				# v642: combo giữ bánh theo từng món thành phần.
				for y in d["thanh_phan"]:
					if isinstance(y, dict) and y.get("ma"):
						ra[y["ma"]] = ra.get(y["ma"], 0) + int(d.get("sl") or 0) * int(y.get("sl") or 0)
				continue
			ra[d["ma"]] = ra.get(d["ma"], 0) + int(d.get("sl") or 0)
	return ra


def mon_dang_giu(dang_cho, da_nhan, phieu_mo, ngay):
	"""Các chuỗi món (json) còn phải giữ trên tủ. THUẦN.

	Codex PR #541: đơn ĐÃ NHẬN nằm trên phiếu tạm tính, mà số đã bán của bảng
	kiểm kho bỏ mọi phiếu tạm tính, nên nhận xong mà thôi giữ thì bàn khác gọi
	lại được đúng mấy cái bánh đó. Giữ tiếp đơn đã nhận trong ngày khi phiếu của
	nó còn là phiếu tạm tính nháp, hoặc khi đơn đang được lập phiếu (chưa có
	phiếu); phiếu đã chốt (thành bill bán hay ghi sổ) thì số đã bán tính rồi,
	thôi giữ để không trừ hai lần."""
	ds = list(dang_cho or [])
	for r in da_nhan or []:
		# Codex PR #541 vòng 7: đơn vừa giành Đã nhận mà CHƯA có phiếu (thu ngân
		# đang lập phiếu tạm tính) vẫn phải giữ; có phiếu thì giữ khi phiếu còn mở.
		if r.get("hoa_don") and r.get("hoa_don") not in phieu_mo:
			continue
		luc = _dt(r.get("nhan_luc"))
		if luc is not None and ngay is not None and luc.date() != ngay:
			continue
		ds.append(r.get("mon"))
	return ds


def _dt(x):
	if isinstance(x, datetime):
		return x
	try:
		return datetime.strptime(str(x or "")[:19], "%Y-%m-%d %H:%M:%S")
	except ValueError:
		return None


def het_han(luc, bay_gio, phut=PHUT_HET_HAN):
	"""Đơn tạo lúc `luc` đã quá hạn chờ chưa. Không đọc được giờ thì coi như
	quá hạn: đơn mồ côi không được treo mãi trên màn quầy. THUẦN."""
	a = _dt(luc)
	if a is None:
		return True
	return bay_gio - a >= timedelta(minutes=phut)


def trang_thai_that(tt, luc, bay_gio):
	"""Trạng thái khách và quầy thấy: đơn chờ quá hạn là Hết hạn ngay cả khi
	nhịp 5 phút chưa kịp chạy. THUẦN."""
	if tt == TT_CHO and het_han(luc, bay_gio):
		return TT_HET_HAN
	return tt


def phut_cho(luc, bay_gio):
	a = _dt(luc)
	return max(0, int((bay_gio - a).total_seconds() // 60)) if a else 0


def mo_ta_tc(tc):
	"""["Ít đá", "50% đường"] -> "Ít đá, 50% đường"; chuỗi này đi vào ô tuy_chon
	của dòng hoá đơn đúng như màn quầy gửi. THUẦN."""
	return ", ".join(str(x) for x in (tc or []) if str(x).strip())


def dong_hoa_don(dong):
	"""Dòng đơn gọi món -> dòng giỏ của màn quầy (ban_hang._dung_dong_mon).
	Topping (v639) thành dòng riêng ngay sau ly nước, số lượng theo ly, mô tả
	"Kèm <tên ly>" để quầy biết của ly nào. THUẦN."""
	ra = []
	for d in dong or []:
		ra.append({"item_code": d["ma"], "qty": int(d["sl"]), "rate": float(d["gia"]), "tuy_chon": mo_ta_tc(tc_hien(d))})
		for t in d.get("tp") or []:
			ra.append({"item_code": t["ma"], "qty": int(d["sl"]), "rate": float(t["gia"]), "tuy_chon": "Kèm " + str(d.get("ten") or "")})
	return ra


def chon_phieu_tam(ds):
	"""Phiếu tạm tính của bàn để thêm món: phiếu mới lập nhất. THUẦN."""
	ds = [r for r in ds or [] if r.get("name")]
	if not ds:
		return ""
	ds.sort(key=lambda r: str(r.get("creation") or ""), reverse=True)
	return ds[0]["name"]


def _doc_mon(r):
	try:
		v = json.loads(r.get("mon") or "[]")
		return v if isinstance(v, list) else []
	except (TypeError, ValueError):
		return []


def the_quay(r, bay_gio, ten_diem="", anh=None):
	"""Một thẻ đơn chờ trên màn quầy. THUẦN. anh: {mã món: đường dẫn ảnh danh mục}
	(Codex PR #541 vòng 2, AGENTS.md 2b.4: chỗ nào có tên món thì có ảnh món)."""
	mon = _doc_mon(r)
	anh = anh or {}
	return {
		"ma": r.get("name"), "ban": chuan_ban(r.get("ban")) or "", "diem": r.get("diem") or "", "ten_diem": ten_diem,
		"so_mon": sum(int(d.get("sl") or 0) for d in mon), "tam_tinh": int(r.get("tam_tinh") or 0),
		"phut": phut_cho(r.get("luc"), bay_gio),
		"mon": [{"ma": d.get("ma"), "ten": d.get("ten"), "sl": int(d.get("sl") or 0), "tc": tc_hien(d),
			"loai": d.get("loai") or "", "nhom": d.get("nhom") or "", "gia": gia_dong(d),
			"anh": anh.get(d.get("ma")) or ""} for d in mon],
		"ghi_chu": r.get("ghi_chu") or "", "ten_goi": r.get("ten_goi") or "",
		"gioi_thieu": r.get("ten_gioi_thieu") or "",
	}


def cho_khach(r, bay_gio, da_tra=False):
	"""Trạng thái đơn trả cho trang khách: tối thiểu, không số điện thoại,
	không tên đầy đủ, không mã hoá đơn nội bộ. THUẦN.

	da_tra (Codex PR #545 vòng 1): phiếu tạm tính của lượt đã nhận không còn
	mở (thu ngân đã chốt bill, hoặc huỷ), để trang khách không cộng lượt của
	bill cũ vào bill mới. Chỉ một cờ, không lộ mã hoá đơn."""
	tt = trang_thai_that(r.get("trang_thai"), r.get("luc"), bay_gio)
	nhan = _dt(r.get("nhan_luc"))
	luc = _dt(r.get("luc"))
	mon = _doc_mon(r)
	# v642 (anh Việt 06/11/2026): màn "Đơn của bàn" hiện giờ gọi từng lượt và
	# tiền từng dòng. Tiền dòng là giá máy chủ đã chốt lúc gọi (chuan_gio),
	# cùng nguồn với tạm tính, không phải giá trình duyệt gửi lên.
	return {
		"ma": r.get("name"), "trang_thai": tt, "ban": chuan_ban(r.get("ban")) or "",
		"luc": luc.strftime("%H:%M") if luc else "",
		"nhan_luc": nhan.strftime("%H:%M") if (nhan and tt == TT_NHAN) else "",
		"ly_do": (r.get("ly_do") or "") if tt == TT_TU_CHOI else "",
		"tam_tinh": int(r.get("tam_tinh") or 0),
		"da_tra": 1 if (da_tra and tt == TT_NHAN) else 0,
		"mon": [{"ten": d.get("ten"), "sl": int(d.get("sl") or 0), "tc": tc_hien(d), "gia": gia_dong(d),
			"tien": gia_dong(d) * int(d.get("sl") or 0)} for d in mon],
	}


def the_bill(hd, tong, ud=None):
	"""Hoá đơn của bàn gửi trang khách (Codex PR #545 vòng 6). Lượt khách gọi
	được nhập vào phiếu tạm tính chung của bàn (_vao_phieu_tam), nên tổng cần
	thanh toán phải lấy từ phiếu đó: gồm cả món máy khác cùng bàn gọi và món
	thu ngân thêm. Khoá là mã băm tên phiếu, để hai lượt cùng phiếu chỉ tính
	một lần mà không lộ tên phiếu nội bộ. THUẦN.

	tong None (Codex PR #545 vòng 7: đọc phiếu lỗi) vẫn trả khoá, tong None: lượt
	đó vẫn thuộc phiếu, trang không cộng nó thêm lên tổng mà lượt khác đọc được."""
	try:
		so = None if tong is None else int(round(float(tong)))
	except (TypeError, ValueError):
		so = None
	ra = {"khoa": hashlib.sha256(("vgb-bill|" + str(hd or "")).encode()).hexdigest()[:16], "tong": so}
	# v643: ưu đãi khách chọn tại bàn đã trừ vào tong; kèm tên và số giảm để
	# trang khách hiện dòng "Ưu đãi".
	if ud:
		from vagabond.uu_dai_ban import the_ud

		t = the_ud(ud)
		if t:
			ra["ud"] = t
	return ra


def soan_tin(r, ten_diem, link):
	"""Tin Zalo báo nhóm quầy. KHÔNG có số tiền: tin bộ phận Bán hàng bị bỏ dòng
	có tiền ở cửa ghi tin (kenh_zalo.bo_dong_tien, luật v613). Tạm tính xem trên
	app. THUẦN. Trả (tiêu đề, các dòng)."""
	mon = _doc_mon(r)
	tieu_de = "Bàn %s · %s gọi món qua QR" % (r.get("ban"), ten_diem)
	dong = ["Đơn %s, %d món:" % (r.get("name"), sum(int(d.get("sl") or 0) for d in mon))]
	for d in mon[:12]:
		dong.append("- %s x%d%s" % (d.get("ten"), int(d.get("sl") or 0), (" (%s)" % mo_ta_tc(tc_hien(d))) if tc_hien(d) else ""))
	if len(mon) > 12:
		dong.append("... và %d món nữa" % (len(mon) - 12))
	if r.get("ghi_chu"):
		dong.append("Ghi chú: %s" % str(r.get("ghi_chu"))[:120])
	dong.append("Nhận đơn trong %d phút trên màn Tính tiền. Mở app: %s" % (PHUT_HET_HAN, link))
	return tieu_de, dong


def the_tro_giup(r, bay_gio, ten_diem="", bill=None):
	"""Một thẻ "bàn cần trợ giúp" trên màn quầy (v639). bill: {"ma", "tam_tinh"}
	của phiếu tạm tính hôm nay của bàn khi khách xin tính tiền. THUẦN."""
	return {
		"ma": r.get("name"), "ban": chuan_ban(r.get("ban")) or "", "diem": r.get("diem") or "", "ten_diem": ten_diem,
		"ly_do": r.get("ly_do") or "", "chi_tiet": r.get("chi_tiet") or "", "phut": phut_cho(r.get("luc"), bay_gio),
		"bill": (bill or {}).get("ma") or "", "tam_tinh": int((bill or {}).get("tam_tinh") or 0), "hoa_don": (bill or {}).get("hoa_don") or "",
	}


def soan_tin_tro_giup(r, ten_diem, link):
	"""Tin Zalo nhóm quầy khi khách bấm chuông (v639). Không số tiền. THUẦN."""
	tieu_de = "Bàn %s · %s cần trợ giúp: %s" % (r.get("ban"), ten_diem, r.get("ly_do") or "")
	dong = []
	if r.get("chi_tiet"):
		dong.append("Khách nhắn: %s" % str(r.get("chi_tiet"))[:DAI_CHI_TIET])
	dong.append("Tới bàn rồi bấm \"Đã tới bàn\" trên màn Tính tiền. Mở app: %s" % link)
	return tieu_de, dong


def chuan_ly_do(v):
	"""Lý do khách chọn phải nằm trong danh sách; khác thì rỗng. THUẦN."""
	v = str(v or "").strip()
	return v if v in LY_DO_GOI else ""


def ma_bill_moi(diem, rand_chu):
	"""Mã bill tạm tính mới cho điểm: tiền tố điểm + 5 ký tự trong bảng chữ không
	gây nhầm (ma_bill). rand_chu là hàm chọn một ký tự. THUẦN."""
	from vagabond import ma_bill

	return ma_bill.tien_to_cua(diem) + "".join(rand_chu(ma_bill.CHU_SINH) for _ in range(ma_bill.DAI_DUOI))


def chuan_nonce(v):
	"""Mã lần gửi do trình duyệt sinh (taoNonce): 32 ký tự base64url. THUẦN."""
	v = str(v or "")
	return v if re.fullmatch(r"[A-Za-z0-9_-]{16,64}", v) else ""


def token_khach(bi_mat, ma):
	"""Khoá khách dùng để hỏi trạng thái một đơn: HMAC mã đơn. THUẦN."""
	return hmac.new(str(bi_mat).encode("utf-8"), ("goi-mon-tt:" + str(ma or "")).encode("utf-8"),
		hashlib.sha256).hexdigest()[:32]


def bam(token):
	return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


# ---------------------------------------------------------- chạm Frappe

import frappe  # noqa: E402
from frappe.utils import cint, flt, getdate, now_datetime  # noqa: E402

try:
	from frappe.rate_limiter import rate_limit  # noqa: E402
except ImportError:  # Frappe giả của bộ kiểm tầng khung
	def rate_limit(**_kw):
		return lambda f: f

QUYEN_IN_QR = {"System Manager", "Giám đốc", "VGB - Quản lý cửa hàng"}


def _bi_mat():
	from frappe.utils.password import get_encryption_key

	return get_encryption_key()


def link_ban(diem, ban):
	"""Địa chỉ tuyệt đối trên miền khách in thành QR một bàn."""
	from vagabond.ten_mien import link_khach

	return link_khach(duong_qr(diem, ban, khoa_ban(_bi_mat(), diem, ban)))


def _diem(ma):
	"""Điểm bán có quầy đang bật, không thì None."""
	from vagabond import diem_ban

	ma = chuan_diem(ma)
	for d in diem_ban.ds(chi_bat=True):
		if d["ma"] == ma and d["quay"]:
			return d
	return None


def _gio_mo_cua(d, bay_gio):
	"""Đang mở cửa không, theo giờ trên thẻ Cửa hàng marketing đã xuất bản (cùng
	nguồn trang Đặt bàn). Chưa điền hay đọc hỏng thì dùng GIO_MAC_DINH."""
	from vagabond import dat_ban

	gio = ""
	try:
		from vagabond import noi_dung_web

		ds = noi_dung_web.thong_tin_day_du(noi_dung_web._ban_cong_khai())["cua_hang"]
		c = dat_ban.tim_cua_hang(ds, d.get("ten"), d.get("dia_chi")) or {}
		gio = c.get("gio_mo_cua") or ""
	except Exception:
		gio = ""
	mo = dat_ban.mo_cua(gio, bay_gio) if gio else None
	if mo is None:
		mo = dat_ban.mo_cua(GIO_MAC_DINH, bay_gio)
	return mo


def doc_tuy_chon():
	"""Lựa chọn pha chế đang bật, cùng nguồn màn Tính tiền."""
	from vagabond import ban_hang

	return ban_hang.doc_tuy_chon()


def do_uong_cua_diem(ma_diem, hom_nay=None):
	"""Đồ uống của một điểm (có giá theo bảng giá điểm), kèm cờ bán web hôm nay."""
	from vagabond import diem_ban, tat_ban_web

	rows = frappe.get_all(
		"Item", filters={"item_group": ["in", list(NHOM_NUOC)], "disabled": 0},
		fields=["item_code", "item_name", "image", "standard_rate", "item_group", "disabled", "is_sales_item", "has_variants",
			"description"],
		limit_page_length=0, ignore_permissions=True,
	)
	tat = tat_ban_web.bang([r.get("item_code") for r in rows], hom_nay)
	mo_ta = {str(r.get("item_code") or ""): mo_ta_ngan(r.get("description")) for r in rows}
	ra = loc_do_uong(rows, diem_ban.gia_rieng(ma_diem), tat)
	for x in ra:
		x["mo_ta"] = mo_ta.get(x["ma"], "")
		x["khong_pha"] = 1 if khong_pha(x["ten"]) else 0
	return ra


def topping_cua_diem(ma_diem):
	"""Topping kèm ly nước của một điểm (v639): [{ma, ten, gia}], giá theo bảng giá điểm."""
	from vagabond import diem_ban

	rows = frappe.get_all(
		"Item", filters={"item_group": NHOM_TOPPING, "disabled": 0},
		fields=["item_code", "item_name", "standard_rate", "item_group", "disabled", "is_sales_item", "has_variants"],
		limit_page_length=0, ignore_permissions=True,
	)
	return loc_topping(rows, diem_ban.gia_rieng(ma_diem))


def _cho_cua(diem, ban=None):
	loc = {"diem": diem, "trang_thai": TT_CHO}
	if ban is not None:
		loc["ban"] = ban
	return frappe.get_all(DT, filters=loc, fields=["name", "ban", "mon", "luc"], limit_page_length=0, ignore_permissions=True)


def _da_nhan_cua(diem):
	return frappe.get_all(DT, filters={"diem": diem, "trang_thai": TT_NHAN},
		fields=["name", "mon", "hoa_don", "nhan_luc"], limit_page_length=0, ignore_permissions=True)


def _phieu_tam_mo(ten):
	"""Trong các phiếu đã cho, phiếu nào còn là phiếu tạm tính nháp chưa huỷ."""
	ten = sorted({str(t) for t in ten or [] if t})
	if not ten:
		return set()
	return set(frappe.get_all("Sales Invoice", filters={"name": ["in", ten], "docstatus": 0, "vgb_tam_tinh": 1,
		"vgb_huy": ["!=", 1]}, pluck="name", limit_page_length=0, ignore_permissions=True))


def bang_mon(d, hom_nay=None):
	"""Bảng món gọi được ở một điểm lúc này: {mã: {...}}. Bánh lấy từ bảng kiểm
	kho (cùng phép tab Tại quầy), trừ số đang chờ quầy nhận và số đã nhận mà
	phiếu tạm tính của bàn chưa chốt; đồ uống đang bật."""
	from vagabond import diem_ban, kiem_kho

	from vagabond import bien_tap_menu

	bay = now_datetime()
	ra = {}
	# v640: món nước, tuỳ chọn và topping theo menu đang chạy của điểm (Biên tập
	# menu): món ẩn, nhóm tắt, món chưa xếp không gọi được; cùng một nguồn với
	# trang khách (kiem_kho) và màn Tính tiền.
	ds_uong = do_uong_cua_diem(d["ma"], hom_nay)
	ds_tp = topping_cua_diem(d["ma"])
	_, uong = bien_tap_menu.ap_menu(bien_tap_menu.menu_hien_hanh(d["ma"], ds_uong, ds_tp), ds_uong)
	for x in uong:
		if not x["ban_web"]:
			continue
		ra[x["ma"]] = {"ten": x["ten"], "gia": x["gia"], "loai": "nuoc", "nhom_goc": x["nhom_goc"],
			"tc": x["tc"], "khong_pha": int(x.get("khong_pha") or 0), "tp_cho": list(x["tp"])}
	for t in ds_tp:
		ra[t["ma"]] = {"ten": t["ten"], "gia": t["gia"], "loai": "topping", "nhom_goc": NHOM_TOPPING}
	da_nhan = _da_nhan_cua(d["ma"])
	cho = sl_dang_cho(mon_dang_giu([r.get("mon") for r in _cho_cua(d["ma"]) if not het_han(r.get("luc"), bay)],
		da_nhan, _phieu_tam_mo([r.get("hoa_don") for r in da_nhan]), bay.date()))
	gia_diem = diem_ban.gia_rieng(d["ma"])
	for m in kiem_kho.banh_tren_quay(d["ma"], hom_nay):
		con = int(m["con"]) - int(cho.get(m["ma"]) or 0)
		ra[m["ma"]] = {"ten": m["ten"], "gia": gia_mon(m["ma"], gia_diem, m["gia_chung"]), "loai": "banh", "con": con,
			"nhom_goc": m.get("nhom") or ""}
	# v642: combo cố định đang chạy, sau khi đã có đủ nước và bánh để kiểm thành phần.
	for c in combo_ban_duoc(doc_combo_ban(d["ma"]), ra):
		ra[c["ma"]] = c
	return ra


def doc_combo_ban(ma_diem):
	"""Combo cố định của một điểm cho trang bàn: [{ma, ten, gia, goc, mo_ta, anh,
	dong}]. Luật bán lấy đúng của hoá đơn (combo_mon.ly_do_khong_ban) và phải qua
	cho CẢ HAI nguồn đơn bàn: phiếu tạm tính lập với nguồn Tại chỗ, các lượt gọi
	sau thêm vào phiếu đã mang nguồn QR tại bàn, mà combo được rã lúc lưu phiếu.
	Giá bộ tính như cửa rã combo (giá gốc trừ phần giảm của bộ)."""
	from vagabond import combo_mon, khuyen_mai

	try:
		ds = frappe.get_all("Vagabond Combo", filters={"bat": 1, "ma_hang": ["like", "KMCB%"]},
			fields=["name", "ma_hang"], order_by="uu_tien asc, ten asc", limit_page_length=0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_mon_ban: đọc combo lỗi")
		return []
	ra = []
	for r in ds:
		try:
			cb = khuyen_mai._doc_combo(r["name"])
			# Số lượng lẻ (0,5 phần) không bày ra bàn: khách gọi theo bộ nguyên.
			if not cb["dong"] or any(flt(x.get("so_luong")) != int(flt(x.get("so_luong"))) for x in cb["dong"]):
				continue
			if any(combo_mon.ly_do_khong_ban(cb, r["ma_hang"], ma_diem, n) for n in (NGUON_TAO, NGUON_QR)):
				continue
			goc = sum(flt(x.get("so_luong")) * flt(x.get("gia_goc")) for x in cb["dong"])
			gia = goc - khuyen_mai._tiet_kiem_bo(cb, goc)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "goi_mon_ban: combo %s lỗi" % r.get("ma_hang"))
			continue
		ra.append({"ma": r["ma_hang"], "ten": cb.get("ten") or r["ma_hang"], "gia": int(round(gia)), "goc": int(round(goc)),
			"mo_ta": cb.get("mo_ta") or "", "anh": cb.get("anh") or "",
			"dong": [{"ma": x.get("item_code"), "ten": x.get("ten_mon") or "", "sl": int(flt(x.get("so_luong")))} for x in cb["dong"]]})
	return ra


def _kiem_link(diem, ban, k):
	"""(điểm, tên bàn) khi link hợp lệ, không thì (None, None). v647: bàn theo
	khu phải còn trong sơ đồ bàn của điểm (đổi tên khu là QR cũ hết dùng)."""
	n = chuan_ban(ban)
	d = _diem(diem)
	if not d or n is None or not dung_khoa(_bi_mat(), d["ma"], n, k):
		return None, None
	if not so_do_ban.co_ban(d.get("so_do_ban"), n):
		return None, None
	return d, n


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=600)
def mo_ban(diem=None, ban=None, k=None):
	"""Trang khách mở link QR: link đúng thì trả tên điểm, số bàn, đang mở cửa
	không. Link sai thì {ok: 0} và trang ở chế độ xem như thường."""
	d, n = _kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0}
	mo = _gio_mo_cua(d, now_datetime())
	return {"ok": 1, "diem": d["ma"], "ten": d.get("ten_ngan") or d["ten"], "ban": n,
		"mo_cua": 1 if mo.get("dang_mo") else 0, "gio": mo.get("gio") or "",
		"gioi_thieu": _co_gioi_thieu()}


def _co_gioi_thieu():
	"""Công tắc Hoa hồng giới thiệu: tắt thì giỏ gọi món ẩn ô Mã giới thiệu."""
	try:
		from vagabond import gioi_thieu
		return 1 if gioi_thieu.bat() else 0
	except Exception:
		return 1


def _ten_gioi_thieu(sdt):
	"""Tên gọi nhân viên giới thiệu, qua mô đun giới thiệu nếu đã có. Lỗi thì rỗng."""
	if not sdt:
		return ""
	try:
		from vagabond import gioi_thieu
	except ImportError:
		return ""
	try:
		return str(gioi_thieu.ten_theo_sdt(sdt) or "")[:60]
	except Exception:
		return ""


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=600)
def goi(diem=None, ban=None, k=None, nonce=None, mon=None, ghi_chu="", ten="", sdt_gioi_thieu=""):
	"""Khách bấm Gọi món. Trả {ok, ma, token} hoặc {ok: 0, cau}.

	Kiểm theo thứ tự: link, mã lần gửi (bấm hai lần trả lại đơn cũ), giờ mở
	cửa, số đơn chờ, món còn bán và còn số. Giá do máy chủ tính."""
	d, n = _kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0, "cau": "Mã QR không hợp lệ. Quý khách nhờ nhân viên gần nhất gọi món giúp."}
	nonce = chuan_nonce(nonce)
	if not nonce:
		return {"ok": 0, "cau": "Quý khách tải lại trang rồi gọi món lại."}
	bi_mat = _bi_mat()
	cu = frappe.db.get_value(DT, {"nonce": nonce}, ["name", "diem", "ban"], as_dict=True)
	if cu:
		if cu.diem != d["ma"] or chuan_ban(cu.ban) != n:
			return {"ok": 0, "cau": "Quý khách tải lại trang rồi gọi món lại."}
		return {"ok": 1, "ma": cu.name, "token": token_khach(bi_mat, cu.name), "lap_lai": 1}
	bay = now_datetime()
	if not _gio_mo_cua(d, bay).get("dang_mo"):
		return {"ok": 0, "cau": "Quầy đang ngoài giờ mở cửa nên chưa nhận gọi món tại bàn."}
	# Codex PR #541 vòng 2: hai bàn gửi cùng lúc cùng đọc số bánh còn trước khi
	# đơn kia được ghi, cả hai qua. Đọc tồn, kiểm số và ghi đơn chạy tuần tự
	# theo điểm bán, khoá giữ tới khi đơn đã commit.
	khoa = TEN_KHOA_DIEM % d["ma"]
	if not _lay_khoa(khoa):
		return {"ok": 0, "cau": "Quầy đang nhận nhiều đơn cùng lúc. Quý khách bấm Gọi món lại sau vài giây."}
	try:
		kq = _goi_trong_khoa(d, n, nonce, bi_mat, bay, mon, ghi_chu, ten, sdt_gioi_thieu)
		if kq.get("ok"):
			frappe.db.commit()
		return kq
	finally:
		_nha_khoa(khoa)


TEN_KHOA_DIEM = "vgb_goi_mon_ban:%s"
TEN_KHOA_BAN = "vgb_phieu_ban:%s:%s"


def _lay_khoa(ten, giay=10):
	"""Khoá tên của MariaDB (theo kết nối), chờ tối đa `giay` giây. True khi lấy được."""
	r = frappe.db.sql("select get_lock(%s, %s)", (ten, giay))
	return bool(r and r[0] and cint(r[0][0]) == 1)


def _nha_khoa(ten):
	try:
		frappe.db.sql("select release_lock(%s)", (ten,))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_mon_ban: nhả khoá %s" % ten)


def _goi_trong_khoa(d, n, nonce, bi_mat, bay, mon, ghi_chu, ten, sdt_gioi_thieu):
	from vagabond.thanh_toan_web_thuan import chuan_gioi_thieu

	cho = [r for r in _cho_cua(d["ma"]) if not het_han(r.get("luc"), bay)]
	if sum(1 for r in cho if chuan_ban(r.get("ban")) == n) >= CHO_TOI_DA_MOI_BAN:
		return {"ok": 0, "cau": "Bàn này đang có %d đơn chờ quầy nhận. Quý khách đợi quầy nhận rồi gọi thêm." % CHO_TOI_DA_MOI_BAN}
	if len(cho) >= CHO_TOI_DA_MOI_DIEM:
		return {"ok": 0, "cau": "Quầy đang bận. Quý khách nhắn nhân viên gần nhất để gọi món."}
	try:
		dong, tam = chuan_gio(mon, bang_mon(d, getdate()))
	except ValueError as e:
		return {"ok": 0, "cau": str(e), "tai_lai": 1}
	sdt = chuan_gioi_thieu(sdt_gioi_thieu)
	doc = frappe.get_doc({
		"doctype": DT, "diem": d["ma"], "ban": n, "mon": json.dumps(dong, ensure_ascii=False),
		"so_mon": sum(x["sl"] for x in dong), "tam_tinh": tam,
		"ghi_chu": str(ghi_chu or "").strip()[:DAI_GHI_CHU], "ten_goi": str(ten or "").strip()[:DAI_TEN],
		"sdt_gioi_thieu": sdt, "ten_gioi_thieu": _ten_gioi_thieu(sdt),
		"trang_thai": TT_CHO, "luc": bay, "nonce": nonce,
	})
	try:
		doc.insert(ignore_permissions=True)
	except Exception as e:
		# Hai lượt cùng mã lần gửi chạy song song: ô nonce là duy nhất, lượt sau
		# vấp khoá và đọc lại đơn của lượt trước.
		if "Duplicate" not in type(e).__name__ and "Duplicate" not in str(e):
			raise
		frappe.db.rollback()
		cu = frappe.db.get_value(DT, {"nonce": nonce}, "name")
		if not cu:
			raise
		return {"ok": 1, "ma": cu, "token": token_khach(bi_mat, cu), "lap_lai": 1}
	token = token_khach(bi_mat, doc.name)
	frappe.db.set_value(DT, doc.name, "token_bam", bam(token), update_modified=False)
	_bao_quay(doc, d)
	return {"ok": 1, "ma": doc.name, "token": token}


def _bao_quay(doc, d):
	"""Tin Zalo cho nhóm quầy. Ghi trong giao dịch của yêu cầu POST, gửi sau commit."""
	from vagabond import kenh_zalo
	from vagabond.lien_ket_app import goc_app

	try:
		tieu_de, dong = soan_tin(doc.as_dict(), d.get("ten_ngan") or d["ten"], goc_app() + "/ban-tai-quay")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_mon_ban: soạn tin lỗi")
		return
	kenh_zalo.bao("viec", "ban_hang", tieu_de, dong, khoa="goi-mon:%s" % doc.name,
		kiem="goi_mon_cho", nguon=doc.name, ma_tin="bh_goi_mon_tai_ban")


def con_cho_nhan(ten):
	"""Tin Zalo hỏi lại ngay trước khi gửi: đơn còn chờ quầy nhận không."""
	r = frappe.db.get_value(DT, ten, ["trang_thai", "luc"], as_dict=True)
	return bool(r) and trang_thai_that(r.trang_thai, r.luc, now_datetime()) == TT_CHO


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=120, seconds=600)
def trang_thai(ma=None, token=None):
	"""Trang khách hỏi trạng thái một đơn. Cần khoá khách trả lúc gọi món."""
	ma = str(ma or "").strip()[:40]
	if not ma or not isinstance(token, str) or not re.fullmatch(r"[0-9a-f]{32}", token or ""):
		return {"ok": 0}
	r = frappe.db.get_value(DT, ma, ["name", "diem", "ban", "mon", "tam_tinh", "trang_thai", "luc", "nhan_luc",
		"ly_do", "token_bam", "hoa_don"], as_dict=True)
	if not r or not hmac.compare_digest(str(r.get("token_bam") or ""), bam(token)):
		return {"ok": 0}
	# Bill đã chốt: phiếu của lượt không còn là phiếu tạm tính mở (cùng phép
	# _phieu_tam_mo mà bảng giữ bánh dùng). Lượt chưa có phiếu là đang lập.
	hd = r.get("hoa_don")
	da_tra = bool(hd) and r.get("trang_thai") == TT_NHAN and hd not in _phieu_tam_mo([hd])
	kq = dict(cho_khach(r, now_datetime(), da_tra), ok=1)
	if hd and kq["trang_thai"] == TT_NHAN and not da_tra:
		bill = _tong_bill(hd)
		if bill:
			kq["bill"] = bill
	return kq


def _tong_bill(hd):
	"""Tổng hiện tại của phiếu tạm tính bàn (Codex PR #545 vòng 6). Đọc lỗi thì
	vẫn trả khoá phiếu, tổng rỗng (vòng 7), không chặn trạng thái."""
	try:
		r = frappe.db.get_value("Sales Invoice", hd, ["grand_total"], as_dict=True)
		try:
			ud = frappe.db.get_value("Sales Invoice", hd, "vgb_ud_ban")
		except Exception:
			ud = None  # cột chưa dựng (trước migrate): không có ưu đãi
		return the_bill(hd, (r or {}).get("grand_total"), ud)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_mon_ban: đọc tổng hoá đơn của bàn lỗi")
		return the_bill(hd, None)


# ------------------------------------------------------- chuông gọi nhân viên


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=600)
def goi_nhan_vien(diem=None, ban=None, k=None, ly_do=None, chi_tiet="", nonce=None):
	"""Khách bấm chuông Gọi nhân viên trên trang bàn (v639). Trả {ok, ma} hoặc
	{ok: 0, cau}. Mỗi bàn tối đa 3 lần trong 10 phút, chỉ trong giờ mở cửa."""
	d, n = _kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0, "cau": "Mã QR không hợp lệ. Quý khách nhắn nhân viên gần nhất."}
	nonce = chuan_nonce(nonce)
	if not nonce:
		return {"ok": 0, "cau": "Quý khách tải lại trang rồi bấm lại."}
	cu = frappe.db.get_value(DT_TG, {"nonce": nonce}, ["name", "diem", "ban"], as_dict=True)
	if cu:
		if cu.diem != d["ma"] or chuan_ban(cu.ban) != n:
			return {"ok": 0, "cau": "Quý khách tải lại trang rồi bấm lại."}
		return {"ok": 1, "ma": cu.name, "lap_lai": 1}
	ly = chuan_ly_do(ly_do)
	if not ly:
		return {"ok": 0, "cau": "Quý khách chọn một lý do."}
	bay = now_datetime()
	if not _gio_mo_cua(d, bay).get("dang_mo"):
		return {"ok": 0, "cau": "Quầy đang ngoài giờ mở cửa."}
	# Codex PR #542 vòng 1: hai khách cùng bàn bấm cùng lúc cùng đếm "2 lời" rồi
	# cùng qua trần 3. Đếm, kiểm, ghi và commit chạy tuần tự theo bàn bằng khoá
	# tên MariaDB, cùng cách khoá của đơn gọi món.
	khoa = TEN_KHOA_CHUONG % (d["ma"], n)
	if not _lay_khoa(khoa, 5):
		return {"ok": 0, "cau": "Bàn này vừa bấm chuông. Quý khách đợi một chút rồi bấm lại."}
	try:
		return _goi_nhan_vien_trong_khoa(d, n, ly, chi_tiet, nonce, bay)
	finally:
		_nha_khoa(khoa)


TEN_KHOA_CHUONG = "vgb_chuong:%s:%s"


def _goi_nhan_vien_trong_khoa(d, n, ly, chi_tiet, nonce, bay):
	moc = bay - timedelta(minutes=PHUT_DEM_GOI)
	gan_day = frappe.get_all(DT_TG, filters={"diem": d["ma"], "ban": n, "luc": [">=", moc]}, pluck="name", limit_page_length=0)
	if len(gan_day) >= GOI_TOI_DA_MOI_BAN:
		return {"ok": 0, "cau": "Bàn này vừa gọi %d lần. Nhân viên đang tới, quý khách đợi một chút hoặc nhắn Zalo." % GOI_TOI_DA_MOI_BAN}
	doc = frappe.get_doc({
		"doctype": DT_TG, "diem": d["ma"], "ban": n, "ly_do": ly, "chi_tiet": str(chi_tiet or "").strip()[:DAI_CHI_TIET],
		"trang_thai": TG_CHO, "luc": bay, "nonce": nonce,
	})
	try:
		doc.insert(ignore_permissions=True)
	except Exception as e:
		if "Duplicate" not in type(e).__name__ and "Duplicate" not in str(e):
			raise
		frappe.db.rollback()
		cu = frappe.db.get_value(DT_TG, {"nonce": nonce}, "name")
		if not cu:
			raise
		return {"ok": 1, "ma": cu, "lap_lai": 1}
	_bao_tro_giup(doc, d)
	# Commit TRONG khoá: luồng sau vào đếm phải thấy lời này.
	frappe.db.commit()
	return {"ok": 1, "ma": doc.name, "luc": bay.strftime("%H:%M")}


def _bao_tro_giup(doc, d):
	"""Tin Zalo nhóm quầy: bàn nào cần gì. Không số tiền."""
	from vagabond import kenh_zalo
	from vagabond.lien_ket_app import goc_app

	try:
		tieu_de, dong = soan_tin_tro_giup(doc.as_dict(), d.get("ten_ngan") or d["ten"], goc_app() + "/ban-tai-quay")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_mon_ban: soạn tin trợ giúp lỗi")
		return
	kenh_zalo.bao("viec", "ban_hang", tieu_de, dong, khoa="tro-giup:%s" % doc.name,
		kiem="tro_giup_cho", nguon=doc.name, ma_tin="bh_khach_can_tro_giup")


def con_tro_giup(ten):
	"""Tin Zalo hỏi lại ngay trước khi gửi: lời gọi còn chờ không."""
	r = frappe.db.get_value(DT_TG, ten, ["trang_thai", "luc"], as_dict=True)
	return bool(r) and r.trang_thai == TG_CHO and not het_han(r.luc, now_datetime(), PHUT_TG_HET_HAN)


@frappe.whitelist(methods=["POST"])
def xong_tro_giup(ma=None):
	"""Thu ngân bấm "Đã tới bàn": lời gọi chuyển Đã xong, ghi ai bấm."""
	_kiem_quyen_quay()
	ma = str(ma or "").strip()
	r = frappe.db.get_value(DT_TG, ma, ["name", "ban", "trang_thai"], as_dict=True)
	if not r:
		frappe.throw("Không thấy lời gọi %s." % ma)
	if r.trang_thai != TG_CHO:
		return {"ok": 1, "da_xong": 1}
	frappe.db.set_value(DT_TG, ma, {"trang_thai": TG_XONG, "xong_luc": now_datetime(), "xong_boi": frappe.session.user})
	frappe.db.commit()
	return {"ok": 1, "ban": r.ban}


# ------------------------------------------------------------ màn quầy


def _kiem_quyen_quay():
	from vagabond import ban_hang

	ban_hang._kiem_quyen_ban()


@frappe.whitelist()
def dem_cho(diem=None):
	"""Màn Tính tiền hỏi mỗi 15 giây: các đơn đang chờ của quầy này."""
	_kiem_quyen_quay()
	d = _diem(diem)
	if not d:
		return {"so": 0, "ds": []}
	bay = now_datetime()
	ds = frappe.get_all(DT, filters={"diem": d["ma"], "trang_thai": TT_CHO},
		fields=["name", "diem", "ban", "mon", "tam_tinh", "luc", "ghi_chu", "ten_goi", "ten_gioi_thieu"],
		order_by="luc asc", limit_page_length=0)
	ten = d.get("ten_ngan") or d["ten"]
	ds = [r for r in ds if not het_han(r.get("luc"), bay)]
	the = [the_quay(r, bay, ten, _anh_mon([x.get("ma") for r in ds for x in _doc_mon(r)])) for r in ds]
	return {"so": len(the), "ds": the, "ly_do": list(LY_DO_TU_CHOI), "tro_giup": _tro_giup_cho(d, bay)}


def _tro_giup_cho(d, bay):
	"""Các lời gọi nhân viên còn chờ của quầy, mới nhất trong 30 phút (v639)."""
	ten = d.get("ten_ngan") or d["ten"]
	ds = frappe.get_all(DT_TG, filters={"diem": d["ma"], "trang_thai": TG_CHO},
		fields=["name", "diem", "ban", "ly_do", "chi_tiet", "luc"], order_by="luc asc", limit_page_length=0)
	ra = []
	for r in ds:
		if het_han(r.get("luc"), bay, PHUT_TG_HET_HAN):
			continue
		bill = None
		if r.get("ly_do") == LY_DO_GOI[1]:
			bill = _bill_cua_ban(d["ma"], chuan_ban(r.get("ban")) or "", bay.date())
		ra.append(the_tro_giup(r, bay, ten, bill))
	return ra


def _bill_cua_ban(diem, ban, ngay):
	"""Phiếu tạm tính hôm nay của bàn, để thu ngân mở ngay khi khách xin tính tiền."""
	try:
		hd = _phieu_tam_cua_ban(diem, ban, ngay)
		if not hd:
			return None
		r = frappe.db.get_value("Sales Invoice", hd, ["custom_pancake_display_id", "grand_total"], as_dict=True) or {}
		return {"hoa_don": hd, "ma": r.get("custom_pancake_display_id") or hd, "tam_tinh": int(flt(r.get("grand_total")))}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_mon_ban: đọc bill của bàn lỗi")
		return None


def _anh_mon(ma):
	"""{mã món: ảnh danh mục} cho các món trên thẻ quầy, một câu đọc."""
	ma = sorted({str(x) for x in ma or [] if x})
	if not ma:
		return {}
	return {r["name"]: r.get("image") or "" for r in frappe.get_all("Item", filters={"name": ["in", ma]},
		fields=["name", "image"], limit_page_length=0, ignore_permissions=True)}


def _khoa(ma):
	"""Đọc HIỆN TẠI và khoá hàng bản ghi tới hết giao dịch (for update). Lượt
	thứ hai chờ ở đây, lúc vào thì thấy trạng thái lượt trước đã commit."""
	r = frappe.db.sql(
		"select name, diem, ban, mon, tam_tinh, ghi_chu, ten_goi, sdt_gioi_thieu, trang_thai, luc, hoa_don "
		"from `tab%s` where name=%%s for update" % DT, (ma,), as_dict=True)
	return r[0] if r else None


def _phieu_tam_cua_ban(diem, ban, ngay):
	from vagabond import ngay_ban

	r = frappe.db.sql(
		"select si.name, si.creation from `tabSales Invoice` si where si.docstatus = 0 "
		"and ifnull(si.vgb_tam_tinh, 0) = 1 and ifnull(si.vgb_huy, 0) = 0 and si.vgb_quay = %(quay)s "
		"and si.vgb_so_ban = %(ban)s and " + ngay_ban.dk_sql("si"),
		{"quay": diem, "ban": str(ban), "ngay": getdate(ngay)}, as_dict=True)
	return chon_phieu_tam(r)


def _vao_phieu_tam(r):
	"""Thêm món vào phiếu tạm tính hôm nay của bàn, chưa có thì lập phiếu mới
	qua ĐÚNG ban_hang.tao_don_tay (giá điểm, khách lẻ, mã bill). Trả (tên, đã có)."""
	import random

	from vagabond import ban_hang

	dong = _doc_mon(r)
	rows = dong_hoa_don(dong)
	gc = ("Bàn %s gọi qua QR%s" % (r["ban"], (": " + r["ghi_chu"]) if r.get("ghi_chu") else ""))[:300]
	ten = _phieu_tam_cua_ban(r["diem"], r["ban"], getdate())
	if ten:
		si = frappe.get_doc("Sales Invoice", ten, for_update=True)
		if si.docstatus != 0 or not cint(si.get("vgb_tam_tinh")) or cint(si.get("vgb_huy")):
			ten = ""
	if ten:
		for x in rows:
			si.append("items", ban_hang._dung_dong_mon(x))
		cu = (si.get("vgb_ghi_chu") or "").strip()
		if r.get("ghi_chu"):
			si.vgb_ghi_chu = (cu + (" | " if cu else "") + gc)[:1000]
		# v643: bàn đã chọn ưu đãi thì tính lại phần giảm trên giỏ mới.
		from vagabond import uu_dai_ban

		uu_dai_ban.tinh_lai(si)
		si.flags.ignore_permissions = True
		si.save()
		return si.name, 1
	sr = random.SystemRandom()
	kq = ban_hang.tao_don_tay(
		nguon=NGUON_TAO, quay=r["diem"], ma_don=ma_bill_moi(r["diem"], sr.choice),
		ten_khach=(r.get("ten_goi") or ("Khách bàn %s" % r["ban"])), items=rows, tam_tinh=1,
		so_ban=str(r["ban"]), ghi_chu=gc)
	frappe.db.set_value("Sales Invoice", kq["name"], "custom_nguon", NGUON_QR, update_modified=False)
	return kq["name"], 0


def _gan_gioi_thieu(si_name, sdt):
	"""Hook hoa hồng giới thiệu. Mô đun chưa có hay lỗi thì bỏ qua, không chặn nhận đơn."""
	if not sdt:
		return
	try:
		from vagabond import gioi_thieu
	except ImportError:
		return
	try:
		si = frappe.get_doc("Sales Invoice", si_name)
		gioi_thieu.gan_cho_hoa_don(si, sdt, "tai_ban")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "goi_mon_ban: gắn giới thiệu lỗi")


@frappe.whitelist(methods=["POST"])
def nhan(ma=None):
	"""Thu ngân bấm "Nhận đơn và in phiếu pha chế". Một đơn chỉ nhận một lần."""
	_kiem_quyen_quay()
	ma = str(ma or "").strip()
	r = _khoa(ma)
	if not r:
		frappe.throw("Không thấy đơn gọi món %s." % ma)
	bay = now_datetime()
	tt = trang_thai_that(r["trang_thai"], r["luc"], bay)
	if tt == TT_HET_HAN and r["trang_thai"] == TT_CHO:
		frappe.db.set_value(DT, ma, "trang_thai", TT_HET_HAN)
		frappe.db.commit()
		frappe.throw("Đơn bàn %s đã chờ quá %d phút nên máy đã chuyển Hết hạn; khách được báo nhắn nhân viên. "
			"Ra bàn hỏi lại khách rồi bấm món trên màn Tính tiền." % (r["ban"], PHUT_HET_HAN))
	if tt != TT_CHO:
		frappe.throw("Đơn bàn %s %s, không cần nhận lại." % (r["ban"], CAU_DA_XU_LY.get(tt, tt.lower())))
	if not _diem(r["diem"]):
		frappe.throw("Điểm bán %s đang tắt, không nhận đơn được." % r["diem"])
	# Codex PR #541 vòng 3: hai đơn KHÁC nhau của cùng một bàn được hai thu ngân
	# nhận cùng lúc thì cả hai cùng tìm không thấy phiếu tạm tính và cùng lập
	# phiếu. Tìm hoặc lập phiếu của một bàn chạy tuần tự bằng khoá tên theo bàn
	# (giữ qua các lần commit giữa chừng của tao_don_tay, nhả sau commit cuối).
	khoa_ban = TEN_KHOA_BAN % (r["diem"], r["ban"])
	if not _lay_khoa(khoa_ban, 15):
		frappe.throw("Bàn %s đang được nhận một đơn khác. Bấm Nhận lại sau vài giây." % r["ban"])
	try:
		# Giành đơn TRƯỚC rồi commit để nhả khoá hàng: thu ngân thứ hai đang chờ khoá
		# vào sẽ thấy Đã nhận. tao_don_tay tự commit giữa chừng nên khoá hàng không
		# giữ được qua bước lập phiếu.
		frappe.db.set_value(DT, ma, {"trang_thai": TT_NHAN, "nhan_luc": bay, "nhan_boi": frappe.session.user})
		frappe.db.commit()
		try:
			ten, da_co = _vao_phieu_tam(r)
		except Exception:
			frappe.db.rollback()
			frappe.db.set_value(DT, ma, {"trang_thai": TT_CHO, "nhan_luc": None, "nhan_boi": None})
			frappe.db.commit()
			raise
		frappe.db.set_value(DT, ma, "hoa_don", ten)
		_gan_gioi_thieu(ten, r.get("sdt_gioi_thieu"))
		frappe.db.commit()
	finally:
		_nha_khoa(khoa_ban)
	ma_bill = frappe.db.get_value("Sales Invoice", ten, "custom_pancake_display_id") or ten
	return {
		"ok": 1, "hoa_don": ten, "bill": ma_bill, "them_vao": da_co, "ban": r["ban"],
		# Phiếu pha chế in bằng đúng posInPhieuMon của màn quầy.
		"phieu": {"name": ten, "bill": ma_bill, "so_ban": str(r["ban"]), "ghi_chu": r.get("ghi_chu") or "",
			"mon": dong_phieu_pha(_doc_mon(r))},
	}


@frappe.whitelist(methods=["POST"])
def tu_choi(ma=None, ly_do=None):
	"""Thu ngân từ chối một đơn, bắt chọn lý do. Không lập phiếu nào."""
	_kiem_quyen_quay()
	ly_do = str(ly_do or "").strip()[:120]
	if not ly_do:
		frappe.throw("Chọn lý do từ chối để khách biết.")
	ma = str(ma or "").strip()
	r = _khoa(ma)
	if not r:
		frappe.throw("Không thấy đơn gọi món %s." % ma)
	tt = trang_thai_that(r["trang_thai"], r["luc"], now_datetime())
	if tt != TT_CHO:
		frappe.throw("Đơn bàn %s %s, không từ chối nữa." % (r["ban"], CAU_DA_XU_LY.get(tt, tt.lower())))
	frappe.db.set_value(DT, ma, {"trang_thai": TT_TU_CHOI, "ly_do": ly_do, "nhan_luc": now_datetime(),
		"nhan_boi": frappe.session.user})
	frappe.db.commit()
	return {"ok": 1}


def quet_het_han():
	"""Lịch 5 phút: đơn chờ quá 10 phút chuyển Hết hạn. Khách đã thấy Hết hạn
	từ trước nhờ trang_thai_that; nhịp này để sổ sách và báo cáo đúng."""
	bay = now_datetime()
	moc = bay - timedelta(minutes=PHUT_HET_HAN)
	ds = frappe.get_all(DT, filters={"trang_thai": TT_CHO, "luc": ["<=", moc]}, pluck="name", limit_page_length=500)
	for ten in ds:
		# Codex PR #541 vòng 4: giữa lúc đọc danh sách và lúc ghi, thu ngân có thể
		# vừa nhận đơn (nhận bắt đầu trước mốc 10 phút). Chỉ đổi khi bản ghi VẪN
		# đang Chờ nhận, đúng trong một câu UPDATE, không ghi đè Đã nhận.
		frappe.db.sql("update `tab%s` set trang_thai = %%s where name = %%s and trang_thai = %%s" % DT,
			(TT_HET_HAN, ten, TT_CHO))
	moc_tg = bay - timedelta(minutes=PHUT_TG_HET_HAN)
	tg = frappe.get_all(DT_TG, filters={"trang_thai": TG_CHO, "luc": ["<=", moc_tg]}, pluck="name", limit_page_length=500)
	for ten in tg:
		frappe.db.sql("update `tab%s` set trang_thai = %%s where name = %%s and trang_thai = %%s" % DT_TG,
			(TG_HET_HAN, ten, TG_CHO))
	if ds or tg:
		frappe.db.commit()
	return len(ds)


# ------------------------------------------------------------ in QR bàn


def _kiem_quyen_in():
	if not QUYEN_IN_QR & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý cửa hàng và Giám đốc in được mã QR tại bàn.")


def the_diem_in(d):
	"""Một điểm trên màn In QR tại bàn: sơ đồ đã khai (để sửa), nhóm bàn theo
	khu (để tích chọn), địa chỉ in dưới standee. THUẦN."""
	so_do = so_do_ban.chuan_so_do(d.get("so_do_ban"))
	return {"ma": d["ma"], "ten": d.get("ten_ngan") or d["ten"], "phu": d.get("phu") or d.get("dia_chi") or "",
		"so_do": so_do, "nhom": so_do_ban.nhom_ban(so_do), "da_khai": 1 if so_do else 0,
		"dia_chi_qr": d.get("dia_chi_qr") or d.get("dia_chi") or ""}


@frappe.whitelist()
def diem_in_qr():
	"""Các điểm có quầy để chọn khi in QR, kèm sơ đồ bàn (v647)."""
	_kiem_quyen_in()
	from vagabond import diem_ban

	return [the_diem_in(d) for d in diem_ban.ds(chi_bat=True) if d["quay"]]


@frappe.whitelist(methods=["POST"])
def luu_so_do_ban(diem=None, so_do=None, dia_chi_qr=None, dong_y_mat=0):
	"""v647: lưu sơ đồ bàn theo khu của một điểm (màn In QR tại bàn). Màn Tính
	tiền đọc chung sơ đồ này. Sơ đồ mới bỏ mất bàn theo khu đã có thì trả danh
	sách để màn hỏi lại (QR đã in của các bàn đó sẽ hết dùng); bấm đồng ý mới lưu."""
	_kiem_quyen_in()
	from vagabond import diem_ban

	d = _diem(diem)
	if not d:
		frappe.throw("Chọn một điểm bán có quầy.")
	if isinstance(so_do, str):
		so_do = json.loads(so_do or "[]")
	moi, loi = so_do_ban.kiem_so_do(so_do)
	if loi:
		frappe.throw("<br>".join(loi[:6]))
	mat = so_do_ban.mat_khi_doi(d.get("so_do_ban"), moi)
	if mat and not cint(dong_y_mat):
		return {"ok": 0, "mat": mat}
	cap = {"so_do_ban": moi}
	if dia_chi_qr is not None:
		cap["dia_chi_qr"] = str(dia_chi_qr or "").strip()[:120]
	diem_ban.dat_truong(d["ma"], cap, "Sửa sơ đồ bàn %s: %s" % (d["ma"], ", ".join(
		so_do_ban.mo_ta_dong(x) for x in moi) or "Bàn 1 tới 20"))
	return {"ok": 1, "diem": the_diem_in(_diem(d["ma"]))}


@frappe.whitelist()
def to_qr(diem=None, tu=1, den=20, ban=None):
	"""Các tờ QR của một điểm. v647: ban là các bàn đã tích (theo sơ đồ);
	không gửi ban thì in bàn số từ tu tới den như trước."""
	_kiem_quyen_in()
	from vagabond.qr_chuyen_khoan import anh_lien_ket

	d = _diem(diem)
	if not d:
		frappe.throw("Chọn một điểm bán có quầy.")
	if ban not in (None, "", "[]", []):
		if isinstance(ban, str) and ban.strip().startswith("["):
			ban = json.loads(ban)
		ds, sai = ds_ban_chon(ban, d.get("so_do_ban"))
		if sai:
			frappe.throw("Bàn %s không có trong sơ đồ bàn của %s. Tải lại màn hình rồi chọn lại." % (
				", ".join(sai[:5]), d.get("ten_ngan") or d["ten"]))
		if not ds:
			frappe.throw("Chọn ít nhất một bàn để in.")
	else:
		ds = ds_ban(tu, den)
		if not ds:
			frappe.throw("Số bàn từ 1 tới %d." % BAN_TOI_DA)
	ten = d.get("ten_ngan") or d["ten"]
	ra = []
	for n in ds:
		link = link_ban(d["ma"], n)
		ra.append({"ban": n, "nhan": so_do_ban.nhan_in(n), "ten_diem": ten, "link": link, "anh": anh_lien_ket(link)})
	return {"diem": d["ma"], "ten": ten, "to": ra, "dia_chi_qr": d.get("dia_chi_qr") or d.get("dia_chi") or ""}

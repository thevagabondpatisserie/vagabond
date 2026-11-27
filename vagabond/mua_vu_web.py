"""v693: tab In season của trang đặt bánh cho mùa Giáng sinh (Panettone, Bûche).

Anh Việt chốt 26/11/2026 (project doc prompt-pr-mua-vu-panettone-buche):
1. Gộp size: nhiều mã của cùng một bánh hiện thành MỘT thẻ, bấm vào mới chọn size.
   Sales hoặc Marketing điền "Nhóm trên web" và "Nhãn size" ở từng dòng của Mùa vụ.
   Dòng chưa điền nhóm thì đứng một mình như trước.
2. "Loại trên web" (Panettone, Bûche, Khác) quyết luật giỏ và lịch nhận.
3. Lịch nhận: Panettone chỉ thứ 2, 4, 6 và đặt trước ít nhất 3 ngày; Bûche ngày
   nào cũng nhận, đặt trước ít nhất 2 ngày; đơn có cả hai theo lịch chặt hơn.
   Số ngày và thứ là ô cài đặt của Mùa vụ. Ngày nhận không quá ngày kết thúc mùa.
4. Sốt chấm bán kèm Panettone: tối đa 2 hũ mỗi bánh, mã sốt khai ở Mùa vụ.
5. Panettone không có cờ lời chúc, không có dĩa nĩa tặng.

Phần THUẦN ở trên (không chạm Frappe, ca kiểm chạy được không cần site). Phần
chạm hệ ở dưới, nạp frappe trong thân hàm. Trình duyệt chạy cùng luật ở
web_vue/kho/thuan.js (ca thu_mua_vu_web_693 chạy cùng bộ số hai phía); máy chủ
kiểm lại lúc tạo đơn vì ai cũng gọi thẳng cửa tạo đơn được.
"""

import datetime
import re
import unicodedata

PANETTONE, BUCHE = "panettone", "buche"
# Giá trị ô chọn "Loại trên web" trên dòng Mùa vụ -> mã loại dùng trong máy.
LOAI_THEO_O = {"Panettone": PANETTONE, "Bûche": BUCHE}
CO_LUAT = (PANETTONE, BUCHE)
# Thứ ghi theo cách người Việt đọc: 2 là thứ Hai ... 7 là thứ Bảy, 8 là Chủ nhật.
MOI_THU = (2, 3, 4, 5, 6, 7, 8)
# Mặc định anh Việt chốt 26/11/2026. thu None nghĩa là ngày nào cũng nhận.
LUAT_MAC_DINH = {
	PANETTONE: {"truoc": 3, "thu": [2, 4, 6]},
	BUCHE: {"truoc": 2, "thu": None},
}
TRUOC_TOI_DA = 60
SOT_MOI_BANH = 2


# ------------------------------------------------------------------ THUẦN

def chuan_loai(v):
	"""Mã loại ('panettone', 'buche') từ ô chọn hoặc từ chính mã loại. Khác thì ''."""
	s = str(v or "").strip()
	if s in LOAI_THEO_O:
		return LOAI_THEO_O[s]
	return s if s in CO_LUAT else ""


def khoa_nhom(ten):
	"""Khoá ổn định của một nhóm: tên viết thường, gọn khoảng trắng. Cùng cách
	banh_web.khoa_banh để nội dung nhóm khoá chung với thẻ Bánh của trình biên tập."""
	t = unicodedata.normalize("NFC", str(ten or ""))
	return " ".join(t.lower().split())[:140]


def duong_dan_nhom(ten):
	"""Đoạn đường dẫn #/in-season/<...> của một nhóm: chữ thường không dấu, gạch nối."""
	s = unicodedata.normalize("NFD", str(ten or "").replace("đ", "d").replace("Đ", "D"))
	s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
	return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80]


def doc_thu(v):
	"""Ô "nhận vào thứ" người điền tay -> (danh sách thứ đã sắp, hoặc None là mọi
	ngày; câu lỗi). Để trống (None, chuỗi rỗng) trả ('mac_dinh', '') để nơi gọi
	lấy mặc định của loại. Nhận: 2,4,6 hoặc "2 4 6", CN hoặc 8 là Chủ nhật,
	"tất cả" là ngày nào cũng nhận."""
	if v is None or not str(v).strip():
		return "mac_dinh", ""
	s = unicodedata.normalize("NFC", str(v)).strip().lower()
	if s in ("tất cả", "tat ca", "mọi ngày", "moi ngay"):
		return None, ""
	ra = set()
	for p in [x for x in re.split(r"[\s,;]+", s) if x]:
		if p in ("cn", "8"):
			ra.add(8)
		elif p in ("2", "3", "4", "5", "6", "7"):
			ra.add(int(p))
		else:
			return "mac_dinh", 'Ô thứ nhận bánh chỉ ghi các số 2 đến 7 và CN, cách nhau dấu phẩy, ví dụ "2,4,6". Để trống là dùng mặc định.'
	if set(MOI_THU) <= ra:
		return None, ""
	return sorted(ra), ""


def doc_truoc(v):
	"""Ô "đặt trước ít nhất (ngày)" -> (số ngày hoặc 'mac_dinh'; câu lỗi). Số 0 là
	giá trị người dùng chọn (nhận ngay hôm nay), KHÔNG phải để trống."""
	if v is None or not str(v).strip():
		return "mac_dinh", ""
	s = str(v).strip()
	if not s.isdigit() or int(s) > TRUOC_TOI_DA:
		return "mac_dinh", "Ô đặt trước ít nhất ghi số ngày từ 0 tới %d. Để trống là dùng mặc định." % TRUOC_TOI_DA
	return int(s), ""


def luat_mua(cai_dat=None):
	"""Luật lịch của từng loại theo bốn ô cài đặt của Mùa vụ. Ô để trống hoặc
	ghi sai thì lấy mặc định của loại (ô ghi sai đã bị chặn lúc lưu Mùa vụ)."""
	cd = cai_dat or {}
	ra = {}
	for loai in CO_LUAT:
		md = LUAT_MAC_DINH[loai]
		thu, _l1 = doc_thu(cd.get(loai + "_thu"))
		truoc, _l2 = doc_truoc(cd.get(loai + "_truoc"))
		ra[loai] = {
			"truoc": md["truoc"] if truoc == "mac_dinh" else truoc,
			"thu": (list(md["thu"]) if md["thu"] else None) if thu == "mac_dinh" else thu,
		}
	return ra


def loi_cai_dat(cai_dat=None):
	"""Các câu lỗi của bốn ô lịch, để chặn lúc lưu Mùa vụ. Rỗng là hợp lệ."""
	cd = cai_dat or {}
	ra = []
	for loai in CO_LUAT:
		for loi in (doc_thu(cd.get(loai + "_thu"))[1], doc_truoc(cd.get(loai + "_truoc"))[1]):
			if loi and loi not in ra:
				ra.append(loi)
	return ra


def luat_don(cac_loai, luat):
	"""Luật của CẢ đơn: đặt trước theo loại cần nhiều ngày nhất, thứ là phần chung
	của các loại. Đơn không có loại nào mang luật thì trả None."""
	loai = [l for l in CO_LUAT if l in set(cac_loai or [])]
	if not loai:
		return None
	truoc, thu = 0, None
	for l in loai:
		x = (luat or {}).get(l) or LUAT_MAC_DINH[l]
		truoc = max(truoc, int(x.get("truoc") or 0))
		if x.get("thu") is not None:
			thu = sorted(set(x["thu"]) if thu is None else set(thu) & set(x["thu"]))
	return {"loai": loai, "truoc": truoc, "thu": thu}


def thu_cua_ngay(ngay):
	"""Thứ kiểu Việt của một ngày: 2 tới 7, Chủ nhật là 8."""
	return ngay.weekday() + 2


def ngay_hop_le(ngay, hom_nay, ld, den_ngay=None):
	"""Ngày nhận có hợp luật của đơn không. Trả '' khi hợp lệ, hoặc mã lý do:
	'som' (chưa đủ số ngày đặt trước), 'sai_thu', 'qua_mua' (sau ngày kết thúc
	mùa), 'khong_ngay' (thiếu ngày). ld None (đơn không có hàng mang luật) thì ''."""
	if not ld:
		return ""
	if not ngay:
		return "khong_ngay"
	if (ngay - hom_nay).days < int(ld.get("truoc") or 0):
		return "som"
	if den_ngay and ngay > den_ngay:
		return "qua_mua"
	if ld.get("thu") is not None and thu_cua_ngay(ngay) not in ld["thu"]:
		return "sai_thu"
	return ""


def chu_thu(thu):
	"""'thứ 2, thứ 4, thứ 6' cho câu nói với khách."""
	return ", ".join("Chủ nhật" if t == 8 else "thứ %d" % t for t in thu or [])


def cau_luat(ld, den_ngay=None):
	"""Câu giải thích lịch nhận của đơn (máy chủ trả khi từ chối ngày sai)."""
	if not ld:
		return ""
	co_p, co_b = PANETTONE in ld["loai"], BUCHE in ld["loai"]
	dau = ("Đơn có cả Panettone và Bûche nên cả đơn theo lịch chặt hơn"
		if co_p and co_b else ("Panettone" if co_p else "Bûche"))
	ve = []
	if ld.get("thu") is not None:
		ve.append("chỉ nhận " + chu_thu(ld["thu"]) if ld["thu"] else "hiện không có thứ nào nhận")
	ve.append("cần đặt trước ít nhất %d ngày" % ld["truoc"] if ld["truoc"] else "nhận được ngay trong ngày")
	cau = dau + (": " if co_p and co_b else " ") + " và ".join(ve) + "."
	if den_ngay:
		cau += " Mùa này nhận bánh tới hết %s." % den_ngay.strftime("%d/%m")
	return cau + " Quý khách chọn lại ngày nhận."


def loai_hieu_luc(dong):
	"""{mã: loại hiệu lực} của mọi dòng Mùa vụ. dong: [{"ma", "nhom", "loai"}].

	MỘT phép cho cả hai phía (Codex #625): thẻ trên trang khách (gom_nhom) và phép
	kiểm lúc tạo đơn (lịch, sốt, dĩa nĩa) phải thấy cùng một loại cho từng mã.
	Các dòng cùng "Nhóm trên web" dùng chung một loại: có dòng nào là Panettone
	thì cả nhóm là Panettone (luật chặt hơn), không thì loại đầu tiên có điền.
	Dòng chưa điền nhóm giữ loại của chính nó. Mã không có loại thì không có khoá."""
	theo_nhom = {}
	for d in dong or []:
		ten = " ".join(str(d.get("nhom") or "").split())
		loai = chuan_loai(d.get("loai"))
		if not ten or not loai:
			continue
		k = khoa_nhom(ten)
		if loai == PANETTONE or k not in theo_nhom:
			theo_nhom[k] = loai
	ra = {}
	for d in dong or []:
		ten = " ".join(str(d.get("nhom") or "").split())
		loai = theo_nhom.get(khoa_nhom(ten)) if ten else chuan_loai(d.get("loai"))
		if loai and d.get("ma"):
			ra[d["ma"]] = loai
	return ra


def ten_the(nhom_web, ten_mon, ten_banh, ma):
	"""Tên thẻ của một dòng: tên nhóm nếu có, không thì tên hồ sơ món, rồi tên
	trên dòng, rồi mã. MỘT phép cho tab In season (hang_theo_mua) và thẻ nội
	dung của trình biên tập (Codex #625: hai nơi chọn tên khác nhau thì nội dung
	Marketing nhập không lên web)."""
	return " ".join(str(nhom_web or "").split()) or ten_mon or ten_banh or ma


def tim_the(so_ghi, ten, cac_ma, khoa=None):
	"""Thẻ nội dung của một nhóm: theo khoá tên trước; không thấy thì theo MÃ
	HÀNG đã gắn trên thẻ (tên món đổi sau khi thẻ đã tạo vẫn tìm ra). so_ghi:
	{khoá: bản ghi có "ma_hang" nhiều dòng}. khoa: hàm tính khoá tên."""
	sg = so_ghi or {}
	bg = sg.get((khoa or khoa_nhom)(ten))
	if bg:
		return bg
	ma = set(cac_ma or [])
	for x in sg.values():
		if ma & {m.strip() for m in str(x.get("ma_hang") or "").splitlines() if m.strip()}:
			return x
	return None


def gom_nhom(mon):
	"""Gộp danh sách phẳng (mỗi mã một dòng) thành các thẻ của tab In season.

	Dòng có "nhom" thì gộp theo tên nhóm; dòng chưa điền nhóm đứng một mình
	(dữ liệu của mùa cũ giữ nguyên cách hiện). Thứ tự thẻ theo lần gặp đầu của
	danh sách đã sắp. Trong một thẻ, size đắt đứng trước (bánh lớn trước bánh mini).
	Loại của thẻ: có dòng nào là Panettone thì cả thẻ theo Panettone (luật chặt
	hơn), không thì loại đầu tiên có điền."""
	nhom, thu_tu = {}, []
	for m in mon or []:
		ten_nhom = " ".join(str(m.get("nhom") or "").split())
		khoa = khoa_nhom(ten_nhom) if ten_nhom else "ma:" + str(m.get("ma") or "")
		g = nhom.get(khoa)
		if not g:
			g = nhom[khoa] = {
				"khoa": duong_dan_nhom(ten_nhom) if ten_nhom else str(m.get("ma") or ""),
				"ten": ten_the(ten_nhom, m.get("ten"), None, m.get("ma")),
				"gop": 1 if ten_nhom else 0,
				"loai": "", "anh": "", "la_hop": 0, "ruot": "", "sizes": [],
			}
			thu_tu.append(khoa)
		loai = chuan_loai(m.get("loai"))
		if loai == PANETTONE or not g["loai"]:
			g["loai"] = loai or g["loai"]
		g["la_hop"] = max(g["la_hop"], int(m.get("la_hop") or 0))
		g["ruot"] = g["ruot"] or m.get("ruot") or ""
		g["sizes"].append({
			"ma": m.get("ma"), "nhan": " ".join(str(m.get("nhan_size") or "").split()),
			"ten": m.get("ten") or m.get("ma"), "gia": int(m.get("gia") or 0), "anh": m.get("anh") or "",
			"con": int(m.get("con") or 0), "het": 1 if int(m.get("het") or 0) else 0,
		})
	ra = []
	for khoa in thu_tu:
		g = nhom[khoa]
		g["sizes"].sort(key=lambda s: (-s["gia"], str(s["ma"])))
		g["anh"] = next((s["anh"] for s in g["sizes"] if s["anh"]), "")
		g["het"] = 1 if all(s["het"] for s in g["sizes"]) else 0
		g["gia_tu"] = min(s["gia"] for s in g["sizes"])
		ra.append(g)
	return ra


def tran_sot(so_panettone, moi_banh=SOT_MOI_BANH):
	"""Số hũ sốt tối đa của cả đơn: mỗi bánh Panettone tối đa `moi_banh` hũ."""
	return max(0, int(so_panettone or 0)) * max(0, int(moi_banh))


def kiem_sot(hang, ma_sot, loai_theo_ma, moi_banh=SOT_MOI_BANH):
	"""hang: [{"variation_id", "quantity"}]. Trả (số hũ sốt trong đơn, trần) khi
	đơn vượt trần, không thì None. Đơn không có sốt thì None."""
	sot = set(ma_sot or [])
	so_sot = sum(int(h.get("quantity") or 0) for h in hang or [] if h.get("variation_id") in sot)
	if not so_sot:
		return None
	so_banh = sum(int(h.get("quantity") or 0) for h in hang or []
		if (loai_theo_ma or {}).get(h.get("variation_id")) == PANETTONE)
	tran = tran_sot(so_banh, moi_banh)
	return (so_sot, tran) if so_sot > tran else None


# v697 (anh Việt chốt 27/11/2026): trần số bánh mỗi ngày nhận theo ô "Trần mỗi ngày"
# của từng mã trên màn Kiểm bánh theo mùa, đếm mọi kênh (bảng Đơn theo ngày đồng bộ
# Pancake mỗi 5 phút, gồm đơn chốt, đơn chờ chốt, kênh khác), cộng đơn web tạo sau
# lần đồng bộ cuối. Nút "Ngưng nhận ngày này" tắt cả ngày trên web khi vượt đột xuất.
# Lùi mốc đếm đơn web chừng này phút trước lần đồng bộ cuối: đơn tạo trong lúc đang
# kéo Pancake không lọt khỏi cả hai nguồn (đếm thừa thì chặn sớm, an toàn hơn đếm thiếu).
LUI_DEM_WEB_PHUT = 10
CAU_NGAY_NGUNG = ("Ngày %s đã nhận đủ đơn bánh mùa lễ trên web. Quý khách chọn ngày khác "
	"hoặc gọi 0931 224 334 để được hỗ trợ.")
CAU_NGAY_DAY = "%s ngày %s chỉ còn nhận %d bánh, quý khách đang chọn %d. Quý khách chọn ngày khác hoặc bớt số lượng."


def doc_ngay_ngung(s):
	"""THUẦN: các ngày (YYYY-MM-DD) đã bấm Ngưng nhận, mỗi dòng một ngày; dòng lạ bỏ."""
	ra = set()
	for d in str(s or "").replace(",", "\n").splitlines():
		d = d.strip()
		if ngay_tu_iso(d):
			ra.add(ngay_tu_iso(d).isoformat())
	return sorted(ra)


def da_nhan_theo_ngay(lich, don_web_moi):
	"""THUẦN: {(mã, ngày ISO): số đã nhận} từ bảng Đơn theo ngày của Mùa vụ
	(lich: [{"ma", "ngay", "so"}]) cộng đơn web chưa vào bảng
	(don_web_moi: [{"ngay", "mon": [{"ma", "sl"}]}])."""
	ra = {}
	for r in lich or []:
		k = (str(r.get("ma") or ""), str(r.get("ngay") or "")[:10])
		ra[k] = ra.get(k, 0) + max(0, int(r.get("so") or 0))
	for d in don_web_moi or []:
		ng = str(d.get("ngay") or "")[:10]
		for m in d.get("mon") or []:
			try:
				sl = int(m.get("sl") or 0)
			except (TypeError, ValueError):
				continue
			if m.get("ma") and sl > 0:
				k = (str(m["ma"]), ng)
				ra[k] = ra.get(k, 0) + sl
	return ra


def xet_ngay(hang, ngay_iso, tran, da_nhan, ngung, ma_mua, ten=None):
	"""THUẦN: đơn có hàng của mùa nhận ngày `ngay_iso` còn chỗ không.

	Trả None khi nhận được, hoặc {"ly_do": "ngay_mua_vu", "nhac": [câu]} (cùng lý do
	với lịch nhận để trang khách mở lại lịch). tran: {mã: trần > 0}; da_nhan:
	{(mã, ngày): số}; ngung: các ngày đã bấm Ngưng nhận; ma_mua: mọi mã của mùa."""
	ngay_iso = str(ngay_iso or "")[:10]
	cua_mua = set(ma_mua or [])
	gop = {}
	for h in hang or []:
		ma = h.get("variation_id")
		if ma in cua_mua:
			gop[ma] = gop.get(ma, 0) + max(0, int(h.get("quantity") or 0))
	if not gop or not ngay_iso:
		return None
	nhan = ngay_tu_iso(ngay_iso)
	chu_ngay = nhan.strftime("%d/%m/%Y") if nhan else ngay_iso
	if ngay_iso in set(ngung or []):
		return {"ly_do": "ngay_mua_vu", "nhac": [CAU_NGAY_NGUNG % chu_ngay]}
	nhac = []
	for ma, sl in gop.items():
		t = int((tran or {}).get(ma) or 0)
		if t <= 0:
			continue
		da = int((da_nhan or {}).get((ma, ngay_iso)) or 0)
		if da + sl > t:
			nhac.append(CAU_NGAY_DAY % ((ten or {}).get(ma) or ma, chu_ngay, max(0, t - da), sl))
	return {"ly_do": "ngay_mua_vu", "nhac": nhac} if nhac else None


def han_ngay_cho_web(tran, da_nhan, ngung, tu_iso=""):
	"""THUẦN: phần trang khách cần để làm mờ ngày: trần từng mã, số đã nhận của
	các mã có trần (từ ngày `tu_iso`), các ngày đã ngưng."""
	tran = {m: int(t) for m, t in (tran or {}).items() if int(t or 0) > 0}
	da = {}
	for (ma, ng), so in (da_nhan or {}).items():
		if ma in tran and so and ng >= tu_iso:
			da.setdefault(ma, {})[ng] = int(so)
	return {"tran": tran, "da": da, "ngung": [d for d in ngung or [] if d >= tu_iso]}


def bo_hang_mua(hang, mua):
	"""THUẦN (v697): bỏ các dòng hàng thuộc mùa đang bán trên web khỏi phép kiểm tồn
	của bánh đặt trước thường (ton_don_web: nhận tới ba ngày tới). Hàng mùa vụ theo
	lịch nhận của loại và hạn mức của Mùa vụ. mua: kết quả doc_mua_web hoặc None."""
	ma = set((mua or {}).get("ma_mua") or ())
	return [h for h in hang or [] if h.get("variation_id") not in ma]


def chot_chiec(chiec, loai_theo_ma):
	"""Chiếc bánh Panettone không cắm cờ lời chúc: bỏ cờ và lời chúc trình duyệt
	gửi kèm. Chiếc của bánh khác giữ nguyên. chiec None (trang cũ) thì trả None."""
	if chiec is None:
		return None
	ra = []
	for c in chiec:
		if (loai_theo_ma or {}).get(c.get("ma")) == PANETTONE:
			c = dict(c, co=False, loi_chuc="")
		ra.append(c)
	return ra


def ngay_tu_iso(v):
	"""Ngày (date) từ chuỗi 'YYYY-MM-DD...' hoặc None."""
	try:
		return datetime.date.fromisoformat(str(v or "")[:10])
	except ValueError:
		return None


def vuot_sl(items_tho, cac_ma, tran):
	"""THUẦN: các mã mùa vụ (bánh, sốt) mà trình duyệt gửi quá `tran` cái trong
	một đơn. items_tho: danh sách "items" NGUYÊN của trình duyệt, trước bước làm
	sạch (bước đó lặng lẽ cắt mỗi mã về trần, Codex #625 vòng 2: đơn tạo ra thiếu
	hàng và thấp tiền hơn màn khách đã xác nhận). Dòng rác bị bỏ qua như bước làm sạch."""
	tong = {}
	for it in items_tho if isinstance(items_tho, list) else []:
		if not isinstance(it, dict):
			continue
		ma = str(it.get("variation_id") or "").strip()
		try:
			sl = int(it.get("quantity") or 0)
		except (TypeError, ValueError):
			continue
		if ma and sl > 0:
			tong[ma] = tong.get(ma, 0) + sl
	can = set(cac_ma or [])
	return sorted(ma for ma, sl in tong.items() if ma in can and sl > int(tran))


def xet_don(hang, ngay, hom_nay, mua, items_tho=None, tran_sl=None):
	"""THUẦN: xét một đơn theo cài đặt mùa `mua` ({loai_theo_ma, luat, ma_sot,
	den_ngay}). Trả None khi nhận được, hoặc {"ly_do", "nhac": [câu]}.
	items_tho, tran_sl: danh sách món nguyên của trình duyệt và trần mỗi mã của
	bước làm sạch, để từ chối rõ thay vì tạo đơn đã bị cắt bớt."""
	if not mua:
		return None
	loai_theo_ma = mua.get("loai_theo_ma") or {}
	if tran_sl is not None and vuot_sl(items_tho, list(loai_theo_ma) + list(mua.get("ma_sot") or []), tran_sl):
		return {"ly_do": "sl_mua_qua_tran", "nhac": [
			"Mỗi đơn trên web nhận tối đa %d cho mỗi loại bánh hoặc sốt mùa vụ. Quý khách bớt số lượng rồi gửi lại, hoặc gọi 0931 224 334." % int(tran_sl)]}
	vuot = kiem_sot(hang, mua.get("ma_sot"), loai_theo_ma)
	if vuot:
		return {"ly_do": "sot_qua_so", "nhac": [
			"Mỗi bánh Panettone chọn tối đa %d hũ sốt, đơn này được tối đa %d hũ. Quý khách bớt sốt rồi gửi lại."
			% (SOT_MOI_BANH, vuot[1])]}
	ld = luat_don([loai_theo_ma.get(h.get("variation_id")) for h in hang or []], mua.get("luat"))
	ly = ngay_hop_le(ngay, hom_nay, ld, mua.get("den_ngay"))
	if ly:
		return {"ly_do": "ngay_mua_vu", "nhac": [cau_luat(ld, mua.get("den_ngay"))]}
	return None


# ------------------------------------------------------------- CHẠM HỆ

def doc_mua_web():
	"""Mùa đang chạy trên web (cùng cách chọn với mua_vu.hang_theo_mua) và cài
	đặt của nó. Không có mùa thì None."""
	import frappe

	from vagabond import mua_vu

	doc = mua_vu.mua_cho_web()
	if not doc:
		return None
	return {
		"doc": doc,
		"loai_theo_ma": loai_cua_mua(doc),
		"luat": luat_mua({k: doc.get(k) for k in ("panettone_thu", "panettone_truoc", "buche_thu", "buche_truoc")}),
		"ma_sot": [s.ma_hang for s in doc.get("sot_web") or [] if s.ma_hang],
		# v697: mọi mã của mùa (kể cả dòng chưa điền Loại trên web), để cửa nhận đơn
		# không xét các mã này theo luật bánh đặt trước thường (bo_hang_mua).
		"ma_mua": [d.ma_hang for d in doc.dong if d.ma_hang],
		"den_ngay": frappe.utils.getdate(doc.den_ngay) if doc.den_ngay else None,
	}


def loai_cua_mua(doc):
	"""{mã: loại hiệu lực} của một bản ghi Mùa vụ (xem loai_hieu_luc)."""
	return loai_hieu_luc([{"ma": d.ma_hang, "nhom": d.get("nhom_web"), "loai": d.get("loai_web")} for d in doc.dong])


def kiem_don(hang, ngay_nhan, mua, items_tho=None, tran_sl=None):
	"""Lúc tạo đơn web: lịch nhận, số hũ sốt và trần số lượng mỗi mã của hàng mùa
	vụ. mua: kết quả doc_mua_web(). Trả None hoặc {"ly_do", "nhac"}. Đơn không có
	hàng mang luật, không có sốt thì None."""
	import frappe

	if not mua:
		return None
	return xet_don(hang, ngay_tu_iso(ngay_nhan), frappe.utils.getdate(frappe.utils.nowdate()), mua, items_tho, tran_sl)


def _don_web_sau_dong_bo(doc, cac_ma):
	"""Đơn web có hàng của mùa tạo sau lần đồng bộ Pancake cuối (lùi LUI_DEM_WEB_PHUT),
	chưa huỷ, nhận trong khoảng mùa: [{"ngay", "mon"}]. Chưa đồng bộ lần nào thì lấy hết."""
	import json

	import frappe

	loc = {"trang_thai": ["!=", "Da huy"]}
	if doc.get("dong_bo_luc"):
		loc["creation"] = [">", frappe.utils.add_to_date(doc.dong_bo_luc, minutes=-LUI_DEM_WEB_PHUT)]
	if doc.get("tu_ngay") and doc.get("den_ngay"):
		loc["ngay_nhan"] = ["between", [str(doc.tu_ngay) + " 00:00:00", str(doc.den_ngay) + " 23:59:59"]]
	ra = []
	cac_ma = set(cac_ma or [])
	if not cac_ma:
		return ra
	# Chỉ lấy đơn có nhắc tới mã của mùa (LIKE thu hẹp; khớp đúng từng món ở dưới):
	# không đọc đơn web nào khác, kể cả khi ca bench chạy trên site thật.
	hoac = [["snapshot", "like", '%%"%s"%%' % m.replace("%", "").replace("_", "\\_")] for m in sorted(cac_ma)]
	for x in frappe.get_all("Vagabond Don Web", filters=loc, or_filters=hoac, fields=["ngay_nhan", "snapshot"], limit_page_length=0, ignore_permissions=True):
		try:
			mon = [m for m in (json.loads(x.snapshot or "{}").get("mon") or []) if m.get("ma") in cac_ma]
		except (TypeError, ValueError, AttributeError):
			continue
		if mon and x.ngay_nhan:
			ra.append({"ngay": str(x.ngay_nhan)[:10], "mon": mon})
	return ra


def doc_han_ngay(doc):
	"""(trần {mã: n}, đã nhận {(mã, ngày): số}, ngày ngưng [ISO], tên {mã: tên}) của
	một bản ghi Mùa vụ. Đếm mọi kênh theo bảng Đơn theo ngày như màn Lịch tháng."""
	from frappe.utils import cint

	tran = {d.ma_hang: cint(d.tran_ngay) for d in doc.dong if d.ma_hang and cint(d.tran_ngay) > 0}
	ten = {d.ma_hang: d.ten_banh or d.ma_hang for d in doc.dong if d.ma_hang}
	ngung = doc_ngay_ngung(doc.get("ngay_ngung_web"))
	if not tran:
		return tran, {}, ngung, ten
	lich = [{"ma": l.ma_hang, "ngay": str(l.ngay), "so": cint(l.so_luong) + cint(l.cho_chot) + cint(l.don_khac)}
		for l in doc.get("lich") or [] if l.ma_hang in tran]
	return tran, da_nhan_theo_ngay(lich, _don_web_sau_dong_bo(doc, tran)), ngung, ten


def khoa_ngay(ngay):
	"""Khoá tệp theo ngày nhận: hai đơn cùng ngày xét trần và ghi lần lượt."""
	try:
		from frappe.utils.synchronization import filelock
	except Exception:  # pragma: no cover
		import contextlib

		return contextlib.nullcontext()
	return filelock("vgb_mua_ngay_" + str(ngay or "")[:10], timeout=20)


def xet_ngay_that(hang, ngay, mua):
	"""Đọc lại Mùa vụ (SAU khoá ngày, bên gọi đã kết thúc giao dịch đọc) và xét trần
	ngày, ngày ngưng cho đơn này. mua: kết quả doc_mua_web."""
	import frappe

	if not mua or not ngay:
		return None
	doc = frappe.get_doc("Vagabond Mua Vu", mua["doc"].name)
	tran, da, ngung, ten = doc_han_ngay(doc)
	return xet_ngay(hang, str(ngay)[:10], tran, da, ngung, mua.get("ma_mua"), ten)


def ma_khong_dung_cu():
	"""Các mã Panettone của mùa đang chạy: không tính vào trần dĩa, nĩa tặng."""
	mua = doc_mua_web()
	return {ma for ma, loai in ((mua or {}).get("loai_theo_ma") or {}).items() if loai == PANETTONE}


def sot_cho_web(doc):
	"""Các hũ sốt khách chọn được: mã khai ở Mùa vụ, còn bán, giá theo hồ sơ món."""
	import frappe

	from vagabond.anh_web import chon_anh

	ma = [s.ma_hang for s in doc.get("sot_web") or [] if s.ma_hang]
	if not ma:
		return []
	it = {x["item_code"]: x for x in frappe.get_all("Item", filters={"item_code": ["in", ma]},
		fields=["item_code", "item_name", "image", "standard_rate", "disabled", "is_sales_item"], limit_page_length=0)}
	ra = []
	for m in ma:
		x = it.get(m)
		if not x or frappe.utils.cint(x.get("disabled")) or not frappe.utils.cint(x.get("is_sales_item", 1)):
			continue
		if any(r["ma"] == m for r in ra):
			continue
		ra.append({"ma": m, "ten": x.get("item_name") or m, "gia": int(x.get("standard_rate") or 0),
			"anh": chon_anh(x.get("image"), [], "", ma_hang=m)[0]})
	return ra


def the_cua(khoa, cac_ma, chi_mua_vu=False, cot=("name", "khoa", "ma_hang")):
	"""Thẻ Bánh trên web chỉ của đúng các khoá tên `khoa` và các thẻ có gắn một
	trong các mã `cac_ma` (Codex #626 P1: không đọc cả bảng, để phép này chỉ chạm
	bản ghi của nhóm đang xét, kể cả khi ca bench chạy trên site thật).
	chi_mua_vu: chỉ lấy thẻ mùa vụ ở phần tìm theo mã. Trả {name: bản ghi}."""
	import frappe

	from vagabond import banh_web

	ra = {}
	khoa = sorted({k for k in khoa or [] if k})
	if khoa:
		for x in frappe.get_all(banh_web.DT, filters={"khoa": ["in", khoa]}, fields=list(cot), limit_page_length=0, ignore_permissions=True):
			ra[x["name"]] = x
	ma = sorted({str(m).strip() for m in cac_ma or [] if str(m or "").strip()})
	if ma:
		loc = {"mua_vu": 1} if chi_mua_vu else {}
		hoac = [[banh_web.DT, "ma_hang", "like", "%" + m.replace("%", "").replace("_", "\\_") + "%"] for m in ma]
		for x in frappe.get_all(banh_web.DT, filters=loc, or_filters=hoac, fields=list(cot), limit_page_length=0, ignore_permissions=True):
			# LIKE chỉ thu hẹp; khớp đúng từng dòng mã ở tim_the.
			ra[x["name"]] = x
	return ra


def noi_dung_nhom(nhom):
	"""Gắn mô tả, nguyên liệu, dị ứng, bảo quản và bộ ảnh Marketing nhập ở thẻ
	Bánh của trình biên tập (khoá theo tên nhóm) vào từng thẻ. Ô để trống thì
	không gắn, trang khách không hiện mục đó. Chỉ đọc thẻ của đúng các nhóm này."""
	from vagabond import banh_web

	if not banh_web.dang_dung() or not nhom:
		return nhom
	try:
		ds = the_cua([banh_web.khoa_banh(g["ten"]) for g in nhom], [s["ma"] for g in nhom for s in g["sizes"]],
			cot=("name", "khoa", "ten", "anh", "mo_ta", "tang", "di_ung", "bao_quan", "kem_theo", "ma_hang"))
	except Exception:
		import frappe

		frappe.log_error(title="Bánh mùa vụ trên web: không đọc được thẻ nội dung", message=frappe.get_traceback())
		return nhom
	sg = {x["khoa"]: x for x in ds.values()}
	for g in nhom:
		bg = tim_the(sg, g["ten"], [s["ma"] for s in g["sizes"]], banh_web.khoa_banh)
		if not bg:
			continue
		g["mo_ta"] = " ".join(banh_web.tach_dong(bg.get("mo_ta")))
		g["tang"] = banh_web.tach_dong(bg.get("tang"), banh_web.SO_TANG_TOI_DA)
		g["di_ung"] = " ".join(banh_web.tach_dong(bg.get("di_ung")))
		g["bao_quan"] = " ".join(banh_web.tach_dong(bg.get("bao_quan")))
		# v697: đồ kèm Marketing chọn ở thẻ Bánh; None là chưa chọn (trang khách dùng bộ mặc định theo loại).
		g["kem_theo"] = banh_web.doc_kem(bg.get("kem_theo"))
		anhs = [x["url"] for x in banh_web.doc_anh(bg.get("anh"))][:banh_web.SO_ANH_TOI_DA]
		if anhs:
			g["anh"], g["anhs"] = anhs[0], anhs
	return nhom


def tao_the_noi_dung(doc):
	"""Mỗi nhóm bánh mùa vụ có "Loại trên web" hoặc "Nhóm trên web" được một thẻ ở
	thẻ Bánh của trình biên tập để Marketing nhập nội dung. Thẻ đã có (kể cả của
	bánh thường trùng tên) thì chỉ gắn thêm mã. Thẻ mùa vụ không chờ ảnh, không
	nhắc Zalo: bánh hiện theo Mùa vụ, ảnh lấy từ hồ sơ món khi thẻ chưa có ảnh."""
	import frappe

	from vagabond import banh_web

	if not banh_web._bang_co():
		return 0
	loai = loai_cua_mua(doc)
	ten_mon = {x["item_code"]: x.get("item_name") for x in frappe.get_all("Item",
		filters={"item_code": ["in", [d.ma_hang for d in doc.dong]]}, fields=["item_code", "item_name"], limit_page_length=0)}
	nhom = {}
	for d in doc.dong:
		ten_nhom = " ".join(str(d.get("nhom_web") or "").split())
		if not ten_nhom and not loai.get(d.ma_hang):
			continue
		if frappe.utils.cint(d.khong_tran):
			continue
		ten = ten_the(ten_nhom, ten_mon.get(d.ma_hang), d.ten_banh, d.ma_hang)
		nhom.setdefault(banh_web.khoa_banh(ten), {"ten": ten, "ma": []})["ma"].append(d.ma_hang)
	the_mua = list(the_cua([], [m for g in nhom.values() for m in g["ma"]], chi_mua_vu=True).values())
	so = 0
	for khoa, g in nhom.items():
		r = frappe.db.sql("select name from `tab%s` where khoa=%%s for update" % banh_web.DT, (khoa,))
		if not r:
			# Tên món đổi sau khi thẻ đã tạo: thẻ mùa vụ cũ còn gắn mã thì dùng lại, không tạo thẻ thứ hai.
			cu = tim_the({x["name"]: x for x in the_mua}, "", g["ma"], lambda _t: None)
			if cu:
				r = frappe.db.sql("select name from `tab%s` where name=%%s for update" % banh_web.DT, (cu["name"],))
		if r:
			bg = frappe.get_doc(banh_web.DT, r[0][0])
			ma_hang = bg.ma_hang
			for m in g["ma"]:
				ma_hang = banh_web._them_ma(ma_hang, m)
			if ma_hang != (bg.ma_hang or ""):
				bg.ma_hang = ma_hang
				bg.flags.ignore_permissions = True
				bg.save()
			continue
		frappe.get_doc({"doctype": banh_web.DT, "khoa": khoa, "ten": g["ten"], "trang_thai": banh_web.DA_AN,
			"mua_vu": 1, "ma_hang": "\n".join(g["ma"]), "anh": "[]",
			"dua_boi": frappe.session.user, "dua_luc": frappe.utils.now_datetime()}).insert(ignore_permissions=True)
		so += 1
	return so

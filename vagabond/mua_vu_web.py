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
				"ten": ten_nhom or m.get("ten") or m.get("ma"),
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


def xet_don(hang, ngay, hom_nay, mua):
	"""THUẦN: xét một đơn theo cài đặt mùa `mua` ({loai_theo_ma, luat, ma_sot,
	den_ngay}). Trả None khi nhận được, hoặc {"ly_do", "nhac": [câu]}."""
	if not mua:
		return None
	loai_theo_ma = mua.get("loai_theo_ma") or {}
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
		"loai_theo_ma": {d.ma_hang: chuan_loai(d.get("loai_web")) for d in doc.dong if chuan_loai(d.get("loai_web"))},
		"luat": luat_mua({k: doc.get(k) for k in ("panettone_thu", "panettone_truoc", "buche_thu", "buche_truoc")}),
		"ma_sot": [s.ma_hang for s in doc.get("sot_web") or [] if s.ma_hang],
		"den_ngay": frappe.utils.getdate(doc.den_ngay) if doc.den_ngay else None,
	}


def kiem_don(hang, ngay_nhan, mua):
	"""Lúc tạo đơn web: lịch nhận và số hũ sốt của hàng mùa vụ. mua: kết quả
	doc_mua_web(). Trả None hoặc {"ly_do", "nhac"}. Đơn không có hàng mang luật,
	không có sốt thì None."""
	import frappe

	if not mua:
		return None
	return xet_don(hang, ngay_tu_iso(ngay_nhan), frappe.utils.getdate(frappe.utils.nowdate()), mua)


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


def noi_dung_nhom(nhom):
	"""Gắn mô tả, nguyên liệu, dị ứng, bảo quản và bộ ảnh Marketing nhập ở thẻ
	Bánh của trình biên tập (khoá theo tên nhóm) vào từng thẻ. Ô để trống thì
	không gắn, trang khách không hiện mục đó."""
	from vagabond import banh_web

	sg = banh_web.so_ghi() or {}
	for g in nhom:
		bg = sg.get(banh_web.khoa_banh(g["ten"]))
		if not bg:
			continue
		g["mo_ta"] = " ".join(banh_web.tach_dong(bg.get("mo_ta")))
		g["tang"] = banh_web.tach_dong(bg.get("tang"), banh_web.SO_TANG_TOI_DA)
		g["di_ung"] = " ".join(banh_web.tach_dong(bg.get("di_ung")))
		g["bao_quan"] = " ".join(banh_web.tach_dong(bg.get("bao_quan")))
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
	nhom = {}
	for d in doc.dong:
		ten_nhom = " ".join(str(d.get("nhom_web") or "").split())
		if not ten_nhom and not chuan_loai(d.get("loai_web")):
			continue
		if frappe.utils.cint(d.khong_tran):
			continue
		ten = ten_nhom or d.ten_banh or d.ma_hang
		nhom.setdefault(banh_web.khoa_banh(ten), {"ten": ten, "ma": []})["ma"].append(d.ma_hang)
	so = 0
	for khoa, g in nhom.items():
		r = frappe.db.sql("select name from `tab%s` where khoa=%%s for update" % banh_web.DT, (khoa,))
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

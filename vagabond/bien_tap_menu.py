"""Biên tập menu theo điểm bán (v640, anh Việt duyệt mẫu 05/11/2026).

Vì sao có mô đun này
--------------------
Trang gọi món tại bàn (v639) lấy đồ uống theo NHÓM MÓN của danh mục và lấy
đá, đường từ doctype tự dựng "Vagabond Tuy Chon Mon" (khai trên Desk, một
nhóm "Đá / Đường" gồm cả "Thay sữa yến mạch"); topping thì mọi món nước pha
đều được chọn hết. Anh Việt chụp trên iPhone: Kombucha hiện "Thay sữa yến
mạch", "Thêm Cà phê phin", đá và đường lẫn một khung. Anh chốt:

- Thêm màn "Biên tập menu" trong phân hệ Bán hàng: kéo thả nhóm và món, ẩn
  hiện trên web, đá và đường là nhóm tuỳ chọn riêng (chọn một, có mặc định),
  bảng topping theo nhóm món, sửa riêng từng món.
- Bản nháp rồi mới Xuất bản; xuất bản là trang bàn và màn Tính tiền đổi cùng
  lúc. Giá CHỈ XEM (sửa giá vẫn ở danh mục, bảng giá điểm).
- MỖI ĐIỂM MỘT MENU (NVHTN 20 m2, menu ít hơn hẳn).

Một nguồn
---------
`menu_hien_hanh(diem)` là chỗ DUY NHẤT trang bàn (kiem_kho feed và cửa gọi
món goi_mon_ban.bang_mon) và màn Tính tiền (ban_hang.pos_ds_tuy_chon) đọc
menu. Điểm chưa xuất bản bản nào thì dựng menu mặc định từ dữ liệu cũ (cùng
món, cùng nhóm, đá và đường tách khỏi khung chung), để hành vi không gãy giữa
lúc deploy và lúc quản lý xuất bản bản đầu.

Nội dung menu (JSON trong Vagabond Menu.noi_dung)
-------------------------------------------------
{
  "nhom": [{"ma": "banh", "ten": "Bánh trên tủ", "loai": "banh", "hien": 1},
           {"ma": "n-tra", "ten": "Trà", "loai": "nuoc", "hien": 1, "goc": "Trà",
            "mon": ["NUTR00021", ...]}],
  "an": ["mã món ẩn trên web"],
  "tuy_chon": [{"ten": "Đá", "muc": ["Bình thường", "50% đá"], "mac_dinh": "Bình thường",
                "ap": ["n-tra", ...]}],
  "topping": {"TPNC00001": ["n-tra", ...]},
  "mon": {"NUTR00021": {"mo_ta": "...", "anh": "/files/menu-nutr00021.jpg", "tat_tc": ["Đường"], "tat_tp": ["TPNC00001"],
                         "bat_tc": ["Nhiệt độ"], "bat_tp": ["TPNC00007"]}}
}
v642 (anh Việt 06/11/2026): mỗi tuỳ chọn, mỗi topping của một món có ba nấc:
Theo nhóm (không ghi gì), Có (bat_tc / bat_tp: bật riêng dù nhóm không áp),
Không (tat_tc / tat_tp). Một mục không nằm cả hai danh sách; mục có trong cả
hai (dữ liệu sửa tay) thì Không thắng.
Món nước chưa nằm trong nhóm nào ("Món mới chưa xếp") thì ẩn trên web; màn
Tính tiền vẫn hỏi tuỳ chọn theo nhóm có cùng nhóm gốc.
"""

import json
import re
import unicodedata

# ------------------------------------------------------------- phần thuần

DT = "Vagabond Menu"
NHAP = "Nháp"
XUAT = "Xuất bản"
MA_BANH = "banh"
TEN_BANH = "Bánh trên tủ"
MUC_MAC_DINH = "Bình thường"
TEN_KHAC = "Tuỳ chọn khác"
# Thứ tự và nhãn nhóm nước mặc định, trùng goi_mon_ban.NHOM_NUOC.
NHOM_GOC = ("Trà", "Cà phê", "Matcha", "Cacao", "Ice Cream - Kem")
NHAN_GOC = {"Ice Cream - Kem": "Kem"}
NHOM_TOI_DA = 30
TC_TOI_DA = 12
MUC_TOI_DA = 12
DAI_TEN = 40
DAI_MUC = 40
DAI_MO_TA = 300
LICH_SU = 10
MAU_MA_NHOM = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
MAU_DA = re.compile(r"(?<!\w)đá(?!\w)", re.I)
MAU_DUONG = re.compile(r"(?<!\w)đường(?!\w)", re.I)
# v645 (anh Việt 08/11/2026): ảnh riêng cho web của một món, do màn Biên tập
# menu cắt vuông và nén rồi tải lên tệp công khai. Chỉ nhận đúng dạng đường dẫn
# tệp công khai của Frappe: không /private (khách không mở được), không link
# ngoài, không ký tự lạ.
MAU_ANH = re.compile(r"^/files/[A-Za-z0-9][A-Za-z0-9._-]{0,139}\.(?:jpe?g|png|webp)$", re.I)


def bo_dau(s):
	"""Chữ không dấu, thường. THUẦN."""
	s = unicodedata.normalize("NFD", str(s or "").lower().replace("đ", "d"))
	return "".join(c for c in s if unicodedata.category(c) != "Mn")


def ma_nhom(goc):
	"""Mã nhóm hiển thị dựng từ tên: "Cà phê" -> "n-ca-phe". THUẦN."""
	s = re.sub(r"[^a-z0-9]+", "-", bo_dau(goc)).strip("-")[:36]
	return "n-" + (s or "nhom")


def _str(v, dai):
	return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()[:dai]


def tach_tuy_chon_cu(ds_tc):
	"""Dòng "Vagabond Tuy Chon Mon" cũ ([{nhom, lua_chon, nhom_mon}]) -> các nhóm
	tuỳ chọn mới: mức có chữ "đá" vào nhóm Đá, chữ "đường" vào nhóm Đường (đều
	thêm "Bình thường" làm mặc định), phần còn lại giữ tên nhóm cũ hoặc vào
	"Tuỳ chọn khác". Kèm `ap_goc` (nhóm món gốc được áp, rỗng là mọi nhóm). THUẦN."""
	theo_ten, thu_tu = {}, []

	def gom(ten, muc, mac_dinh, ap_goc):
		if not muc:
			return
		if ten not in theo_ten:
			theo_ten[ten] = {"ten": ten, "muc": [], "mac_dinh": mac_dinh, "ap_goc": list(ap_goc)}
			thu_tu.append(ten)
		else:
			g = theo_ten[ten]
			# Rỗng nghĩa là mọi nhóm: gộp với rỗng vẫn là mọi nhóm.
			g["ap_goc"] = [] if not g["ap_goc"] or not ap_goc else sorted(set(g["ap_goc"]) | set(ap_goc))
		g = theo_ten[ten]
		for x in ([mac_dinh] if mac_dinh else []) + muc:
			if x not in g["muc"]:
				g["muc"].append(x)

	for n in ds_tc or []:
		lc = [_str(x, DAI_MUC) for x in (n.get("lua_chon") or []) if _str(x, DAI_MUC)]
		ap = [_str(x, 140) for x in (n.get("nhom_mon") or []) if _str(x, 140)]
		da = [x for x in lc if MAU_DA.search(x) and not MAU_DUONG.search(x)]
		duong = [x for x in lc if MAU_DUONG.search(x)]
		khac = [x for x in lc if x not in da and x not in duong]
		gom("Đá", da, MUC_MAC_DINH, ap)
		gom("Đường", duong, MUC_MAC_DINH, ap)
		gom(_str(n.get("nhom"), DAI_TEN) if not (da or duong) and _str(n.get("nhom"), DAI_TEN) else TEN_KHAC, khac, "", ap)
	return [theo_ten[t] for t in thu_tu]


def _thu_tu_goc(goc):
	return (NHOM_GOC.index(goc), "") if goc in NHOM_GOC else (len(NHOM_GOC), bo_dau(goc))


def menu_mac_dinh(do_uong, topping, ds_tc):
	"""Menu dựng từ dữ liệu cũ cho điểm chưa xuất bản bản nào: Bánh trên tủ,
	rồi mỗi nhóm món nước một nhóm (theo thứ tự đang có), đá và đường tách
	riêng, topping áp cho mọi nhóm nước như v639. THUẦN.

	do_uong: [{ma, ten, nhom_goc}] (thứ tự đang hiện); topping: [{ma}]."""
	theo_goc = {}
	for x in do_uong or []:
		goc = str(x.get("nhom_goc") or "").strip()
		if goc:
			theo_goc.setdefault(goc, []).append(str(x["ma"]))
	nhom = [{"ma": MA_BANH, "ten": TEN_BANH, "loai": "banh", "hien": 1}]
	for goc in sorted(theo_goc, key=_thu_tu_goc):
		nhom.append({"ma": ma_nhom(goc), "ten": NHAN_GOC.get(goc, goc), "loai": "nuoc", "hien": 1, "goc": goc,
			"mon": theo_goc[goc]})
	nuoc = [g for g in nhom if g["loai"] == "nuoc"]
	tuy_chon = []
	for t in tach_tuy_chon_cu(ds_tc):
		ap = [g["ma"] for g in nuoc if not t["ap_goc"] or g["goc"] in t["ap_goc"]]
		tuy_chon.append({"ten": t["ten"], "muc": t["muc"], "mac_dinh": t["mac_dinh"], "ap": ap})
	return {
		"nhom": nhom, "an": [], "tuy_chon": tuy_chon,
		"topping": {str(t["ma"]): [g["ma"] for g in nuoc] for t in topping or []},
		"mon": {},
	}


def chuan_menu(menu, ma_hop_le, tp_hop_le, banh_hop_le=()):
	"""Menu quản lý gửi lên -> menu đã chuẩn hoá. Sai cấu trúc thì ValueError với
	câu quản lý đọc được; mã món, mã topping không còn trong danh mục thì lặng
	lẽ bỏ (món vừa ngừng bán giữa lúc sửa). THUẦN.

	ma_hop_le: tập mã món nước của điểm; tp_hop_le: tập mã topping của điểm;
	banh_hop_le (v652): mã bánh từng bày ở tủ của điểm. Bánh chỉ giữ ảnh và mô tả
	riêng trên web, không vào nhóm nước, không tuỳ chọn, không topping."""
	if isinstance(menu, str):
		try:
			menu = json.loads(menu or "{}")
		except ValueError:
			raise ValueError("Menu gửi lên không đọc được. Tải lại màn rồi sửa lại.")
	if not isinstance(menu, dict):
		raise ValueError("Menu gửi lên không đọc được. Tải lại màn rồi sửa lại.")
	ma_hop_le, tp_hop_le = set(ma_hop_le or []), set(tp_hop_le or [])
	banh_hop_le = set(banh_hop_le or []) - ma_hop_le
	nhom_vao = menu.get("nhom") or []
	if not isinstance(nhom_vao, list) or len(nhom_vao) > NHOM_TOI_DA:
		raise ValueError("Menu tối đa %d nhóm." % NHOM_TOI_DA)
	nhom, da_ma, da_mon, co_banh = [], set(), set(), False
	for g in nhom_vao:
		if not isinstance(g, dict):
			raise ValueError("Có nhóm không đọc được. Tải lại màn rồi sửa lại.")
		loai = "banh" if g.get("loai") == "banh" else "nuoc"
		if loai == "banh":
			if co_banh:
				continue
			co_banh = True
			nhom.append({"ma": MA_BANH, "ten": _str(g.get("ten"), DAI_TEN) or TEN_BANH, "loai": "banh",
				"hien": 1 if g.get("hien", 1) else 0})
			continue
		ma = str(g.get("ma") or "").strip().lower()
		if not MAU_MA_NHOM.match(ma) or ma == MA_BANH:
			raise ValueError("Có nhóm mang mã không hợp lệ. Tải lại màn rồi sửa lại.")
		if ma in da_ma:
			raise ValueError("Hai nhóm trùng mã. Tải lại màn rồi sửa lại.")
		ten = _str(g.get("ten"), DAI_TEN)
		if not ten:
			raise ValueError("Có nhóm chưa có tên. Đặt tên cho nhóm rồi lưu lại.")
		mon = []
		for x in g.get("mon") or []:
			x = str(x or "").strip()
			if x in ma_hop_le and x not in da_mon:
				da_mon.add(x)
				mon.append(x)
		da_ma.add(ma)
		nhom.append({"ma": ma, "ten": ten, "loai": "nuoc", "hien": 1 if g.get("hien", 1) else 0,
			"goc": _str(g.get("goc"), 140), "mon": mon})
	if not co_banh:
		nhom.insert(0, {"ma": MA_BANH, "ten": TEN_BANH, "loai": "banh", "hien": 1})
	ten_nhom = {}
	for g in nhom:
		k = bo_dau(g["ten"])
		if k in ten_nhom:
			raise ValueError("Hai nhóm cùng tên \"%s\". Đổi tên một nhóm rồi lưu lại." % g["ten"])
		ten_nhom[k] = 1
	ma_nuoc = [g["ma"] for g in nhom if g["loai"] == "nuoc"]

	tc_vao = menu.get("tuy_chon") or []
	if not isinstance(tc_vao, list) or len(tc_vao) > TC_TOI_DA:
		raise ValueError("Tối đa %d nhóm tuỳ chọn." % TC_TOI_DA)
	tuy_chon, ten_tc = [], set()
	for t in tc_vao:
		if not isinstance(t, dict):
			raise ValueError("Có nhóm tuỳ chọn không đọc được. Tải lại màn rồi sửa lại.")
		ten = _str(t.get("ten"), DAI_TEN)
		if not ten:
			raise ValueError("Có nhóm tuỳ chọn chưa có tên.")
		if bo_dau(ten) in ten_tc:
			raise ValueError("Hai nhóm tuỳ chọn cùng tên \"%s\"." % ten)
		ten_tc.add(bo_dau(ten))
		muc, da = [], set()
		for x in t.get("muc") or []:
			x = _str(x, DAI_MUC)
			if x and bo_dau(x) not in da:
				da.add(bo_dau(x))
				muc.append(x)
		if not muc:
			raise ValueError("Nhóm tuỳ chọn \"%s\" chưa có mức nào." % ten)
		if len(muc) > MUC_TOI_DA:
			raise ValueError("Nhóm tuỳ chọn \"%s\" tối đa %d mức." % (ten, MUC_TOI_DA))
		mac_dinh = _str(t.get("mac_dinh"), DAI_MUC)
		if mac_dinh and mac_dinh not in muc:
			mac_dinh = ""
		ap = [m for m in ma_nuoc if m in set(str(x) for x in (t.get("ap") or []))]
		tuy_chon.append({"ten": ten, "muc": muc, "mac_dinh": mac_dinh, "ap": ap})

	tp_vao = menu.get("topping") or {}
	if not isinstance(tp_vao, dict):
		raise ValueError("Bảng topping không đọc được. Tải lại màn rồi sửa lại.")
	topping = {}
	for ma, ap in tp_vao.items():
		ma = str(ma or "").strip()
		if ma in tp_hop_le:
			ap = set(str(x) for x in (ap or []) if isinstance(ap, list))
			topping[ma] = [m for m in ma_nuoc if m in ap]

	an = []
	for x in menu.get("an") or []:
		x = str(x or "").strip()
		if x in ma_hop_le and x not in an:
			an.append(x)

	mon = {}
	mon_vao = menu.get("mon") or {}
	if not isinstance(mon_vao, dict):
		raise ValueError("Phần sửa riêng từng món không đọc được. Tải lại màn rồi sửa lại.")
	ten_tc_dung = {t["ten"] for t in tuy_chon}
	for ma, o in mon_vao.items():
		ma = str(ma or "").strip()
		if (ma not in ma_hop_le and ma not in banh_hop_le) or not isinstance(o, dict):
			continue
		r = {}
		mo_ta = _str(o.get("mo_ta"), DAI_MO_TA)
		if mo_ta:
			r["mo_ta"] = mo_ta
		anh = str(o.get("anh") or "").strip()
		if MAU_ANH.match(anh):
			r["anh"] = anh
		if ma in banh_hop_le:
			if r:
				mon[ma] = r
			continue
		tat_tc = [x for x in (o.get("tat_tc") or []) if x in ten_tc_dung]
		if tat_tc:
			r["tat_tc"] = sorted(set(tat_tc))
		tat_tp = [str(x) for x in (o.get("tat_tp") or []) if str(x) in tp_hop_le]
		if tat_tp:
			r["tat_tp"] = sorted(set(tat_tp))
		bat_tc = [x for x in (o.get("bat_tc") or []) if x in ten_tc_dung and x not in set(tat_tc)]
		if bat_tc:
			r["bat_tc"] = sorted(set(bat_tc))
		bat_tp = [str(x) for x in (o.get("bat_tp") or []) if str(x) in tp_hop_le and str(x) not in set(tat_tp)]
		if bat_tp:
			r["bat_tp"] = sorted(set(bat_tp))
		if r:
			mon[ma] = r
	return {"nhom": nhom, "an": an, "tuy_chon": tuy_chon, "topping": topping, "mon": mon}


def nhom_cua_mon(menu, ma, goc=""):
	"""Nhóm nước chứa món; món chưa xếp thì nhóm có cùng nhóm gốc (cho màn Tính
	tiền hỏi đúng tuỳ chọn). Không có thì None. THUẦN."""
	nuoc = [g for g in (menu or {}).get("nhom") or [] if g.get("loai") == "nuoc"]
	for g in nuoc:
		if ma in (g.get("mon") or []):
			return g
	goc = str(goc or "").strip()
	for g in nuoc if goc else []:
		if g.get("goc") == goc:
			return g
	return None


def tc_cua_mon(menu, ma, goc="", khong_pha=False):
	"""Các nhóm tuỳ chọn của một món: [{nhom, lua_chon, mac_dinh}]. Món đóng sẵn
	(chai, lon) không hỏi. THUẦN."""
	if khong_pha:
		return []
	g = nhom_cua_mon(menu, ma, goc)
	rieng = (menu.get("mon") or {}).get(ma) or {}
	tat, bat = set(rieng.get("tat_tc") or []), set(rieng.get("bat_tc") or [])
	if not g and not bat:
		return []
	gm = g["ma"] if g else None
	# Thứ tự theo bảng tuỳ chọn của menu; nhóm áp hoặc món bật riêng, trừ món tắt riêng.
	return [{"nhom": t["ten"], "lua_chon": list(t["muc"]), "mac_dinh": t.get("mac_dinh") or ""}
		for t in menu.get("tuy_chon") or []
		if (gm in (t.get("ap") or []) or t["ten"] in bat) and t["ten"] not in tat]


def tp_cua_mon(menu, ma, goc="", khong_pha=False):
	"""Mã topping được chọn kèm một món. Món đóng sẵn không có topping. THUẦN."""
	if khong_pha:
		return []
	g = nhom_cua_mon(menu, ma, goc)
	rieng = (menu.get("mon") or {}).get(ma) or {}
	tat, bat = set(rieng.get("tat_tp") or []), [str(x) for x in rieng.get("bat_tp") or []]
	if not g and not bat:
		return []
	gm = g["ma"] if g else None
	ra = [tp for tp, ap in (menu.get("topping") or {}).items() if gm in (ap or []) and tp not in tat]
	# Topping bật riêng mà bảng nhóm chưa có dòng nào (chưa áp nhóm nào) vẫn kèm được.
	return ra + [tp for tp in bat if tp not in ra and tp not in tat]


def ap_menu(menu, do_uong):
	"""Menu + đồ uống đang bán của điểm -> (các nhóm hiện trên web theo thứ tự,
	đồ uống theo thứ tự nhóm rồi thứ tự món). Nhóm tắt, món ẩn, món chưa xếp
	không lên web; nhóm nước không còn món nào thì không hiện. Mỗi đồ uống có
	thêm nhom_hien (mã nhóm), tc, tp (mã topping được kèm), mô tả và ảnh sửa riêng. THUẦN."""
	theo_ma = {str(x["ma"]): x for x in do_uong or []}
	an = set(menu.get("an") or [])
	nhom_ra, uong_ra = [], []
	for g in menu.get("nhom") or []:
		if not g.get("hien", 1):
			continue
		if g.get("loai") == "banh":
			nhom_ra.append({"ma": MA_BANH, "ten": g.get("ten") or TEN_BANH, "loai": "banh"})
			continue
		cac = []
		for ma in g.get("mon") or []:
			x = theo_ma.get(ma)
			if not x or ma in an:
				continue
			kp = bool(x.get("khong_pha"))
			y = dict(x)
			y["nhom_hien"] = g["ma"]
			y["tc"] = tc_cua_mon(menu, ma, x.get("nhom_goc"), kp)
			y["tp"] = tp_cua_mon(menu, ma, x.get("nhom_goc"), kp)
			mo_ta = ((menu.get("mon") or {}).get(ma) or {}).get("mo_ta")
			if mo_ta:
				y["mo_ta"] = mo_ta
			# v645: ảnh riêng cho web đứng trước ảnh danh mục; ảnh quầy (POS) không đổi.
			anh = ((menu.get("mon") or {}).get(ma) or {}).get("anh")
			if anh:
				y["anh"] = anh
			cac.append(y)
		if cac:
			nhom_ra.append({"ma": g["ma"], "ten": g["ten"], "loai": "nuoc"})
			uong_ra.extend(cac)
	return nhom_ra, uong_ra


def rieng_banh(menu, ma, anh_goc, mo_ta_goc):
	"""v652 (anh Việt 12/11/2026, Minh Vũ không vào được danh mục món): ảnh và mô
	tả bánh khách thấy ở menu tại quầy, trang bàn. Sửa riêng trong Biên tập menu
	thì dùng bản riêng, để trống thì dùng danh mục món. Trả (ảnh, mô tả). THUẦN."""
	r = ((menu or {}).get("mon") or {}).get(str(ma or "")) or {}
	return (r.get("anh") or anh_goc or ""), (r.get("mo_ta") or mo_ta_goc or "")


def tc_cho_quay(menu, do_uong):
	"""Tuỳ chọn cho màn Tính tiền: {"mon": {mã: [nhóm]}, "tc": [nhóm + nhom_mon]}.
	"mon" phủ mọi đồ uống của điểm (đã xếp hay chưa, kể cả món ẩn trên web: quầy
	vẫn bán), kể cả món không có tuỳ chọn nào (danh sách rỗng). "tc" theo nhóm món gốc cho món ngoài danh sách. THUẦN."""
	mon = {}
	for x in do_uong or []:
		# Giữ cả danh sách RỖNG (món đóng chai, món quản lý tắt hết tuỳ chọn):
		# rỗng nghĩa là "không hỏi gì", khác hẳn "chưa có trong bảng tra" (Codex
		# PR #543: bỏ mục rỗng thì quầy rơi về tuỳ chọn theo nhóm gốc).
		mon[str(x["ma"])] = tc_cua_mon(menu, str(x["ma"]), x.get("nhom_goc"), bool(x.get("khong_pha")))
	goc_cua = {g["ma"]: g.get("goc") or "" for g in menu.get("nhom") or [] if g.get("loai") == "nuoc"}
	tc = []
	for t in menu.get("tuy_chon") or []:
		goc = sorted({goc_cua.get(m) for m in t.get("ap") or [] if goc_cua.get(m)})
		# Không áp nhóm nào thì bỏ hẳn: danh sách nhóm món rỗng ở bản cũ nghĩa là
		# "mọi nhóm", để lại là áp nhầm cho cả quầy.
		if goc:
			tc.append({"nhom": t["ten"], "lua_chon": list(t["muc"]), "mac_dinh": t.get("mac_dinh") or "", "nhom_mon": goc})
	return {"mon": mon, "tc": tc}


def mon_chua_xep(menu, do_uong):
	"""Mã đồ uống của điểm chưa nằm trong nhóm nào, theo thứ tự danh mục. THUẦN."""
	da = {m for g in (menu or {}).get("nhom") or [] for m in g.get("mon") or []}
	return [str(x["ma"]) for x in do_uong or [] if str(x["ma"]) not in da]


def _ds_ten(ds):
	ds = list(ds)
	return ", ".join(ds[:4]) + (" và %d nữa" % (len(ds) - 4) if len(ds) > 4 else "") if ds else "không nhóm nào"


def khac_nhau(cu, moi, ten):
	"""Danh sách câu tiếng Việt mô tả thay đổi từ menu cũ sang menu mới, cho màn
	Xem và xuất bản và cột "Thay đổi" của bản xuất bản. ten: {mã món/topping:
	tên}. THUẦN."""
	cu, moi, ten = cu or {}, moi or {}, ten or {}
	ra = []
	gc = {g["ma"]: g for g in cu.get("nhom") or []}
	gm = {g["ma"]: g for g in moi.get("nhom") or []}
	tn = lambda ma, g=None: (gm.get(ma) or gc.get(ma) or {}).get("ten") or ma
	for ma, g in gm.items():
		if ma not in gc:
			ra.append("Thêm nhóm %s" % g["ten"])
	for ma, g in gc.items():
		if ma not in gm:
			ra.append("Bỏ nhóm %s" % g["ten"])
	thu_cu = [m for m in (g["ma"] for g in cu.get("nhom") or []) if m in gm]
	thu_moi = [m for m in (g["ma"] for g in moi.get("nhom") or []) if m in gc]
	if thu_cu != thu_moi:
		ra.append("Đổi thứ tự nhóm: %s" % ", ".join(tn(m) for m in thu_moi))
	for ma, g in gm.items():
		c = gc.get(ma)
		if not c:
			continue
		if c.get("ten") != g.get("ten"):
			ra.append("Đổi tên nhóm %s thành %s" % (c.get("ten"), g.get("ten")))
		if int(c.get("hien", 1)) != int(g.get("hien", 1)):
			ra.append(("Hiện nhóm %s trên web" if g.get("hien", 1) else "Ẩn nhóm %s trên web") % g["ten"])
	o_cu = {m: g["ma"] for g in cu.get("nhom") or [] for m in g.get("mon") or []}
	o_moi = {m: g["ma"] for g in moi.get("nhom") or [] for m in g.get("mon") or []}
	for m, g in o_moi.items():
		if m not in o_cu:
			ra.append("Xếp %s vào nhóm %s" % (ten.get(m, m), tn(g)))
		elif o_cu[m] != g:
			ra.append("Chuyển %s từ %s sang %s" % (ten.get(m, m), tn(o_cu[m]), tn(g)))
	for m, g in o_cu.items():
		if m not in o_moi:
			ra.append("Bỏ %s khỏi nhóm %s" % (ten.get(m, m), tn(g)))
	for ma, g in gm.items():
		c = gc.get(ma)
		if c and c.get("loai") == "nuoc":
			chung = [m for m in g.get("mon") or [] if m in (c.get("mon") or [])]
			chung_cu = [m for m in c.get("mon") or [] if m in (g.get("mon") or [])]
			if chung != chung_cu:
				ra.append("%s: đổi thứ tự món" % g["ten"])
	an_cu, an_moi = set(cu.get("an") or []), set(moi.get("an") or [])
	for m in sorted(an_moi - an_cu, key=lambda x: ten.get(x, x)):
		ra.append("Ẩn %s trên web" % ten.get(m, m))
	for m in sorted(an_cu - an_moi, key=lambda x: ten.get(x, x)):
		ra.append("Hiện lại %s trên web" % ten.get(m, m))
	tc_cu = {t["ten"]: t for t in cu.get("tuy_chon") or []}
	tc_moi = {t["ten"]: t for t in moi.get("tuy_chon") or []}
	for t in tc_moi:
		if t not in tc_cu:
			ra.append("Thêm tuỳ chọn %s" % t)
	for t in tc_cu:
		if t not in tc_moi:
			ra.append("Bỏ tuỳ chọn %s" % t)
	for t, v in tc_moi.items():
		c = tc_cu.get(t)
		if not c:
			continue
		if c.get("muc") != v.get("muc"):
			ra.append("%s: các mức %s" % (t, ", ".join(v.get("muc") or [])))
		if (c.get("mac_dinh") or "") != (v.get("mac_dinh") or ""):
			ra.append("%s: mặc định %s" % (t, v.get("mac_dinh") or "không có"))
		if set(c.get("ap") or []) != set(v.get("ap") or []):
			ra.append("%s: áp cho %s" % (t, _ds_ten(tn(x) for x in v.get("ap") or [])))
	tp_cu, tp_moi = cu.get("topping") or {}, moi.get("topping") or {}
	for tp in list(tp_moi) + [x for x in tp_cu if x not in tp_moi]:
		if set(tp_cu.get(tp) or []) != set(tp_moi.get(tp) or []):
			ra.append("Topping %s: áp cho %s" % (ten.get(tp, tp), _ds_ten(tn(x) for x in tp_moi.get(tp) or [])))
	mc, mm = cu.get("mon") or {}, moi.get("mon") or {}
	for m in list(mm) + [x for x in mc if x not in mm]:
		a, b = mc.get(m) or {}, mm.get(m) or {}
		if (a.get("mo_ta") or "") != (b.get("mo_ta") or ""):
			ra.append("%s: sửa mô tả trên web" % ten.get(m, m))
		if (a.get("anh") or "") != (b.get("anh") or ""):
			ra.append("%s: %s" % (ten.get(m, m), "đổi ảnh trên web" if b.get("anh") else "về ảnh trong danh mục món"))
		for x in sorted(set(b.get("tat_tc") or []) - set(a.get("tat_tc") or [])):
			ra.append("%s: tắt tuỳ chọn %s" % (ten.get(m, m), x))
		for x in sorted(set(a.get("tat_tc") or []) - set(b.get("tat_tc") or [])):
			ra.append("%s: bật lại tuỳ chọn %s" % (ten.get(m, m), x))
		for x in sorted(set(b.get("tat_tp") or []) - set(a.get("tat_tp") or [])):
			ra.append("%s: tắt topping %s" % (ten.get(m, m), ten.get(x, x)))
		for x in sorted(set(a.get("tat_tp") or []) - set(b.get("tat_tp") or [])):
			ra.append("%s: bật lại topping %s" % (ten.get(m, m), ten.get(x, x)))
		for x in sorted(set(b.get("bat_tc") or []) - set(a.get("bat_tc") or [])):
			ra.append("%s: thêm riêng tuỳ chọn %s" % (ten.get(m, m), x))
		for x in sorted(set(a.get("bat_tc") or []) - set(b.get("bat_tc") or [])):
			ra.append("%s: bỏ tuỳ chọn thêm riêng %s" % (ten.get(m, m), x))
		for x in sorted(set(b.get("bat_tp") or []) - set(a.get("bat_tp") or [])):
			ra.append("%s: thêm riêng topping %s" % (ten.get(m, m), ten.get(x, x)))
		for x in sorted(set(a.get("bat_tp") or []) - set(b.get("bat_tp") or [])):
			ra.append("%s: bỏ topping thêm riêng %s" % (ten.get(m, m), ten.get(x, x)))
	return ra


def doc_noi_dung(s):
	"""Chuỗi JSON đã lưu -> dict menu; hỏng thì None. THUẦN."""
	try:
		v = json.loads(s or "")
	except (TypeError, ValueError):
		return None
	return v if isinstance(v, dict) and isinstance(v.get("nhom"), list) else None


def ghi_noi_dung(menu):
	return json.dumps(menu, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# ------------------------------------------------------------- phần chạm Frappe

import frappe  # noqa: E402
from frappe.utils import cint, now_datetime  # noqa: E402

QUYEN = {"System Manager", "Giám đốc", "VGB - Quản lý cửa hàng"}
TEN_KHOA = "vgb_menu:%s"


def _kiem_quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý cửa hàng mới biên tập menu được.", frappe.PermissionError)


def _diem_co_quay():
	from vagabond import diem_ban

	return [d for d in diem_ban.ds(chi_bat=True) if d.get("quay")]


def _chon_diem(diem):
	ds = _diem_co_quay()
	diem = str(diem or "").strip().upper()
	for d in ds:
		if d["ma"] == diem:
			return d, ds
	if diem:
		frappe.throw("Không có điểm bán %s." % diem)
	if not ds:
		frappe.throw("Chưa có điểm bán nào có quầy.")
	return ds[0], ds


def _dong(diem, loai):
	return frappe.get_all(DT, filters={"diem": diem, "loai": loai},
		fields=["name", "phien", "noi_dung", "luc", "boi", "thay_doi"],
		order_by="phien desc, creation desc", limit_page_length=0, ignore_permissions=True)


def menu_dang_chay(diem):
	"""(menu, phiên) của bản Xuất bản mới nhất; chưa có thì (None, 0)."""
	try:
		ds = frappe.get_all(DT, filters={"diem": diem, "loai": XUAT}, fields=["noi_dung", "phien"],
			order_by="phien desc", limit_page_length=1, ignore_permissions=True)
	except Exception:
		# Site chưa migrate xong doctype: chạy theo dữ liệu cũ, không làm gãy trang bàn.
		return None, 0
	if not ds:
		return None, 0
	return doc_noi_dung(ds[0].get("noi_dung")), cint(ds[0].get("phien"))


SO_NGAY_BANH = 60


def banh_cua_diem(diem, hom_nay=None):
	"""v652: bánh từng bày trên tủ của điểm trong SO_NGAY_BANH ngày gần đây (lấy
	từ bảng Kiểm kho điểm), để quản lý sửa ảnh, mô tả trước khi bánh lên tủ.
	[{ma, ten, anh, mo_ta, gia}] theo tên."""
	from frappe.utils import add_days, getdate

	from vagabond import diem_ban, goi_mon_ban, kiem_kho

	ngay = getdate(hom_nay) if hom_nay else getdate()
	ma = [r[0] for r in frappe.db.sql(
		"select distinct d.ma_hang from `tab%s` d join `tab%s` p on p.name = d.parent "
		"where d.parenttype = %%s and p.diem = %%s and p.ngay between %%s and %%s"
		% (kiem_kho.DT_DONG, kiem_kho.DT), (kiem_kho.DT, diem, add_days(ngay, -SO_NGAY_BANH), ngay)) if r and r[0]]
	if not ma:
		return []
	ds = frappe.get_all("Item", filters={"item_code": ["in", ma], "disabled": 0},
		fields=["item_code", "item_name", "image", "standard_rate", "description"],
		limit_page_length=0, ignore_permissions=True)
	# Giá đúng như khách thấy ở điểm này: bảng giá điểm bán, không có thì giá chung.
	gia_diem = diem_ban.gia_rieng(diem)
	return sorted(({"ma": x["item_code"], "ten": x.get("item_name") or x["item_code"], "anh": x.get("image") or "",
		"mo_ta": goi_mon_ban.mo_ta_ngan(x.get("description")),
		"gia": goi_mon_ban.gia_mon(x["item_code"], gia_diem, x.get("standard_rate") or 0)} for x in ds),
		key=lambda x: bo_dau(x["ten"]))


def _hop_le(do_uong, topping, banh):
	return ({str(x["ma"]) for x in do_uong}, {str(t["ma"]) for t in topping}, {str(b["ma"]) for b in banh or []})


def _du_lieu(diem, hom_nay=None):
	from vagabond import goi_mon_ban

	return goi_mon_ban.do_uong_cua_diem(diem, hom_nay), goi_mon_ban.topping_cua_diem(diem)



def tc_theo_quay(quay):
	"""Tuỳ chọn pha chế cho màn Tính tiền của một quầy: menu đang chạy của
	điểm chứa quầy đó (ban_hang.pos_ds_tuy_chon gọi vào đây; để ở tệp này cho
	bộ kiểm nạp được mà không kéo thư viện mạng của ban_hang)."""
	from vagabond import diem_ban, goi_mon_ban

	diem = diem_ban.ma_theo_quay(quay)
	ds_uong = goi_mon_ban.do_uong_cua_diem(diem)
	menu = menu_hien_hanh(diem, ds_uong, goi_mon_ban.topping_cua_diem(diem))
	return tc_cho_quay(menu, ds_uong)


def menu_hien_hanh(diem, do_uong=None, topping=None):
	"""MỘT NGUỒN menu cho trang bàn và màn Tính tiền: bản đã xuất bản, chưa có thì
	menu mặc định dựng từ dữ liệu cũ."""
	m, _ = menu_dang_chay(diem)
	if m:
		return m
	if do_uong is None or topping is None:
		do_uong, topping = _du_lieu(diem)
	from vagabond import goi_mon_ban

	return menu_mac_dinh(do_uong, topping, goi_mon_ban.doc_tuy_chon())


def _ten_tra(do_uong, topping, banh=()):
	ten = {str(b["ma"]): b.get("ten") or b["ma"] for b in banh or []}
	ten.update({str(x["ma"]): x.get("ten") or x["ma"] for x in do_uong or []})
	ten.update({str(t["ma"]): t.get("ten") or t["ma"] for t in topping or []})
	return ten


def _lay_khoa(ten, giay=10):
	r = frappe.db.sql("select get_lock(%s, %s)", (ten, giay))
	return bool(r and r[0] and cint(r[0][0]) == 1)


def _nha_khoa(ten):
	try:
		frappe.db.sql("select release_lock(%s)", (ten,))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "bien_tap_menu: nhả khoá %s" % ten)


@frappe.whitelist()
def mo(diem=None):
	"""Dữ liệu cho màn Biên tập menu của một điểm: bản nháp (chưa có thì bằng
	menu đang chạy), menu đang chạy, các món nước và topping của điểm (giá chỉ
	xem), danh sách thay đổi, lịch sử xuất bản."""
	_kiem_quyen()
	d, ds = _chon_diem(diem)
	do_uong, topping = _du_lieu(d["ma"])
	dang, phien = menu_dang_chay(d["ma"])
	if not dang:
		from vagabond import goi_mon_ban

		dang = menu_mac_dinh(do_uong, topping, goi_mon_ban.doc_tuy_chon())
	nhap_dong = _dong(d["ma"], NHAP)
	nhap = doc_noi_dung(nhap_dong[0].get("noi_dung")) if nhap_dong else None
	banh = banh_cua_diem(d["ma"])
	ma_hop_le, tp_hop_le, banh_hop_le = _hop_le(do_uong, topping, banh)
	nhap = chuan_menu(nhap or dang, ma_hop_le, tp_hop_le, banh_hop_le)
	dang_sach = chuan_menu(dang, ma_hop_le, tp_hop_le, banh_hop_le)
	ten = _ten_tra(do_uong, topping, banh)
	lich_su = [{"phien": cint(r.phien), "luc": str(r.luc or ""), "boi": r.boi or "", "thay_doi": r.thay_doi or ""}
		for r in _dong(d["ma"], XUAT)[:LICH_SU]]
	return {
		"diem": d["ma"], "ten_diem": d.get("ten_ngan") or d["ten"],
		"cac_diem": [{"ma": x["ma"], "ten": x.get("ten_ngan") or x["ten"]} for x in ds],
		"nhap": nhap, "dang_chay": dang_sach, "phien": phien,
		"thay_doi": khac_nhau(dang_sach, nhap, ten),
		"nhap_boi": (nhap_dong[0].get("boi") or "") if nhap_dong else "",
		"nhap_luc": str(nhap_dong[0].get("luc") or "") if nhap_dong else "",
		"mon": [{"ma": x["ma"], "ten": x["ten"], "gia": x["gia"], "anh": x.get("anh") or "", "goc": x.get("nhom_goc") or "",
			"khong_pha": int(x.get("khong_pha") or 0), "mo_ta": x.get("mo_ta") or "", "ban_web": int(x.get("ban_web", 1))}
			for x in do_uong],
		"topping": [{"ma": t["ma"], "ten": t["ten"], "gia": t["gia"]} for t in topping],
		# v652: bánh từng bày ở tủ điểm này, sửa ảnh và mô tả riêng cho menu tại quầy.
		"banh": banh,
		"chua_xep": mon_chua_xep(nhap, do_uong),
		"lich_su": lich_su,
	}


def _luu_nhap(diem, menu):
	ds = _dong(diem, NHAP)
	if ds:
		frappe.db.set_value(DT, ds[0]["name"], {"noi_dung": ghi_noi_dung(menu), "luc": now_datetime(),
			"boi": frappe.session.user}, update_modified=True)
		return ds[0]["name"]
	doc = frappe.get_doc({"doctype": DT, "diem": diem, "loai": NHAP, "phien": 0, "noi_dung": ghi_noi_dung(menu),
		"luc": now_datetime(), "boi": frappe.session.user})
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist(methods=["POST"])
def luu_nhap(diem=None, noi_dung=None):
	"""Lưu bản nháp (khách chưa thấy). Trả danh sách thay đổi so với menu đang chạy."""
	_kiem_quyen()
	d, _ = _chon_diem(diem)
	do_uong, topping = _du_lieu(d["ma"])
	banh = banh_cua_diem(d["ma"])
	ma_hop_le, tp_hop_le, banh_hop_le = _hop_le(do_uong, topping, banh)
	try:
		menu = chuan_menu(noi_dung, ma_hop_le, tp_hop_le, banh_hop_le)
	except ValueError as e:
		frappe.throw(str(e))
	_luu_nhap(d["ma"], menu)
	frappe.db.commit()
	dang = chuan_menu(menu_hien_hanh(d["ma"], do_uong, topping), ma_hop_le, tp_hop_le, banh_hop_le)
	return {"ok": 1, "thay_doi": khac_nhau(dang, menu, _ten_tra(do_uong, topping, banh)),
		"chua_xep": mon_chua_xep(menu, do_uong)}


def _xuat(diem, menu, thay_doi):
	"""Ghi một bản Xuất bản phiên mới trong khoá theo điểm (hai quản lý bấm cùng
	lúc không ra hai bản trùng phiên). Trả số phiên."""
	khoa = TEN_KHOA % diem
	if not _lay_khoa(khoa, 10):
		frappe.throw("Menu điểm này đang được xuất bản. Đợi vài giây rồi bấm lại.")
	try:
		_, phien = menu_dang_chay(diem)
		phien = cint(phien) + 1
		doc = frappe.get_doc({"doctype": DT, "diem": diem, "loai": XUAT, "phien": phien,
			"noi_dung": ghi_noi_dung(menu), "luc": now_datetime(), "boi": frappe.session.user,
			"thay_doi": "\n".join(thay_doi)[:2000] or "Xuất bản lại, không đổi gì"})
		doc.insert(ignore_permissions=True)
		_luu_nhap(diem, menu)
		frappe.db.commit()
		return phien
	finally:
		_nha_khoa(khoa)


@frappe.whitelist(methods=["POST"])
def xuat_ban(diem=None):
	"""Bản nháp thành menu đang chạy: trang bàn và màn Tính tiền đổi cùng lúc."""
	_kiem_quyen()
	d, _ = _chon_diem(diem)
	do_uong, topping = _du_lieu(d["ma"])
	banh = banh_cua_diem(d["ma"])
	ma_hop_le, tp_hop_le, banh_hop_le = _hop_le(do_uong, topping, banh)
	nhap_dong = _dong(d["ma"], NHAP)
	nhap = doc_noi_dung(nhap_dong[0].get("noi_dung")) if nhap_dong else None
	if not nhap:
		frappe.throw("Chưa có bản nháp nào để xuất bản.")
	nhap = chuan_menu(nhap, ma_hop_le, tp_hop_le, banh_hop_le)
	dang = chuan_menu(menu_hien_hanh(d["ma"], do_uong, topping), ma_hop_le, tp_hop_le, banh_hop_le)
	thay_doi = khac_nhau(dang, nhap, _ten_tra(do_uong, topping, banh))
	_, phien_cu = menu_dang_chay(d["ma"])
	if not thay_doi and phien_cu:
		return {"ok": 1, "phien": phien_cu, "khong_doi": 1}
	return {"ok": 1, "phien": _xuat(d["ma"], nhap, thay_doi), "thay_doi": thay_doi}


@frappe.whitelist(methods=["POST"])
def bo_nhap(diem=None):
	"""Bỏ bản nháp: nháp trở về đúng menu đang chạy."""
	_kiem_quyen()
	d, _ = _chon_diem(diem)
	_luu_nhap(d["ma"], menu_hien_hanh(d["ma"]))
	frappe.db.commit()
	return {"ok": 1}


@frappe.whitelist(methods=["POST"])
def khoi_phuc(diem=None, phien=None):
	"""Quay về một bản đã xuất bản trước: xuất bản lại nội dung đó thành phiên mới."""
	_kiem_quyen()
	d, _ = _chon_diem(diem)
	phien = cint(phien)
	ds = [r for r in _dong(d["ma"], XUAT) if cint(r.phien) == phien]
	cu = doc_noi_dung(ds[0].get("noi_dung")) if ds else None
	if not cu:
		frappe.throw("Không tìm thấy bản xuất bản phiên %s." % phien)
	do_uong, topping = _du_lieu(d["ma"])
	banh = banh_cua_diem(d["ma"])
	ma_hop_le, tp_hop_le, banh_hop_le = _hop_le(do_uong, topping, banh)
	cu = chuan_menu(cu, ma_hop_le, tp_hop_le, banh_hop_le)
	dang = chuan_menu(menu_hien_hanh(d["ma"], do_uong, topping), ma_hop_le, tp_hop_le, banh_hop_le)
	thay_doi = ["Quay về bản phiên %d" % phien] + khac_nhau(dang, cu, _ten_tra(do_uong, topping, banh))
	return {"ok": 1, "phien": _xuat(d["ma"], cu, thay_doi)}

# -*- coding: utf-8 -*-
"""Thống kê giao diện app /bep cho việc "Nghệ sĩ công nghệ" (PR 0).

    python3 cong_cu/thong_ke_ui_nghe_si.py           ghi lại hai tệp trong docs/ui-nghe-si/
    python3 cong_cu/thong_ke_ui_nghe_si.py --kiem    chỉ so, lệch thì trả mã 1

Chỉ ĐỌC mã nguồn trong vagabond/public/js/bep/. Không sửa phần nào của app,
không chạm Frappe, không cần requests.

Sinh ra:
  docs/ui-nghe-si/danh-muc-man.md   mọi màn (hàm scr...), hộp thoại, nhóm PR,
                                    thành phần dùng chung, trạng thái cần kiểm
  docs/ui-nghe-si/thong-ke-kieu.md  màu, emoji, cỡ chữ, bo góc, khoảng cách,
                                    kiểu viết trong thẻ, theo từng phần

Giới hạn đã biết (ghi thật, không giấu):
  - Đọc tĩnh bằng biểu thức chính quy, không chạy app. Màn dựng tiêu đề bằng
    biến thì cột tiêu đề ghi "(động)".
  - Nhóm PR gán theo đường đi ngắn nhất từ ô trang chủ (VGB_NHOM, vgbGo).
    Màn không tới được từ ô nào thì ghi "chưa xếp", người làm xếp tay.
  - Cột vai chỉ là các vai NHẮC TÊN trong thân hàm màn. Quyền thật nằm ở máy
    chủ (quyen_phan_he.py) và docs/quyen-theo-phan-he.md.
"""

import io
import os
import re
import sys
from collections import Counter, OrderedDict, deque

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEP = os.path.join(GOC, "vagabond", "public", "js", "bep")
RA = os.path.join(GOC, "docs", "ui-nghe-si")

# Nhóm trang chủ -> PR con (bản 4 mục 1). Thu mua đi cùng Kho vì chung luồng
# hàng vào; Báo cáo, Nhân sự, Danh mục, Cài đặt là "các màn còn lại".
PR_THEO_NHOM = OrderedDict([
	("BH", 2), ("GH", 2),
	("DH", 3), ("SX", 3), ("NK", 3), ("XK", 3), ("KK", 3), ("TM", 3),
	("KT", 4), ("TC", 4),
	("KHG", 5), ("BC", 5), ("NS", 5), ("DM", 5), ("KHAC", 5),
])

# Màn thuộc khung nền, PR 1 chuyển cùng khung chung.
MAN_NEN = ("scrHome", "scrNhom", "scrLogin", "scrAccount")
# Màn mở từ ô riêng trên trang chủ hoặc từ chuông, không thuộc nhóm nào: đi cùng "các màn còn lại".
MAN_CON_LAI = ("scrChuong", "scrSoTay", "scrHuongDan", "scrVclList")

HOP_THOAI_CHUNG = ("hopKhung", "hoiChon", "hoiChonNhieu", "hoiChu", "hoiSo", "hoiNgay", "hoiCo",
	"baoTin", "hoiNhap", "xacNhan", "pickDate", "sheet", "confirmSheet")

RE_HAM = re.compile(r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", re.M)
RE_TEN = re.compile(r"\b([A-Za-z_$][\w$]*)\b")
RE_FRAME = re.compile(r"\bframe\(\s*('(?:[^'\\]|\\.)*'|[^,)]+)")
RE_VAI = re.compile(r"hasRole\(\s*'([^']+)'")
RE_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RE_CO_CHU = re.compile(r"font-size\s*:\s*([0-9.]+)px")
RE_BO_GOC = re.compile(r"border-radius\s*:\s*([^;\"'}\n]+)")
RE_KHOANG = re.compile(r"\b(padding|margin|gap)(?:-(?:top|right|bottom|left))?\s*:\s*([^;\"'}\n]+)")
RE_PHONG = re.compile(r"font-family\s*:\s*([^;\"'}\n]+)")
RE_MAU_VAI = re.compile(r"\b(color|background(?:-color)?|border(?:-(?:top|right|bottom|left))?(?:-color)?|box-shadow|fill|stroke)\s*:\s*([^;\"'}\n]*)")
RE_THUC_THE = re.compile(r"&#(\d+);")


def la_emoji(c):
	"""Ký tự hình (emoji, ký hiệu trang trí), không tính chữ và dấu câu."""
	o = ord(c)
	return (0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF
		or 0x2300 <= o <= 0x23FF or 0x2190 <= o <= 0x21FF or 0x25A0 <= o <= 0x25FF)


def doc_cac_phan(thu_muc=None):
	thu_muc = thu_muc or BEP
	ds = sorted(t for t in os.listdir(thu_muc) if re.match(r"^\d\d-[a-z0-9-]+\.js$", t))
	return OrderedDict((t, io.open(os.path.join(thu_muc, t), encoding="utf-8").read()) for t in ds)


def tach_ham(cac_phan):
	"""Hàm ở mức ngoài cùng (khai ở cột 0). Thân hàm kéo tới hàm cột 0 kế tiếp."""
	ham = OrderedDict()
	for tep, ma in cac_phan.items():
		moc = [(m.start(), m.group(1)) for m in RE_HAM.finditer(ma)]
		for i, (vt, ten) in enumerate(moc):
			het = moc[i + 1][0] if i + 1 < len(moc) else len(ma)
			# Hàm khai sau đè hàm khai trước (cùng một vỏ hàm): giữ bản sau.
			ham[ten] = {"tep": tep, "than": ma[vt:het], "dong": ma.count("\n", 0, vt) + 1}
	return ham


def doc_nhom(ma_trang_chu):
	"""Bảng VGB_NHOM: [(khoá nhóm, tên, [khoá ô])]."""
	bd = ma_trang_chu.find("var VGB_NHOM = [")
	if bd < 0:
		return []
	kt = ma_trang_chu.find("\nvar VGB_HUB", bd)
	khoi = ma_trang_chu[bd:kt if kt > 0 else len(ma_trang_chu)]
	kq = []
	for m in re.finditer(r"k:\s*'(\w+)',\s*ten:\s*'([^']+)',\s*icon:\s*'[^']*',\s*keys:\s*(\[[^\]]*\]|VGB_DM[^\n]*)", khoi):
		khoa = re.findall(r"'([^']+)'", m.group(3)) if m.group(3).startswith("[") else ["DM:*"]
		kq.append((m.group(1), m.group(2), khoa))
	return kq


def doc_dinh_tuyen(than_vgbgo):
	"""vgbGo: khoá ô -> [tên hàm màn] (đọc từng dòng if (k === 'X'))."""
	kq = OrderedDict()
	for dong in than_vgbgo.split("\n"):
		m = re.search(r"k\s*===\s*'([^']+)'", dong)
		if not m:
			continue
		kq[m.group(1)] = sorted(set(re.findall(r"\b(scr[A-Z]\w*)\b", dong)))
	return kq


def do_thi(ham):
	"""Ai nhắc tên ai. Bỏ các hàm tổng đài (nhắc quá nhiều màn) để không loang."""
	ten_ham = set(ham)
	canh = {}
	for ten, h in ham.items():
		goi = set(RE_TEN.findall(h["than"])) & ten_ham
		goi.discard(ten)
		canh[ten] = goi
	tong_dai = set(t for t, g in canh.items() if len([x for x in g if x.startswith("scr")]) > 25)
	return canh, tong_dai


def xep_nhom(ham, nhom, tuyen, canh, tong_dai):
	"""Mỗi màn về nhóm có đường đi ngắn nhất từ ô trang chủ; hoà thì nhóm đứng trước."""
	tot = {}
	for thu_tu, (k, _ten, khoa) in enumerate(nhom):
		goc = []
		for kh in khoa:
			goc.extend(tuyen.get(kh, []))
		xa = {}
		hang = deque((g, 0) for g in goc if g in ham)
		while hang:
			t, d = hang.popleft()
			if t in xa or t in tong_dai:
				continue
			xa[t] = d
			for g in canh.get(t, ()):
				if g not in xa:
					hang.append((g, d + 1))
		for t, d in xa.items():
			if t.startswith("scr") and (t not in tot or (d, thu_tu) < tot[t][:2]):
				tot[t] = (d, thu_tu, k)
	return dict((t, v[2]) for t, v in tot.items())


# Hàm hạ tầng: ai cũng gọi, thân của chúng không nói gì về riêng một màn.
HA_TANG = ("frame", "go", "api", "toast", "h", "vgbGomNhom", "scrHome")
SAU_TOI_DA = 4


def than_gop(ten, ham, canh, tong_dai):
	"""Thân màn CỘNG thân các hàm vẽ phụ nó gọi (Codex #598).

	Màn hay dựng nội dung qua hàm phụ (scrDanhMuc gọi dmDraw). Chỉ đọc thân
	hàm scr thì ghi sót thành phần, PR sửa khung chung tra bảng sẽ bỏ sót màn.
	Đi theo lời gọi tới hàm KHÔNG phải màn, sâu tối đa SAU_TOI_DA tầng; dừng ở
	màn khác (đó là màn riêng, có dòng riêng), ở hàm tổng đài, ở bộ hộp thoại
	chung và ở hàm hạ tầng. Thà ghi dư một thành phần còn hơn ghi sót: dư thì
	kiểm thừa một màn, sót thì lọt một màn hỏng.
	"""
	da = [ten]
	hang = deque([(ten, 0)])
	while hang:
		t, d = hang.popleft()
		if d >= SAU_TOI_DA:
			continue
		for g in sorted(canh.get(t, ())):
			if g in da or g in tong_dai or g in HOP_THOAI_CHUNG or g in HA_TANG:
				continue
			if g.startswith("scr") and len(g) > 3 and g[3].isupper():
				continue
			da.append(g)
			hang.append((g, d + 1))
	return "\n".join(ham[t]["than"] for t in da), len(da) - 1


def thanh_phan(than):
	"""Thành phần dùng chung và dấu hiệu trạng thái trong thân một màn."""
	co = []
	def them(ten, dk):
		if dk:
			co.append(ten)
	them("thanh đáy", bool(re.search(r"\bfooter\s*:", than)))
	them("nút nổi", bool(re.search(r"\bfab\s*:", than)))
	them("nút đầu trang", bool(re.search(r"\baction\s*:", than)))
	them("thanh công cụ ds", "dsCongCu(" in than)
	them("khuôn ds", bool(re.search(r"\bkg[A-Z]\w*\(", than)))
	them("thẻ", 'class="card' in than)
	them("dòng hub", 'class="hub' in than)
	them("chip", bool(re.search(r'class="[^"]*\bchip', than)))
	them("ảnh món", "anhMon(" in than)
	them("ô tìm", "vgbOTim(" in than or 'type="search"' in than)
	them("ô nhập", bool(re.search(r"<(input|textarea|select)\b", than)) or bool(re.search(r"\b(hoiChu|hoiSo|hoiNhap)\(", than)))
	them("bảng", "<table" in than)
	them("tiền", bool(re.search(r"\b(money|fmtMoney|vnd|tien|rndMoney)\(", than)))
	hop = sorted(set(x for x in HOP_THOAI_CHUNG if re.search(r"\b" + x + r"\(", than)))
	rieng = len(re.findall(r"className\s*=\s*'sh'", than))
	return co, hop, rieng


def trang_thai(than, co, hop, rieng):
	"""Trạng thái cần kiểm của một màn (bản 4 mục 6)."""
	tt = ["có dữ liệu", "tên dài", "cỡ chữ 150% và 200%"]
	if 'class="emp' in than or "Chưa có" in than or "Không có" in than:
		tt.append("rỗng")
	if "await " in than or "api(" in than:
		tt.append("đang tải")
		tt.append("lỗi")
	if "tiền" in co:
		tt.append("số lớn, âm, 0")
	if hop or rieng:
		tt.append("hộp thoại mở")
	if "ô nhập" in co or "ô tìm" in co:
		tt.append("bàn phím ảo")
	return tt


def tieu_de(than):
	kq = []
	for m in RE_FRAME.finditer(than):
		x = m.group(1).strip()
		kq.append(x[1:-1] if x.startswith("'") else "(động)")
	gon = []
	for x in kq:
		if x not in gon:
			gon.append(x)
	return gon[:3]


def lap_danh_muc(cac_phan):
	ham = tach_ham(cac_phan)
	nhom = doc_nhom(cac_phan.get("02-trang-chu.js", ""))
	tuyen = doc_dinh_tuyen(ham["vgbGo"]["than"]) if "vgbGo" in ham else OrderedDict()
	canh, tong_dai = do_thi(ham)
	cua_nhom = xep_nhom(ham, nhom, tuyen, canh, tong_dai)
	khoa_cua_man = {}
	for kh, ds in tuyen.items():
		for t in ds:
			khoa_cua_man.setdefault(t, []).append(kh)
	man = []
	for ten, h in ham.items():
		if not re.match(r"^scr[A-Z]", ten):
			continue
		than, so_phu = than_gop(ten, ham, canh, tong_dai)
		co, hop, rieng = thanh_phan(than)
		k = cua_nhom.get(ten)
		if ten in MAN_NEN:
			k, pr = None, 1
		elif ten in MAN_CON_LAI:
			k, pr = None, 5
		else:
			pr = PR_THEO_NHOM.get(k)
		man.append({
			"ten": ten, "tep": h["tep"], "dong": h["dong"], "tieu_de": tieu_de(h["than"]) or tieu_de(than),
			"qua_ham_phu": so_phu,
			"nhom": k, "pr": pr, "khoa": khoa_cua_man.get(ten, []),
			"vai": sorted(set(RE_VAI.findall(than))),
			"co": co, "hop": hop, "rieng": rieng,
			"trang_thai": trang_thai(than, co, hop, rieng),
		})
	hop_rieng = []
	for ten, h in ham.items():
		if re.match(r"^scr[A-Z]", ten):
			continue
		n = len(re.findall(r"className\s*=\s*'sh'", h["than"]))
		if n or "hopKhung(" in h["than"]:
			if ten not in HOP_THOAI_CHUNG:
				hop_rieng.append({"ten": ten, "tep": h["tep"], "dong": h["dong"], "so": n})
	return {"so_phan": len(cac_phan), "ham": ham, "nhom": nhom, "tuyen": tuyen, "man": man, "hop_rieng": hop_rieng, "tong_dai": sorted(tong_dai)}


def thong_ke_kieu(cac_phan):
	tung = OrderedDict()
	tong = {"mau": Counter(), "mau_vai": {}, "emoji": Counter(), "co_chu": Counter(), "bo_goc": Counter(),
		"khoang_le": Counter(), "phong": Counter()}
	for tep, ma in cac_phan.items():
		mau = Counter(x.lower() for x in RE_HEX.findall(ma))
		em = Counter(c for c in ma if la_emoji(c))
		for so in RE_THUC_THE.findall(ma):
			try:
				c = chr(int(so))
			except (ValueError, OverflowError):
				continue
			if la_emoji(c):
				em[c] += 1
		co = Counter(RE_CO_CHU.findall(ma))
		bo = Counter(x.strip() for x in RE_BO_GOC.findall(ma))
		le = Counter()
		for _tt, gt in RE_KHOANG.findall(ma):
			for so in re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)px", gt):
				if float(so) % 4:
					le[so] += 1
		ph = Counter(x.strip() for x in RE_PHONG.findall(ma))
		for tt, gt in RE_MAU_VAI.findall(ma):
			vai = "chữ" if tt == "color" else "nền" if tt.startswith("background") else "viền" if tt.startswith("border") else "bóng" if tt == "box-shadow" else "nét vẽ"
			for x in RE_HEX.findall(gt):
				tong["mau_vai"].setdefault(x.lower(), Counter())[vai] += 1
		tung[tep] = {
			"style": ma.count('style="'), "mau": sum(mau.values()), "mau_khac": len(mau),
			"emoji": sum(em.values()), "co_chu": sum(co.values()), "bo_goc": sum(bo.values()), "le": sum(le.values()),
			"rgb": len(re.findall(r"\brgba?\(", ma)),
		}
		tong["mau"] += mau
		tong["emoji"] += em
		tong["co_chu"] += co
		tong["bo_goc"] += bo
		tong["khoang_le"] += le
		tong["phong"] += ph
	return tung, tong


CO_CHUAN = set(["13", "15", "17", "20", "24", "30", "40", "48"])
BO_CHUAN = set(["14px", "16px", "18px", "24px", "26px", "999px"])


def viet_danh_muc(dm):
	man = dm["man"]
	ten_nhom = dict((k, t) for k, t, _ in dm["nhom"])
	d = []
	d.append("# Danh mục màn app /bep (PR 0, việc Nghệ sĩ công nghệ)")
	d.append("")
	d.append("Tệp này do `cong_cu/thong_ke_ui_nghe_si.py` sinh ra. Đừng sửa tay: sửa công cụ rồi chạy lại.")
	d.append("\"Đạt 100%\" của các PR sau tính trên bảng này (bản 4 mục 6), không tính trên số tệp.")
	d.append("")
	d.append("## Tóm tắt")
	d.append("")
	theo_pr = Counter(m["pr"] for m in man)
	d.append("- Số phần nguồn: %d. Số hàm màn (scr...): %d. Hộp thoại riêng ngoài bộ dùng chung: %d hàm." % (
		dm["so_phan"], len(man), len(dm["hop_rieng"])))
	d.append("- Màn máy chưa dò ra thành phần nào (ghi chưa xác định): %d." % len([m for m in man if not m["co"]]))
	d.append("- Số ô trang chủ có định tuyến trong vgbGo: %d. Số nhóm trang chủ: %d." % (len(dm["tuyen"]), len(dm["nhom"])))
	for pr, ten in ((1, "PR 1 nền"), (2, "PR 2 Bán hàng và Quầy"), (3, "PR 3 Kho, Sản xuất, Thu mua"),
			(4, "PR 4 Kế toán, Tài chính"), (5, "PR 5 Marketing và các màn còn lại"), (None, "Chưa xếp, cần xếp tay")):
		d.append("- %s: %d màn." % (ten, theo_pr.get(pr, 0)))
	d.append("")
	d.append("Cách đọc cột: **Thành phần** là khung dùng chung màn đó dùng (PR nào sửa khung thì phải kiểm lại màn này). "
		"**Hộp thoại** là bộ hỏi dùng chung màn gọi, số trong ngoặc là số bảng trượt tự dựng trong màn. "
		"Ba cột này đọc cả thân màn lẫn các hàm vẽ phụ màn gọi (sâu tối đa %d tầng, không sang màn khác). "
		"Ô ghi **chưa xác định** nghĩa là máy không dò ra gì, KHÔNG có nghĩa là màn không dùng: người làm phải mở màn xem và coi như màn chịu ảnh hưởng của mọi khung chung. "
		"**Vai nhắc trong mã** chỉ để gợi ý chỗ giao diện đổi theo quyền; quyền thật xem docs/quyen-theo-phan-he.md." % SAU_TOI_DA)
	d.append("")
	for pr, ten in ((1, "PR 1 nền"), (2, "PR 2 Bán hàng và Quầy"), (3, "PR 3 Kho, Sản xuất, Thu mua"),
			(4, "PR 4 Kế toán, Tài chính"), (5, "PR 5 Marketing và các màn còn lại"), (None, "Chưa xếp, cần xếp tay")):
		ds = [m for m in man if m["pr"] == pr]
		if not ds:
			continue
		d.append("## %s (%d màn)" % (ten, len(ds)))
		d.append("")
		d.append("| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |")
		d.append("|---|---|---|---|---|---|---|---|")
		for m in sorted(ds, key=lambda x: (x["nhom"] or "~", x["tep"], x["dong"])):
			hop = ", ".join(m["hop"]) + (" (+%d)" % m["rieng"] if m["rieng"] else "")
			d.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
				m["ten"], "; ".join(m["tieu_de"]).replace("|", "/") or "(không gọi frame)",
				ten_nhom.get(m["nhom"], "-"), m["tep"][:2], ", ".join(m["co"]) or "chưa xác định", hop or ("-" if m["co"] else "chưa xác định"),
				", ".join(m["trang_thai"]), ", ".join(m["vai"]) or "-"))
		d.append("")
	d.append("## Hộp thoại")
	d.append("")
	d.append("Bộ dùng chung (07-hop-thoai.js và 00-nen.js): " + ", ".join(HOP_THOAI_CHUNG) + ".")
	dem = Counter()
	for h in dm["ham"].values():
		for x in HOP_THOAI_CHUNG:
			dem[x] += len(re.findall(r"\b" + x + r"\(", h["than"]))
	d.append("")
	d.append("| Hộp thoại chung | Số chỗ gọi trong app |")
	d.append("|---|--:|")
	for x in HOP_THOAI_CHUNG:
		d.append("| %s | %d |" % (x, dem[x]))
	d.append("")
	d.append("Hàm tự dựng bảng trượt (lớp `sh`) hoặc gọi hopKhung, không phải hàm màn:")
	d.append("")
	d.append("| Hàm | Phần | Số bảng trượt tự dựng |")
	d.append("|---|---|--:|")
	for h in sorted(dm["hop_rieng"], key=lambda x: (x["tep"], x["dong"])):
		d.append("| %s | %s | %d |" % (h["ten"], h["tep"][:2], h["so"]))
	d.append("")
	d.append("## Ô trang chủ trỏ ra ngoài app hoặc qua khuôn danh sách")
	d.append("")
	ngoai = [k for k, ds in dm["tuyen"].items() if not ds]
	d.append("Các khoá sau không mở hàm scr trực tiếp (mở trang khác, khuôn danh sách kgMo, hoặc chỉ báo tin): " + ", ".join(ngoai) + ".")
	d.append("")
	d.append("Hàm tổng đài bị bỏ khỏi phép dò đường (nhắc quá 25 màn): " + ", ".join(dm["tong_dai"]) + ".")
	d.append("")
	return "\n".join(d) + "\n"


def viet_thong_ke(tung, tong):
	d = []
	d.append("# Thống kê kiểu hiển thị app /bep (PR 0, việc Nghệ sĩ công nghệ)")
	d.append("")
	d.append("Tệp này do `cong_cu/thong_ke_ui_nghe_si.py` sinh ra. Đây là số ĐẾM để biết khối lượng; "
		"bảng ánh xạ theo vai trò (bản 4 mục 5 bước 2) làm ở PR nền và từng PR nhóm màn.")
	d.append("")
	s = lambda k: sum(x[k] for x in tung.values())
	d.append("## Tổng")
	d.append("")
	d.append("- Kiểu viết trong thẻ (style=\"...\"): %d chỗ." % s("style"))
	d.append("- Mã màu hex: %d lần, %d màu khác nhau. Màu viết rgb()/rgba(): %d lần." % (sum(tong["mau"].values()), len(tong["mau"]), s("rgb")))
	d.append("- Emoji và ký hiệu hình: %d lần, %d ký tự khác nhau." % (sum(tong["emoji"].values()), len(tong["emoji"])))
	ngoai_co = sum(v for k, v in tong["co_chu"].items() if k not in CO_CHUAN)
	duoi13 = sum(v for k, v in tong["co_chu"].items() if float(k) < 13)
	d.append("- Khai báo cỡ chữ px: %d lần, %d cỡ khác nhau; %d lần ngoài 8 cỡ chuẩn, trong đó %d lần dưới 13." % (
		sum(tong["co_chu"].values()), len(tong["co_chu"]), ngoai_co, duoi13))
	ngoai_bo = sum(v for k, v in tong["bo_goc"].items() if k not in BO_CHUAN)
	d.append("- Khai báo bo góc: %d lần, %d giá trị khác nhau; %d lần ngoài 6 mức chuẩn." % (
		sum(tong["bo_goc"].values()), len(tong["bo_goc"]), ngoai_bo))
	d.append("- Giá trị px không phải bội số của 4 trong padding, margin, gap: %d lần." % sum(tong["khoang_le"].values()))
	d.append("- Khai báo phông: %d lần, %d giá trị khác nhau." % (sum(tong["phong"].values()), len(tong["phong"])))
	d.append("")
	d.append("## Theo từng phần")
	d.append("")
	d.append("| Phần | style trong thẻ | Màu hex (lần / màu) | rgb() | Emoji | Cỡ chữ px | Bo góc | Khoảng lẻ |")
	d.append("|---|--:|--:|--:|--:|--:|--:|--:|")
	for tep, x in tung.items():
		d.append("| %s | %d | %d / %d | %d | %d | %d | %d | %d |" % (
			tep[:-3], x["style"], x["mau"], x["mau_khac"], x["rgb"], x["emoji"], x["co_chu"], x["bo_goc"], x["le"]))
	d.append("")
	d.append("## 40 màu dùng nhiều nhất, kèm vai đang mang")
	d.append("")
	d.append("Một màu mang nhiều vai thì KHÔNG đổi thành một biến chung (bản 4 mục 5).")
	d.append("")
	d.append("| Màu | Số lần | Vai (chữ / nền / viền / bóng / nét vẽ) |")
	d.append("|---|--:|---|")
	for mau, n in tong["mau"].most_common(40):
		v = tong["mau_vai"].get(mau, Counter())
		d.append("| %s | %d | %s |" % (mau, n, ", ".join("%s %d" % (k, c) for k, c in v.most_common()) or "ngoài khai báo màu"))
	d.append("")
	d.append("## Cỡ chữ px")
	d.append("")
	d.append("| Cỡ | Số lần | Trong bộ chuẩn |")
	d.append("|--:|--:|---|")
	for k, n in sorted(tong["co_chu"].items(), key=lambda x: float(x[0])):
		d.append("| %s | %d | %s |" % (k, n, "có" if k in CO_CHUAN else "không"))
	d.append("")
	d.append("## Bo góc (20 giá trị nhiều nhất)")
	d.append("")
	d.append("| Giá trị | Số lần | Trong 6 mức |")
	d.append("|---|--:|---|")
	for k, n in tong["bo_goc"].most_common(20):
		d.append("| %s | %d | %s |" % (k.replace("|", "/"), n, "có" if k in BO_CHUAN else "không"))
	d.append("")
	d.append("## Emoji và ký hiệu hình (tất cả)")
	d.append("")
	d.append("Đếm ở MỌI chuỗi trong mã, gồm cả chuỗi tin gửi đi và mẫu in. Phần đó KHÔNG được thay (bản 4 mục 0); "
		"PR nền phân loại từng chỗ theo lớp vẽ giao diện hay nội dung gửi đi trước khi lập bảng đối chiếu.")
	d.append("")
	d.append("| Ký tự | Mã | Số lần |")
	d.append("|---|---|--:|")
	for c, n in tong["emoji"].most_common():
		d.append("| %s | U+%04X | %d |" % (c, ord(c), n))
	d.append("")
	d.append("## Phông đang khai")
	d.append("")
	d.append("| Giá trị font-family | Số lần |")
	d.append("|---|--:|")
	for k, n in tong["phong"].most_common():
		d.append("| %s | %d |" % (k.replace("|", "/"), n))
	d.append("")
	return "\n".join(d) + "\n"


def dung(thu_muc=None):
	cac_phan = doc_cac_phan(thu_muc)
	dm = lap_danh_muc(cac_phan)
	tung, tong = thong_ke_kieu(cac_phan)
	return OrderedDict([
		("danh-muc-man.md", viet_danh_muc(dm)),
		("thong-ke-kieu.md", viet_thong_ke(tung, tong)),
	])


def main(argv):
	kiem = "--kiem" in argv
	kq = dung()
	lech = 0
	if not os.path.isdir(RA):
		os.makedirs(RA)
	for ten, nd in kq.items():
		duong = os.path.join(RA, ten)
		cu = io.open(duong, encoding="utf-8").read() if os.path.exists(duong) else None
		if kiem:
			if cu != nd:
				lech += 1
				print("LỆCH: docs/ui-nghe-si/%s không khớp mã nguồn. Chạy lại công cụ không kèm --kiem." % ten)
		else:
			io.open(duong, "w", encoding="utf-8").write(nd)
			print("Đã ghi docs/ui-nghe-si/%s (%d dòng)" % (ten, nd.count("\n")))
	if kiem and not lech:
		print("Khớp: danh mục và thống kê trùng mã nguồn bep/.")
	return 1 if lech else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))

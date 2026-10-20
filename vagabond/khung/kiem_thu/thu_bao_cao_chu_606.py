"""v606 (anh Việt 20/10/2026): báo cáo cuối ngày cho chủ qua nhóm Zalo.

Anh duyệt mẫu dựng từ số thật ngày 19/10 (gửi 23:30, nhóm nào tích tin "Báo
cáo cuối ngày" thì nhận). Ca đầu chốt NGUYÊN VĂN tin của ngày đó; các ca sau
chạy hàm thật lay_so_lieu, gui_cuoi_ngay và đường ghi tin của kenh_zalo, chỉ
thay tầng Frappe và các hàm đọc hoá đơn của phân hệ Báo cáo bằng bản giả.
"""
import datetime
import json
import os
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import bao_cao_chu as b
from vagabond import kenh_zalo as kz

SL=dict(ngay=datetime.date(2026,10,19),ngay_truoc=datetime.date(2026,10,18),tong=123039344,so_hd=171,tong_truoc=114423188,
 diem=[dict(ten="Sales Online",tien=88949984,so_hd=48,truoc=77062381,giam=505516),dict(ten="District 1",tien=31807342,so_hd=108,truoc=33959307,giam=5073658),dict(ten="NVHTN",tien=2282018,so_hd=15,truoc=3401500,giam=547982)],
 kenh=[("Pancake",87760500),("Tại chỗ",19596000),("GrabFood",13041250),("ShopeeFood",2173672),("GreenSM Food",323422),("BeFood",144500)],
 thanh_toan=[("Chuyển khoản",92244000),("GrabFood",13041250),("Thẻ - ShinhanBank",9220000),("Tiền mặt",2500000),("OnePay",2190000),("ShopeeFood",2173672),("Công nợ",1670422)],
 giam=6127156,ctkm=dict(tien=945000,luot=11,top=("VOUCHER 200.000 GRAB DINE OUT",395000)),huy=dict(so=2,tien=91979),sua=7,
 ban_chay=[dict(ten="Bánh trung thu Thập Cẩm Jambon Nấm Truffle",sl=60,tien=9600000),dict(ten="Bánh trung thu Vải Hoa Hồng\t",sl=60,tien=7800000),dict(ten="Bánh trung thu Phúc Bồn Tử Dâu",sl=60,tien=7800000)],
 nhap=dict(so=1,tien=1012500))

MAU = """📊 Vagabond | Báo cáo cuối ngày T2 19/10
Doanh thu 123,0 tr · 171 hoá đơn · bình quân 720k
So với CN 18/10: +7,5%

🏠 Theo điểm bán
• Sales Online 88,9 tr (72%) · 48 HĐ · +15%
• District 1 31,8 tr (26%) · 108 HĐ · -6%
• NVHTN 2,3 tr (2%) · 15 HĐ · -33%

🛵 Theo kênh
• Pancake 87,8 tr · Tại chỗ 19,6 tr
• GrabFood 13,0 tr · ShopeeFood 2,2 tr · GreenSM Food, BeFood 468k

💳 Tiền về
• Chuyển khoản 92,2 tr · Thẻ 9,2 tr · Tiền mặt 2,5 tr
• Sàn, ví 17,4 tr · Khác 1,7 tr

🎫 Giảm giá 6,1 tr (5,0% doanh thu)
• District 1 5,1 tr · NVHTN 548k · Sales Online 506k
• Khuyến mãi 945k / 11 lượt, nhiều nhất VOUCHER 200.000 GRAB DINE OUT (395k)

✂️ Sửa, huỷ: 2 huỷ (92k), 7 sửa

🍰 Bán chạy
• BTT Thập Cẩm Jambon Nấm Truffle: 60 (9,6 tr)
• BTT Vải Hoa Hồng: 60 (7,8 tr)
• BTT Phúc Bồn Tử Dâu: 60 (7,8 tr)

⚠️ Cần để ý
• NVHTN giảm 33% so với hôm trước
• 1 đơn chưa ghi sổ (1,0 tr) đã tính vào số trên

Chi tiết: app > Báo cáo"""


@ca("v606 báo cáo ngày: tin ngày 19/10 đúng nguyên văn mẫu anh Việt duyệt (thứ thật T2, chữ có dấu, dưới 2.000 ký tự)")
def _mau():
	t = b.soan_bao_cao(SL)
	la("nguyên văn", t, MAU)
	dung("dưới giới hạn Zalo", len(t) <= 2000)
	dung("không em dash, en dash", "\u2013" not in t and "\u2014" not in t)


@ca("v606 báo cáo ngày: số gọn và phần trăm kiểu Việt")
def _so():
	la("tiền", [b.tien_gon(x) for x in (123039344, 945000, 91979, 500, 0, None, "x", -2500000)],
		["123,0 tr", "945k", "92k", "500 đ", "0 đ", "0 đ", "0 đ", "-2,5 tr"])
	la("phần trăm", [b.phan_tram(7.53, 1), b.phan_tram(-33.4), b.phan_tram(0), b.phan_tram(None)], ["+7,5%", "-33%", "0%", ""])
	la("chênh không có số trước", b.chenh(5, 0), None)
	la("thứ", [b.ngay_vn(datetime.date(2026, 10, 19)), b.ngay_vn(datetime.date(2026, 10, 25))], ["T2 19/10", "CN 25/10"])
	la("nhóm thanh toán", [b.nhom_thanh_toan(x) for x in ("Chuyển khoản", "Thẻ - ShinhanBank", "Tiền mặt", "GrabFood", "OnePay", "Công nợ", "")],
		["Chuyển khoản", "Thẻ", "Tiền mặt", "Sàn, ví", "Sàn, ví", "Khác", "Khác"])
	la("gộp kênh nhỏ", b.gop_kenh([("A", 90), ("B", 9.5), ("C", 0.3), ("D", 0.2), ("E", 0)], 100), [("A", 90), ("B", 9.5), ("C, D", 0.5)])


@ca("v606 báo cáo ngày: mục Cần để ý theo ngưỡng; ngày yên thì nói rõ không có gì bất thường; ngày không hoá đơn nói rõ")
def _de_y():
	yen = dict(SL, diem=[dict(d, truoc=d["tien"]) for d in SL["diem"]], nhap={"so": 0, "tien": 0})
	la("ngày yên", b.can_de_y(yen), [])
	dung("tin ngày yên", "✅ Không có gì bất thường." in b.soan_bao_cao(yen))
	xau = dict(yen, tong_truoc=SL["tong"] * 2, giam=SL["tong"] * 0.1, huy={"so": 3, "tien": 50000})
	la("ngày xấu", b.can_de_y(xau), ["Doanh thu cả ngày giảm 50% so với hôm trước", "Giảm giá chiếm 10,0% doanh thu", "3 hoá đơn bị huỷ (50k)"])
	la("huỷ ít mà tiền lớn", b.can_de_y(dict(yen, huy={"so": 1, "tien": 1500000})), ["1 hoá đơn bị huỷ (1,5 tr)"])
	# Dòng này từng chốt NGUYÊN VĂN tin ngắn cho dict(SL, so_hd=0) dù SL còn
	# huỷ, sửa và hôm trước có bán: chính nó che lỗi Codex #492 P2 4325217633.
	# Đã chuyển sang ca _huy_het; đừng chốt lại tin ngắn cho ngày còn huỷ, sửa.
	t = b.soan_bao_cao(dict(SL, so_hd=0, tong=0))
	dung("không hoá đơn: nói rõ, vẫn báo huỷ", "Hôm nay chưa có hoá đơn nào." in t and "✂️ Sửa, huỷ: 2 huỷ" in t)
	dai = dict(SL, kenh=[("Kênh %d" % i, 1000000) for i in range(400)])
	dung("tin quá dài thì cắt ở 2.000 ký tự", len(b.soan_bao_cao(dai)) <= 2000)


def _gia_bao_cao(hd_nay, hd_truoc):
	"""Bản giả các hàm đọc của phân hệ Báo cáo: mỗi hàm trả đúng hình dạng thật."""
	from vagabond import bao_cao as bc

	def hoa_don(tu, den, **k):
		return hd_nay if tu == datetime.date(2026, 10, 19) else hd_truoc

	def tong(hd, **k):
		gom = {}
		for r in hd:
			o = gom.setdefault(r["diem"], {"diem": r["diem"], "so_hd": 0, "tien": 0.0, "giam": 0.0})
			o["so_hd"] += 1
			o["tien"] += r["tien"]
			o["giam"] += r["giam"]
		return {"dong": list(gom.values())}
	return [patch.object(bc, "_hoa_don", hoa_don),
		patch.object(bc, "_bc_tong_doanh_thu", tong),
		patch.object(bc, "_bc_nguon_don", lambda hd, **k: {"dong": [{"nguon": "Pancake", "tien": sum(r["tien"] for r in hd)}]}),
		patch.object(bc, "_bc_thanh_toan", lambda hd, **k: {"dong": [{"pt": "Chuyển khoản", "tien": sum(r["tien"] for r in hd)}]}),
		patch.object(bc, "_bc_khuyen_mai", lambda hd, **k: {"dong": [{"ctkm": "Mã A", "so_lan": 2, "giam": 100000}, {"ctkm": "Mã B", "so_lan": 1, "giam": 50000}]}),
		patch.object(bc, "_bc_sua_huy", lambda hd, **k: {"dong": [{"viec": "Huỷ hoá đơn", "tien": 300000}, {"viec": "Huỷ bill nháp: nhầm", "tien": 20000},
			{"viec": "Sửa hoá đơn: món", "tien": 0}, {"viec": "Đổi ngày hoá đơn", "tien": 0}]}),
		patch.object(bc, "_bc_mon_ban_chay", lambda hd, **k: {"dong": [{"mon": "Nĩa gỗ", "sl": 99, "tien": 0}, {"mon": "Kankin", "sl": 2, "tien": 2000000},
			{"mon": "Very Berry", "sl": 1, "tien": 1300000}]}),
		patch.object(bc, "_do_nhap", lambda hd: (1, 500000))]


def _chay(cac, ham):
	from contextlib import ExitStack
	with ExitStack() as st:
		for p in cac:
			st.enter_context(p)
		return ham()


HD = [{"diem": "District 1", "tien": 1000000, "giam": 100000}, {"diem": "District 1", "tien": 2000000, "giam": 0},
	{"diem": "Sales Online", "tien": 3000000, "giam": 50000}]
HD_CU = [{"diem": "District 1", "tien": 6000000, "giam": 0}, {"diem": "Sales Online", "tien": 2000000, "giam": 0}]
for _r in HD + HD_CU:
	_r["grand_total"] = _r["tien"]


@ca("v606 báo cáo ngày: lay_so_lieu đọc qua đúng hàm của phân hệ Báo cáo, tách huỷ khỏi sửa, so với hôm trước theo từng điểm")
def _lay():
	sl = _chay(_gia_bao_cao(HD, HD_CU), lambda: b.lay_so_lieu(datetime.date(2026, 10, 19)))
	la("tổng, số hoá đơn, hôm trước", (sl["tong"], sl["so_hd"], sl["tong_truoc"]), (6000000, 3, 8000000))
	la("từng điểm có số hôm trước", [(d["ten"], d["tien"], d["truoc"], d["giam"]) for d in sl["diem"]],
		[("District 1", 3000000, 6000000, 100000), ("Sales Online", 3000000, 2000000, 50000)])
	la("huỷ và sửa", (sl["huy"], sl["sua"]), ({"so": 2, "tien": 320000}, 2))
	la("khuyến mãi", sl["ctkm"], {"tien": 150000, "luot": 3, "top": ("Mã A", 100000)})
	la("bán chạy theo doanh thu", [m["ten"] for m in sl["ban_chay"]], ["Kankin", "Very Berry", "Nĩa gỗ"])
	t = b.soan_bao_cao(sl)
	dung("District 1 giảm 50% vào Cần để ý", "• District 1 giảm 50% so với hôm trước" in t)
	dung("món 0 đồng không vào Bán chạy", "Nĩa gỗ" not in t)


@ca("v606 báo cáo ngày: gửi 23:30 bằng tin soạn sẵn, mã tin Báo cáo cuối ngày, một khoá mỗi ngày; đọc số lỗi thì không gửi số dở")
def _gui():
	goi = []
	with patch.object(kz, "bao_hoac_ghi_loi", lambda *a, **k: goi.append((a, k))), \
			patch.object(b.frappe.db, "commit", lambda: None, create=True), \
			patch.object(b, "lay_so_lieu", lambda ngay: SL):
		t = b.gui_cuoi_ngay(datetime.date(2026, 10, 19))
	la("một lần gọi", len(goi), 1)
	a, k = goi[0]
	la("loại, chủ đề", a[:2], ("ban_tin", "ban_hang"))
	la("mã tin, khoá ngày", (k["ma_tin"], k["khoa"]), ("bgd_bao_cao_ngay", "bao_cao_ngay:2026-10-19"))
	la("gửi nguyên văn tin đã soạn", k["noi_dung"], MAU)
	dung("mã tin có trong danh mục, đúng bộ phận", kz.TIN["bgd_bao_cao_ngay"][0] == "Ban giám đốc" and "Ban giám đốc" in kz.BO_PHAN)
	loi = []
	goi.clear()

	def hong(ngay):
		raise RuntimeError("doc hoa don loi")
	with patch.object(kz, "bao_hoac_ghi_loi", lambda *a, **k: goi.append((a, k))), \
			patch.object(b.frappe, "log_error", lambda *a, **k: loi.append(a), create=True), \
			patch.object(b.frappe, "get_traceback", lambda: "tb", create=True), \
			patch.object(b, "lay_so_lieu", hong):
		la("lỗi đọc số: không gửi", (b.gui_cuoi_ngay(datetime.date(2026, 10, 19)), goi), (None, []))
	la("lỗi đọc số: ghi Error Log", len(loi), 1)
	hooks = open(os.path.join(os.path.dirname(kz.__file__), "hooks.py"), encoding="utf-8").read()
	dung("nhịp 23:30", '"30 23 * * *", []).append("vagabond.bao_cao_chu.gui_cuoi_ngay")' in hooks)


@ca("v606 kênh Zalo: tin soạn sẵn đi nguyên văn vào sổ tin, không qua khuôn soan_tin; quá dài thì cắt ở 2.000 ký tự")
def _ghi():
	ghi = []

	class Doc(dict):
		def insert(self, **k):
			ghi.append(dict(self))
	nhom = [{"ten_nhom": "BGĐ", "chat_id": "zgr-bgd", "bat": 1, "tin_nhan": "bgd_bao_cao_ngay"}]
	with patch.object(kz, "_cac_nhom", lambda: nhom), \
			patch.object(kz.frappe, "get_doc", lambda d: Doc(d), create=True), \
			patch.object(kz.frappe, "generate_hash", lambda length=8: "h" * length, create=True), \
			patch.object(kz.frappe.db, "savepoint", lambda sp: None, create=True):
		kz._ghi_hop_thu({"loai": "ban_tin", "chu_de": "ban_hang", "tieu_de": "x", "khoa": "bao_cao_ngay:2026-10-19",
			"ma_tin": "bgd_bao_cao_ngay", "noi_dung": MAU})
		kz._ghi_hop_thu({"loai": "ban_tin", "chu_de": "ban_hang", "tieu_de": "x", "khoa": "k2",
			"ma_tin": "bgd_bao_cao_ngay", "noi_dung": "a" * 2500})
	la("nguyên văn", ghi[0]["noi_dung"], MAU)
	la("cắt dài", len(ghi[1]["noi_dung"]), 2000)
	la("tin thường vẫn qua khuôn cũ", kz.tin_soan_san(None), "")


@ca("v606 kênh Zalo: bao() chuyển tin soạn sẵn xuống sổ tin (đường thật bao_hoac_ghi_loi -> bao -> ghi sổ)")
def _bao():
	import types
	nhan = []
	f = kz.frappe
	sau = types.SimpleNamespace(add=lambda fn: None)
	with patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_ghi_hop_thu", lambda tin: nhan.append(tin) or ["T1"]), \
			patch.object(f, "flags", types.SimpleNamespace(), create=True), \
			patch.object(f.db, "after_commit", sau, create=True):
		kq = kz.bao_hoac_ghi_loi("ban_tin", "ban_hang", "Báo cáo cuối ngày T2 19/10", khoa="bao_cao_ngay:2026-10-19",
			ma_tin="bgd_bao_cao_ngay", noi_dung=MAU)
	la("ghi sổ một lần", (kq, len(nhan)), (["T1"], 1))
	la("tin soạn sẵn tới sổ", (nhan[0]["noi_dung"], nhan[0]["ma_tin"]), (MAU, "bgd_bao_cao_ngay"))


@ca("v606 báo cáo ngày (Codex #492 P2 4324973553): một lần huỷ ra hai dòng BC07 (dòng hoá đơn và dòng ghi vết) vẫn chỉ đếm một hoá đơn huỷ")
def _huy_mot_lan():
	# Chạy THẬT bao_cao._bc_sua_huy; chỉ thay frappe.get_all. Nội dung ghi vết
	# lấy từ chính chung_tu._ghi_vet, với đúng câu ba đường huỷ đang ghi:
	# huỷ mềm phiếu nháp (chung_tu.danh_dau_huy), huỷ bill ở quầy (ban_hang),
	# huỷ ghi sổ hàng loạt (chung_tu). Bản giả cũ của ca _lay chỉ có dòng hoá
	# đơn, không có dòng ghi vết, nên không thấy lỗi đếm đôi.
	from vagabond import bao_cao as bc
	from vagabond import chung_tu as ct
	vet = []

	class Doc(dict):
		def insert(self, **k):
			vet.append(dict(self))
	with patch.object(ct.frappe, "get_doc", lambda d: Doc(d), create=True), \
			patch.object(ct.frappe, "session", type("S", (), {"user": "thu.ngan@vgb"})(), create=True):
		ct._ghi_vet("Sales Invoice", "SI-2", "Huỷ phiếu nháp. Lý do: khách đổi ý")
		ct._ghi_vet("Sales Invoice", "SI-3", "Huỷ bill PCK-3 (150.000 đ). Lý do: nhầm món")
		ct._ghi_vet("Sales Invoice", "SI-1", "Huỷ ghi sổ hàng loạt. Lý do: trùng")
		ct._ghi_vet("Sales Invoice", "SI-4", "Đổi ngày hoá đơn 18/10 -> 19/10")
	R = lambda **k: type("R", (dict,), {"__getattr__": dict.get})(**k)
	ngay = datetime.date(2026, 10, 19)

	def get_all(dt, filters=None, **k):
		if dt == "Sales Invoice" and filters.get("docstatus") == 2:
			return [R(name="SI-1", posting_date=ngay, grand_total=300000, vgb_quay="D1", vgb_huy=1, vgb_huy_ly_do="trùng")]
		if dt == "Sales Invoice":
			return [R(name="SI-2", posting_date=ngay, grand_total=20000, vgb_quay="D1", vgb_huy=1, vgb_huy_ly_do="khách đổi ý"),
				R(name="SI-3", posting_date=ngay, grand_total=150000, vgb_quay="D1", vgb_huy=1, vgb_huy_ly_do="nhầm món")]
		if dt == "Comment":
			return [R(reference_name=v["reference_name"], content=v["content"], creation="2026-10-19 20:00:00", owner="thu.ngan@vgb")
				for v in vet]
		raise AssertionError(dt)
	gia = [p for p in _gia_bao_cao(HD, HD_CU) if getattr(p, "attribute", "") != "_bc_sua_huy"]
	gia += [patch.object(bc.frappe, "get_all", get_all, create=True),
		patch.object(bc.diem_ban, "ten_diem", lambda: {"D1": "District 1"})]
	sh = _chay(gia, lambda: bc._bc_sua_huy([], tu=ngay, den=ngay))["dong"]
	la("BC07 vẫn giữ đủ dòng ghi vết (màn Báo cáo không đổi)", len(sh), 7)
	sl = _chay(gia, lambda: b.lay_so_lieu(ngay))
	la("ba hoá đơn huỷ, tiền lấy từ dòng hoá đơn", sl["huy"], {"so": 3, "tien": 470000})
	la("một lần sửa (đổi ngày)", sl["sua"], 1)
	t = b.soan_bao_cao(sl)
	dung("Cần để ý nói 3 hoá đơn huỷ, không phải 6", "• 3 hoá đơn bị huỷ (470k)" in t and "6 hoá đơn" not in t)


@ca("v606 báo cáo ngày (Codex #492 P2 4325217633): ngày huỷ hết hoá đơn vẫn báo số huỷ, sửa và mục Cần để ý, không chỉ nói chưa có hoá đơn")
def _huy_het():
	# Đi đúng đường thật: lay_so_lieu với _hoa_don rỗng (huỷ thì _hoa_don lọc
	# bỏ) nhưng BC07 còn ba hoá đơn huỷ và một lần sửa, hôm trước có bán.
	from vagabond import bao_cao as bc
	sh = [{"hoa_don": "SI-%d" % i, "viec": v, "tien": t} for i, v, t in (
		(1, "Huỷ hoá đơn", 300000), (1, "Huỷ ghi sổ hàng loạt. Lý do: trùng - a", 0),
		(2, "Huỷ bill nháp: khách đổi ý", 20000), (2, "Huỷ phiếu nháp. Lý do: khách đổi ý - a", 0),
		(3, "Huỷ bill nháp: nhầm món", 150000), (4, "Đổi ngày hoá đơn - a", 0))]
	gia = [p for p in _gia_bao_cao([], HD_CU) if getattr(p, "attribute", "") not in ("_bc_sua_huy", "_bc_khuyen_mai", "_bc_mon_ban_chay", "_do_nhap")]
	gia += [patch.object(bc, "_bc_sua_huy", lambda hd, **k: {"dong": sh}),
		patch.object(bc, "_bc_khuyen_mai", lambda hd, **k: {"dong": []}),
		patch.object(bc, "_bc_mon_ban_chay", lambda hd, **k: {"dong": []}),
		patch.object(bc, "_do_nhap", lambda hd: (0, 0))]
	sl = _chay(gia, lambda: b.lay_so_lieu(datetime.date(2026, 10, 19)))
	la("không hoá đơn, ba huỷ, một sửa", (sl["so_hd"], sl["huy"], sl["sua"]), (0, {"so": 3, "tien": 470000}, 1))
	t = b.soan_bao_cao(sl)
	la("tin ngày huỷ hết", t, "📊 Vagabond | Báo cáo cuối ngày T2 19/10\nHôm nay chưa có hoá đơn nào.\n\n"
		"✂️ Sửa, huỷ: 3 huỷ (470k), 1 sửa\n\n⚠️ Cần để ý\n• Doanh thu cả ngày giảm 100% so với hôm trước\n"
		"• 3 hoá đơn bị huỷ (470k)\n\nChi tiết: app > Báo cáo")
	trong = dict(SL, so_hd=0, tong=0, tong_truoc=0, diem=[], huy={"so": 0, "tien": 0}, sua=0, giam=0,
		ctkm={"tien": 0, "luot": 0, "top": None}, nhap={"so": 0, "tien": 0})
	la("ngày không có gì thật thì vẫn gọn", b.soan_bao_cao(trong),
		"📊 Vagabond | Báo cáo cuối ngày T2 19/10\nHôm nay chưa có hoá đơn nào.\n\nChi tiết: app > Báo cáo")
	yen = b.soan_bao_cao(dict(SL, huy={"so": 0, "tien": 0}, sua=0))
	dung("ngày có bán mà không huỷ, sửa: không dòng Sửa, huỷ, không khoảng trống thừa", "✂️" not in yen and "\n\n\n" not in yen)
	chi_sua = b.soan_bao_cao(dict(SL, huy={"so": 0, "tien": 0}, sua=2))
	dung("ngày chỉ có sửa vẫn có dòng Sửa, huỷ", "✂️ Sửa, huỷ: 0 huỷ, 2 sửa" in chi_sua)


@ca("v606 báo cáo ngày (Codex #492 P2 4325572133): chỉ đếm sửa thật trên bill; ghi vết đối soát hoá đơn điện tử, điểm, tờ thay thế, khoá sổ không phải sửa")
def _chi_sua_that():
	# Nội dung là đúng câu các nơi đang ghi vết Info lên Sales Invoice. Không
	# nạp ban_hang hay doi_soat_hddt_ra ở đây vì chúng kéo requests (CI tay
	# không); khuôn "%s - người (cách)" chép từ ban_hang._ghi_vet. Ca chốt
	# nguồn bên dưới đọc mã ban_hang để câu ở đây không lệch câu thật.
	vet = [
		("SI-5", "Sửa hoá đơn: giá món - thu.ngan@vgb (OTP)"),                       # ban_hang sửa bill
		("SI-6", "Đổi ngày hoá đơn 2026-10-18 sang 2026-10-19 - ql@vgb (Quản lý)"),  # ban_hang đổi ngày
		("SI-7", "Gắn khách công nợ KH-01 cho đơn đã ghi sổ - kt@vgb ()"),           # ban_hang gắn khách
		("SI-8", "Gỡ dấu huỷ, phiếu dùng lại bình thường. - ql@vgb"),                # chung_tu gỡ huỷ
		("SI-9", "Nối tờ hoá đơn điện tử 123 (C26TVG, lập thẳng trên m-invoice, 100.000 đ) vào đơn này."),  # doi_soat_hddt_ra
		("SI-9", "Gỡ tờ hoá đơn điện tử 123 khỏi đơn này. Lý do: nhầm. Người gỡ: kt@vgb."),               # doi_soat_hddt_ra
		("SI-10", "[Điểm] Trừ 100 điểm của khách, giảm 10.000 đ. - thu.ngan@vgb"),   # diem_otp
		# Lý do gõ tay có thể chứa đúng chữ "Sửa hoá đơn"; chỉ ĐẦU CÂU mới là sửa.
		("SI-10", "[Điểm] Hoàn lại 100 điểm. Sửa hoá đơn nên hoàn - thu.ngan@vgb"),  # diem_otp
		("SI-11", "Ghi nhận hoá đơn thay thế 456 cho tờ cũ 123. Lý do: sai MST"),     # ban_hang tờ thay thế
		("SI-12", "MỞ KHOÁ SỔ để sửa. Lý do: kiểm kê - kt@vgb"),                     # chung_tu mở khoá sổ
		("SI-12", "Đóng khoá sổ lại. - kt@vgb"),
	]
	dong = [{"hoa_don": h, "viec": v, "tien": 0} for h, v in vet]
	la("bốn lần sửa thật, không huỷ", b.gom_huy_sua(dong), ({"so": 0, "tien": 0}, 4))
	nguon = open(os.path.join(os.path.dirname(b.__file__), "ban_hang.py"), encoding="utf-8").read()
	for cau in ('_ghi_vet(name, "Sửa hoá đơn: %s"', '_ghi_vet(si.name, "Đổi ngày hoá đơn %s', '_ghi_vet(si.name, "Gắn khách công nợ %s'):
		dung("câu ghi vết trong ban_hang còn đúng đầu câu: " + cau, cau in nguon)
	ct = open(os.path.join(os.path.dirname(b.__file__), "chung_tu.py"), encoding="utf-8").read()
	dung("câu gỡ huỷ trong chung_tu còn đúng", '"Gỡ dấu huỷ, phiếu dùng lại bình thường."' in ct)
	la("mỗi đầu câu sửa đều có trong danh mục", sorted(b.DAU_SUA),
		sorted(["Sửa hoá đơn", "Đổi ngày hoá đơn", "Gắn khách công nợ", "Gỡ dấu huỷ"]))

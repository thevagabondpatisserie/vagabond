"""v644 (anh Việt 07/11/2026, duyệt mẫu cùng ngày): ảnh bánh trên web quản MỘT nơi.

Ca gốc: Very Berry (3 size BAWC00086/87/88) hiện 4 ảnh giống nhau vì mỗi size
mang cùng một tấm trong hồ sơ món (3 tệp khác tên) cộng bản Pancake của chính
tấm đó, còn máy chỉ loại trùng theo đường dẫn. Luồng mới: bánh chỉ lên web khi
có bản ghi Bánh trên web (nút Đưa lên web), Marketing thêm ảnh ở thẻ Bánh, chưa
bật thì khách không thấy; ảnh trùng loại theo nội dung (dHash).

Các ca chạy hàm THẬT (banh_web, kiem_banh.co_the_ban_hom_nay,
_dat_truoc_theo_decor), chỉ thay tầng Frappe bằng bản giả.
"""
import io
import json
import types
from unittest.mock import patch

from vagabond import banh_web as bw
from vagabond import kiem_banh as kb
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_len_web_606 import ITEM, _chay, _dong

# Ba tệp hồ sơ món của Very Berry (cùng một ảnh) và hai ảnh Pancake (một là bản
# nén khác của chính tấm đó, một là ảnh cận cảnh khác hẳn), như site 07/11/2026.
B_VB = "f0e1d2c3b4a59687"
B_VB_PANCAKE = "f0e1d2c3b4a59685"   # lệch 1 bit: cùng tấm, nén khác
B_CAN = "0f1e2d3c4b5a6978"          # ảnh cận cảnh, khác hẳn


def _danh_muc():
	"""Cùng cách thu_diem_ban_631: Frappe giả không có frappe.model.naming."""
	import sys
	if "vagabond.danh_muc" not in sys.modules and "frappe.model.naming" not in sys.modules:
		sys.modules["frappe.model.naming"] = types.SimpleNamespace(getseries=lambda *a: "00001")
	from vagabond import danh_muc
	return danh_muc


def _bg(ten, trang_thai, anh=(), mo_ta="", tang=""):
	return {"khoa": bw.khoa_banh(ten), "ten": ten, "trang_thai": trang_thai,
		"anh": json.dumps([{"url": u, "bam": b} for u, b in anh]), "mo_ta": mo_ta, "tang": tang, "ma_hang": ""}


@ca("v644 khoá bánh: tên không size, viết thường, gọn khoảng trắng, cùng cách web gom size")
def _():
	la("gọn", bw.khoa_banh("  Very   Berry "), "very berry")
	la("NFC", bw.khoa_banh("Phi Tử Tiếu"), bw.khoa_banh("Phi Tử Tiếu"))
	goc, cm = kb._tach_ten_size("Bánh Ổ Very Berry, size 20cm")
	la("khớp tên web gom size", (bw.khoa_banh(goc), cm), ("very berry", 20))


@ca("v644 ảnh lưu: bỏ ảnh riêng tư và rác, nhận chuỗi lẫn {url,bam}, JSON hỏng ra rỗng")
def _():
	la("lọc", bw.doc_anh(json.dumps(["/files/a.jpg", {"url": "/private/files/b.jpg"}, {"url": ""}, 5, {"url": "https://x/c.webp", "bam": B_CAN}])),
		[{"url": "/files/a.jpg", "bam": ""}, {"url": "https://x/c.webp", "bam": B_CAN}])
	la("hỏng", bw.doc_anh("{khong phai json"), [])


@ca("v644 tái hiện Very Berry: 3 tệp hồ sơ món + bản Pancake cùng một tấm + ảnh cận cảnh gộp còn 2 ảnh")
def _():
	ds = [{"url": "/files/20260915-144218.png", "bam": B_VB},
		{"url": "/files/20260915-14421866b7a3.png", "bam": B_VB},
		{"url": "/files/20260915-1442186122d5.png", "bam": B_VB},
		{"url": "https://content.pancake.vn/a76a43.jpg", "bam": B_VB_PANCAKE},
		{"url": "https://content.pancake.vn/c0606405.jpg", "bam": B_CAN}]
	# Trước (đường cũ): chon_anh chỉ loại trùng đường dẫn, khách thấy cả 5 (4 tấm như một).
	from vagabond.anh_web import chon_anh
	la("trước: đường cũ giữ cả 5", len(chon_anh([x["url"] for x in ds[:3]], [x["url"] for x in ds[3:]])[1]), 5)
	la("sau: còn ảnh bìa và ảnh cận cảnh", [x["url"] for x in bw.gop_trung(ds)],
		["/files/20260915-144218.png", "https://content.pancake.vn/c0606405.jpg"])
	la("ảnh không băm được thì chỉ loại trùng đường dẫn", [x["url"] for x in bw.gop_trung([{"url": "/files/a"}, {"url": "/files/a"}, {"url": "/files/b"}])],
		["/files/a", "/files/b"])
	dung("lệch đúng ngưỡng vẫn là một tấm", bw.giong("0000000000000000", "000000000000003f"))
	dung("lệch quá ngưỡng là hai tấm", not bw.giong("0000000000000000", "000000000000007f"))


@ca("v644 bật Hiện trên web phải có ít nhất một ảnh; trạng thái lạ bị chặn")
def _():
	for tt, anh, ok in ((bw.DANG_HIEN, [], False), (bw.DANG_HIEN, ["/files/a.jpg"], True), (bw.DA_AN, [], True),
			(bw.CHO_ANH, [], True), ("Hiện", ["/files/a.jpg"], False)):
		try:
			bw.kiem_luu(tt, anh)
			kq = True
		except ValueError as e:
			kq = False
			if tt == bw.DANG_HIEN:
				la("câu chỉ việc", str(e), bw.CAU_CAN_ANH)
		la("%s với %d ảnh" % (tt, len(anh)), kq, ok)


@ca("v644 anh Việt chọn ẩn: chỉ bánh Đang hiện có ảnh lên web, mang đúng ảnh, mô tả, tầng của thẻ Bánh")
def _():
	sg = {x["khoa"]: x for x in (
		_bg("Very Berry", bw.DANG_HIEN, [("/files/vb.png", B_VB), ("https://p/can.jpg", B_CAN)], "Vỏ sô cô la.\nTrái cây tươi.", "Vỏ - shell\nKem - cream"),
		_bg("Roman De La Rose", bw.CHO_ANH),
		_bg("Hannari", bw.DA_AN, [("/files/h.png", "")]),
		_bg("Candle", bw.DANG_HIEN, []))}
	nhom = [{"ten": t, "anh": "", "sizes": [{"ma": t[:3], "_anh_erp": "/files/erp.png", "_anh_dong": "/files/d.png"}]}
		for t in ("Very Berry", "Roman De La Rose", "Hannari", "Candle", "Bánh Mới")]
	ra = bw.ap_nhom(nhom, sg)
	la("chỉ Very Berry", [g["ten"] for g in ra], ["Very Berry"])
	g = ra[0]
	la("ảnh của thẻ Bánh, không lấy ảnh hồ sơ món", (g["anh"], g["anhs"]), ("/files/vb.png", ["/files/vb.png", "https://p/can.jpg"]))
	la("mô tả và tầng", (g["mo_ta"], g["tang"], g["tu_web"]), ("Vỏ sô cô la. Trái cây tươi.", ["Vỏ - shell", "Kem - cream"], 1))
	dung("không lộ khoá riêng ở mọi nhóm, kể cả nhóm bị ẩn", all("_anh_erp" not in s and "_anh_dong" not in s for x in nhom for s in x["sizes"]))


def _vb_dong():
	return [_dong(ma_hang="BAWC00089", ten_banh="Very Berry", co_the_ban=2, hinh=""),
		_dong(ma_hang="BAWC00124X", ten_banh="Kankin", co_the_ban=1, hinh="")]


ITEM2 = dict(ITEM, BAWC00124X={"item_code": "BAWC00124X", "item_name": "Bánh Ổ Kankin, size 16cm", "image": "/files/k.jpg",
	"standard_rate": 900000, "disabled": 0, "is_sales_item": 1})


@ca("v644 tab Có sẵn hôm nay: bánh chưa bật bị bỏ khỏi CẢ nhóm, bảng số và danh sách món; bánh bật mang ảnh thẻ Bánh")
def _():
	sg = {x["khoa"]: x for x in (_bg("Very Berry", bw.DANG_HIEN, [("/files/vb.png", B_VB)], "Mô tả web"),
		_bg("Kankin", bw.CHO_ANH))}
	with patch.dict(ITEM, ITEM2, clear=False), patch.object(bw, "so_ghi", lambda: sg):
		kq = _chay(kb.co_the_ban_hom_nay, kiem_hom_nay=_vb_dong(), decor=[])
	la("nhóm", [g["ten"] for g in kq["nhom"]], ["Very Berry"])
	la("bảng số không còn Kankin", kq["banh"], {"BAWC00089": 2})
	la("danh sách món", [(m["ma"], m["anh"]) for m in kq["mon"]], [("BAWC00089", "/files/vb.png")])
	la("mô tả từ thẻ Bánh", kq["nhom"][0]["mo_ta"], "Mô tả web")


@ca("v644 tab Đặt bánh trước cũng theo thẻ Bánh")
def _():
	sg = {x["khoa"]: x for x in (_bg("Very Berry", bw.DA_AN, [("/files/vb.png", B_VB)]), _bg("Kankin", bw.DANG_HIEN, [("/files/k2.png", "")]))}
	decor = [_dong(ma_hang="BAWC00089", ten_banh="Very Berry", so_decor=3, hinh=""),
		_dong(ma_hang="BAWC00124X", ten_banh="Kankin", so_decor=2, hinh="")]
	with patch.dict(ITEM, ITEM2, clear=False), patch.object(bw, "so_ghi", lambda: sg):
		kq = _chay(kb._dat_truoc_theo_decor, decor=decor)
	la("chỉ Kankin", [(g["ten"], g["anh"]) for g in kq["nhom"]], [("Kankin", "/files/k2.png")])


@ca("v644 bảng Bánh chưa dùng (trước lần gieo đầu): web chạy đúng đường cũ, không ẩn bánh nào")
def _():
	goi = []
	with patch.object(bw, "so_ghi", lambda: None), patch.object(kb, "_bo_anh_mo_ta", lambda ds: goi.append(len(ds))):
		kq = _chay(kb.co_the_ban_hom_nay, kiem_hom_nay=[_dong(ma_hang="BAWC00089", ten_banh="Very Berry", co_the_ban=2, hinh="")], decor=[])
	la("đường cũ được gọi", goi[:1], [1])
	la("bánh vẫn hiện", list(kq["banh"]), ["BAWC00089"])
	f = types.SimpleNamespace(db=types.SimpleNamespace(table_exists=lambda dt: True), get_all=lambda *a, **k: [])
	with patch.object(bw, "frappe", f):
		la("bảng có mà rỗng thì coi như chưa dùng", bw.so_ghi(), None)
	f2 = types.SimpleNamespace(db=types.SimpleNamespace(table_exists=lambda dt: False))
	with patch.object(bw, "frappe", f2):
		la("chưa migrate", bw.so_ghi(), None)


class _Doc(dict):
	def __getattr__(self, k):
		if k == "flags":
			dict.__setitem__(self, "flags", types.SimpleNamespace())
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def save(self):
		self["_luu"] = self.get("_luu", 0) + 1

	def insert(self, **k):
		_Doc.kho.append(self)

	def as_dict(self):
		return dict(self)


def _frappe_gia(kho, item):
	da_bao = []
	f = types.SimpleNamespace()
	f.session = types.SimpleNamespace(user="uyen@vgb")
	f.throw = lambda m, *a, **k: (_ for _ in ()).throw(Exception(m))
	f.PermissionError = PermissionError
	f.get_roles = lambda: ["Accounts Manager"]
	f.db = types.SimpleNamespace(
		get_value=lambda dt, ten, fields, as_dict=False: _Doc(item[ten]) if ten in item else None,
		sql=lambda q, v=(): [[x["name"]] for x in kho if x["khoa"] == v[0]],
		table_exists=lambda dt: True)
	f.get_doc = lambda x, ten=None: (next(d for d in kho if d["name"] == ten) if ten else _Doc(x, name="BW-%d" % (len(kho) + 1)))
	f.utils = types.SimpleNamespace(now_datetime=lambda: "2026-11-07 20:00:00")
	f.log_error = lambda *a, **k: None
	f.get_all = lambda *a, **k: [dict(x) for x in kho]
	return f, da_bao


@ca("v644 nút Đưa lên web: bánh mới tạo thẻ Chờ ảnh và nhắn Marketing một lần; size khác của cùng bánh gắn vào thẻ cũ")
def _():
	kho = []
	_Doc.kho = kho
	item = {"BAWC00086": {"item_name": "Bánh Ổ Very Berry, size 12cm", "disabled": 0, "is_sales_item": 1, "standard_rate": 620000},
		"BAWC00087": {"item_name": "Bánh Ổ Very Berry, size 16cm", "disabled": 0, "is_sales_item": 1, "standard_rate": 900000},
		"BAWC00999": {"item_name": "Bánh Ổ Thử, size 16cm", "disabled": 0, "is_sales_item": 1, "standard_rate": 0}}
	f, _bao = _frappe_gia(kho, item)
	tin = []
	from vagabond import kenh_zalo
	danh_muc = _danh_muc()
	with patch.object(bw, "frappe", f), patch.object(danh_muc, "frappe", f), \
			patch.object(kb, "frappe", f), patch.object(kenh_zalo, "bao", lambda *a, **k: tin.append((a, k)) or ["Z1"]):
		r1 = bw.dua_len_web("BAWC00086")
		r2 = bw.dua_len_web("BAWC00087")
		try:
			bw.dua_len_web("BAWC00999")
			loi = ""
		except Exception as e:
			loi = str(e)
		try:
			bw.dua_len_web("BAWS00001")
			loi_si = ""
		except Exception as e:
			loi_si = str(e)
	la("một thẻ", [(x["khoa"], x["ten"], x["trang_thai"], x["ma_hang"]) for x in kho], [("very berry", "Very Berry", bw.CHO_ANH, "BAWC00086\nBAWC00087")])
	la("lần đầu mới, lần hai gắn thẻ cũ", (r1["moi"], r2["moi"]), (1, 0))
	dung("báo người bấm khách chưa thấy", "Khách chưa thấy" in r1["thong_bao"] and "khách chưa thấy" in r2["thong_bao"])
	la("nhắn Marketing đúng một lần, đúng tin", [(k["ma_tin"], k["khoa"], k["kiem"]) for a, k in tin], [("mkt_banh_cho_anh", "banh_cho_anh:very berry", "banh_cho_anh")])
	dung("mã giá 0 bị chặn", "chưa có giá" in loi)
	dung("mã bánh sỉ bị chặn", "bánh sỉ" in loi_si)


@ca("v644 quyền Đưa lên web: người Đồng bộ Pancake được (kế toán, thu mua, giám đốc) hoặc Marketing; thu ngân thì không")
def _():
	danh_muc = _danh_muc()
	for vai, duoc in ((["Accounts Manager"], True), (["Purchase User"], True), (["Marketing"], True), (["Sales User"], False)):
		f = types.SimpleNamespace(session=types.SimpleNamespace(user="a@b"), get_roles=lambda v=vai: v, PermissionError=PermissionError,
			throw=lambda m, *a, **k: (_ for _ in ()).throw(PermissionError(m)))
		with patch.object(bw, "frappe", f), patch.object(danh_muc, "frappe", f):
			try:
				bw._quyen_dua()
				kq = True
			except PermissionError:
				kq = False
		la(",".join(vai), kq, duoc)


@ca("v644 tin nhắc Marketing: tên bánh và việc cần làm, gọn khi nhiều bánh")
def _():
	la("rỗng", bw.chu_nhac([]), [])
	d = bw.chu_nhac(["B%d" % i for i in range(11)])
	dung("gọn", d[0].endswith("và 3 bánh khác.") and "B7" in d[0] and "B8" not in d[0])
	dung("việc", "thẻ Bánh" in d[1] and "Khách chưa thấy" in d[1])


@ca("v644 băm hình thật: cùng tấm khác cỡ và khác nén là một, ảnh khác là hai (máy có Pillow)")
def _():
	try:
		from PIL import Image, ImageDraw
	except ImportError:
		return

	def anh(ve, co, kieu):
		a = Image.new("RGB", (400, 300), (30, 20, 20))
		d = ImageDraw.Draw(a)
		ve(d)
		a = a.resize(co)
		b = io.BytesIO()
		a.save(b, kieu, quality=60) if kieu == "JPEG" else a.save(b, kieu)
		return b.getvalue()
	tron = lambda d: (d.ellipse((60, 40, 340, 260), fill=(200, 30, 40)), d.rectangle((150, 120, 250, 180), fill=(250, 240, 230)))
	soc = lambda d: [d.rectangle((i * 40, 0, i * 40 + 20, 300), fill=(240, 200, 40)) for i in range(10)]
	a1, a2, a3 = bw.bam_hinh(anh(tron, (400, 300), "PNG")), bw.bam_hinh(anh(tron, (200, 150), "JPEG")), bw.bam_hinh(anh(soc, (400, 300), "PNG"))
	dung("đọc được", len(a1) == 16 and len(a3) == 16)
	dung("cùng tấm", bw.giong(a1, a2))
	dung("khác tấm", not bw.giong(a1, a3))
	la("không phải ảnh", bw.bam_hinh(b"khong phai anh"), "")


@ca("v644 nút Đưa lên web trên app và thẻ Bánh của trình biên tập: bấm thật bằng node (hanh_vi)")
def _():
	import subprocess
	from pathlib import Path
	thu = Path(__file__).parent / "hanh_vi"
	for tep in ("dua_len_web_644.js", "bien_tap_banh_644.js"):
		r = subprocess.run(["node", str(thu / tep)], capture_output=True, text=True, timeout=120)
		la(tep + " mã trả về", (r.returncode, (r.stdout + r.stderr)[-600:] if r.returncode else ""), (0, ""))

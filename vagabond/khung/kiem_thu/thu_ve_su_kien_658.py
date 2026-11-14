"""v658 Vé sự kiện (anh Việt chọn A 14/11/2026): mục Tiệc nâng thành Vé sự kiện.

Khách giữ chỗ trên web (tiec_web.dang_ky, đã có ca khoá hàng ở
thu_bien_tap_theo_the_586), nhận mã vé. Màn Khách sự kiện trên app cho Quầy,
Sales, Marketing xem danh sách khách và bấm "Đã vào cửa".

Ca ở đây: phép thuần (mã vé, dòng khách, đếm, luật đổi dấu vào cửa), hàm
máy chủ thật với Frappe giả (khoá dòng trước khi đọc trạng thái, bấm hai lần
không đổi, vé huỷ bị chặn, đọc đủ mọi đăng ký), một nguồn cho danh sách vai
và loại sự kiện giữa máy chủ, trang web, trình biên tập, app; và chạy bộ ca
node hanh_vi/vanh_658.mjs (Vành nghiêng, Vé sự kiện).
"""
import json
import os
import re
import subprocess
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la

if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda *a, **k: (lambda f: f)

from vagabond import noi_dung_web as nw  # noqa: E402
from vagabond import tiec_web as tw  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(duong):
	return open(os.path.join(GOC, duong), encoding="utf-8").read()


@ca("v658 Vành nghiêng và Vé sự kiện: bộ ca node hanh_vi/vanh_658.mjs đều đạt")
def _():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/vanh_658.mjs"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-1500:] + r.stderr[-800:], r.returncode, 0)
	dung("đủ 8 ca", "8 ca dat, 0 ca hong" in r.stdout)


@ca("v658 mã vé: 8 ký tự đầu tên phiếu, chữ hoa; phiếu cũ chưa có ô mã vé vẫn ra đúng mã khách đã được báo")
def _():
	la("mã", tw.ma_ve("a1b2c3d4e5f6"), "A1B2C3D4")
	cu = tw.dong_khach({"name": "ffee0011aa", "ten": "Lan", "so_ve": 2, "trang_thai": "Chờ xác nhận"})
	la("phiếu cũ", cu["ma_ve"], "FFEE0011")
	moi = tw.dong_khach({"name": "x", "ma_ve": "ABCD1234", "so_ve": "3", "trang_thai": "Đã xác nhận", "da_vao_cua": 1})
	la("phiếu mới", (moi["ma_ve"], moi["so_ve"], moi["da_vao"]), ("ABCD1234", 3, True))
	huy = tw.dong_khach({"name": "y", "so_ve": 2, "trang_thai": "Đã hủy", "da_vao_cua": 1})
	dung("vé huỷ không tính đã vào", not huy["da_vao"])


@ca("v658 đếm của sự kiện: bỏ vé đã huỷ, cộng số vé đã vào cửa theo số vé từng phiếu")
def _():
	ds = [tw.dong_khach(r) for r in (
		{"name": "a", "so_ve": 2, "trang_thai": "Đã xác nhận", "da_vao_cua": 1},
		{"name": "b", "so_ve": 3, "trang_thai": "Chờ xác nhận"},
		{"name": "c", "so_ve": 4, "trang_thai": "Đã hủy", "da_vao_cua": 1})]
	la("đếm", tw.tong_khach(ds), {"so_dk": 2, "so_ve": 5, "da_vao": 2})


@ca("v658 luật dấu Đã vào cửa: vé huỷ chặn; bấm hai lần không đổi gì; bỏ dấu được")
def _():
	dung("huỷ", "huỷ" in tw.ly_do_vao_cua("Đã hủy", 0, True))
	la("đã vào bấm lại", tw.ly_do_vao_cua("Đã xác nhận", 1, True), "giu")
	la("chưa vào bỏ dấu", tw.ly_do_vao_cua("Chờ xác nhận", 0, False), "giu")
	la("đánh dấu", tw.ly_do_vao_cua("Chờ xác nhận", 0, True), "")
	la("bỏ dấu", tw.ly_do_vao_cua("Đã thanh toán", 1, False), "")


class _Db:
	def __init__(self, hang):
		self.hang = hang
		self.goi = []

	def get_value(self, dt, ten, cot, as_dict=False, for_update=False):
		self.goi.append(("get", ten, for_update))
		r = self.hang.get(ten)
		if r is None:
			return None
		return types.SimpleNamespace(**r) if isinstance(cot, list) and as_dict and "name" in cot and len(cot) == 3 else dict(r)

	def set_value(self, dt, ten, gia_tri):
		self.goi.append(("set", ten, dict(gia_tri)))
		self.hang[ten].update(gia_tri)


def _vao_frappe(db, vai=("Sales User",)):
	fr = sys.modules["frappe"]
	return [um.patch.object(fr, "db", db, create=True), um.patch.object(fr, "get_roles", lambda *a: list(vai), create=True),
		um.patch.object(fr, "throw", lambda m, *a: (_ for _ in ()).throw(ValueError(m)), create=True),
		um.patch.object(fr.utils, "now_datetime", lambda: "2026-11-22 15:05:00", create=True),
		um.patch.object(fr, "PermissionError", getattr(fr, "PermissionError", PermissionError), create=True)]


def _chay(ps, fn):
	for p in ps:
		p.start()
	try:
		return fn()
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v658 Đã vào cửa (hàm máy chủ thật): khoá đúng dòng trước khi đọc trạng thái; bấm hai lần chỉ ghi một lần; vé huỷ bị chặn; vai khác bị chặn")
def _():
	hang = {"p1": {"name": "p1", "ma_ve": "P1", "ten": "Lan", "sdt": "0909", "so_ve": 2, "trang_thai": "Đã xác nhận", "da_vao_cua": 0, "vao_cua_luc": None, "ghi_chu": ""},
		"p2": {"name": "p2", "ma_ve": "P2", "ten": "Mai", "sdt": "0908", "so_ve": 1, "trang_thai": "Đã hủy", "da_vao_cua": 0, "vao_cua_luc": None, "ghi_chu": ""}}
	db = _Db(hang)
	kq = _chay(_vao_frappe(db), lambda: tw.vao_cua("p1", 1))
	la("đọc đầu tiên có khoá", db.goi[0], ("get", "p1", True))
	dung("đã vào", kq["da_vao"] and kq["vao_luc"].startswith("2026-11-22"))
	_chay(_vao_frappe(db), lambda: tw.vao_cua("p1", 1))
	la("bấm hai lần chỉ ghi một lần", len([g for g in db.goi if g[0] == "set"]), 1)
	kq = _chay(_vao_frappe(db), lambda: tw.vao_cua("p1", 0))
	dung("bỏ dấu", not kq["da_vao"])
	try:
		_chay(_vao_frappe(db), lambda: tw.vao_cua("p2", 1))
		dung("vé huỷ phải bị chặn", False)
	except ValueError as e:
		dung("câu báo vé huỷ", "huỷ" in str(e))
	try:
		_chay(_vao_frappe(db, ("Website User",)), lambda: tw.vao_cua("p1", 1))
		dung("vai khác phải bị chặn", False)
	except ValueError as e:
		dung("câu báo vai", "Quầy" in str(e))


@ca("v658 danh sách khách và danh sách sự kiện đọc ĐỦ mọi đăng ký (không giới hạn trang): số vé ở cửa phải đúng thật")
def _():
	nguon = _doc("vagabond/tiec_web.py")
	for ham in ("def ds_su_kien", "def khach_su_kien"):
		than = nguon[nguon.index(ham):]
		than = than[:than.index("\n\n\n") if "\n\n\n" in than else len(than)]
		dung(ham + " đọc đủ", "limit_page_length=0" in than)
	goi = []
	fr = sys.modules["frappe"]
	ps = [um.patch.object(fr, "get_roles", lambda *a: ["Marketing"], create=True),
		um.patch.object(fr, "get_all", lambda dt, **k: goi.append(k) or [dict(name="a%d" % i, so_ve=1, trang_thai="Chờ xác nhận") for i in range(25)], create=True)]
	kq = _chay(ps, lambda: tw.khach_su_kien("tiec-1"))
	la("đủ 25 dòng", (len(kq["khach"]), kq["tong"]["so_ve"]), (25, 25))
	la("không giới hạn", goi[0].get("limit_page_length"), 0)


@ca("v658 một nguồn: danh sách vai màn Khách sự kiện trùng tuyệt đối giữa máy chủ và app")
def _():
	m = re.search(r"var QUYEN_SK = \[(.*?)\];", _doc("vagabond/public/js/bep/74-khach-su-kien.js"), re.S)
	la("hai bản", re.findall(r"'([^']+)'", m.group(1)), list(tw.QUYEN_SK))


@ca("v658 một nguồn: ba loại sự kiện trùng tuyệt đối giữa máy chủ, trang web và trình biên tập; loại lạ bị chặn ở cửa lưu")
def _():
	web = re.search(r"export const LOAI_SU_KIEN = (\{.*?\});", _doc("vagabond/public/web_vue/banh/ve-su-kien.js")).group(1)
	bt = re.search(r"const LOAI_SK = (\{.*?\});", _doc("vagabond/public/web_order/bien-tap-moi.js")).group(1)
	doi = lambda s: dict(re.findall(r"(\w+): '([^']+)'", s))
	la("web", doi(web), nw.LOAI_SU_KIEN)
	la("trình biên tập", doi(bt), nw.LOAI_SU_KIEN)
	for ma in ("", "tiec", "ra_mat", "dien_gia"):
		nw._kiem_truong_586({"loai_su_kien": ma})
	try:
		nw._kiem_truong_586({"loai_su_kien": "hoi_thao"})
		dung("loại lạ phải bị chặn", False)
	except ValueError as e:
		dung("câu báo", "Diễn giả" in str(e))
	dung("trường được lưu", "loai_su_kien" in nw.TRUONG)


@ca("v658 phiếu đăng ký có ô mã vé, Đã vào cửa, Vào cửa lúc; đẩy mốc modified để migrate đồng bộ; khách sửa không đổi được mã vé")
def _():
	d = json.loads(_doc("vagabond/vagabond/doctype/vagabond_dang_ky_tiec/vagabond_dang_ky_tiec.json"))
	ten = {f["fieldname"]: f for f in d["fields"]}
	la("ba ô", [ten["ma_ve"]["fieldtype"], ten["da_vao_cua"]["fieldtype"], ten["vao_cua_luc"]["fieldtype"]], ["Data", "Check", "Datetime"])
	dung("thứ tự trường đủ", {"ma_ve", "da_vao_cua", "vao_cua_luc"} <= set(d["field_order"]))
	dung("mốc modified", d.get("modified", "") >= "2026-11-14")
	dung("mã vé giữ nguyên khi sửa", '"ma_ve"' in _doc("vagabond/tiec_web.py").split("def kiem_phieu")[1].split("def ")[0])


@ca("Codex #566 vòng 3: ô tìm ở màn Khách sự kiện tìm ra vé có mã toàn chữ số (12345678) chứ không chỉ tìm trong số điện thoại; tìm số điện thoại, 4 số cuối, tên, mã có chữ vẫn đúng")
def _():
	nen = _doc("vagabond/public/js/bep/00-nen.js")
	ham = []
	for ten in ("vgbChuan", "vgbKhop"):
		m = re.search(r"\nfunction " + ten + r"\(.*?\n\}\n", nen, re.S)
		dung("có " + ten, m is not None)
		ham.append(m.group(0))
	m = re.search(r"\nfunction skKhop\(.*?\n\}\n", _doc("vagabond/public/js/bep/74-khach-su-kien.js"), re.S)
	dung("có skKhop", m is not None)
	ham.append(m.group(0))
	js = "\n".join(ham) + """
var so = {ma_ve: '12345678', ten: 'Lan Anh', sdt: '0901234567'};
var chu = {ma_ve: 'A1B2C3D4', ten: 'Minh', sdt: '0912000111'};
console.log(JSON.stringify([skKhop(so, '12345678'), skKhop(so, '1234 5678'), skKhop(chu, '12345678'),
  skKhop(so, '0901 234 567'), skKhop(chu, '0111'), skKhop(so, '4567'), skKhop(chu, 'a1b2'), skKhop(so, 'lan anh'), skKhop(chu, 'lan')]));
"""
	r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
	la(r.stderr[-600:], r.returncode, 0)
	la("kết quả", json.loads(r.stdout), [True, True, False, True, True, True, True, True, False])

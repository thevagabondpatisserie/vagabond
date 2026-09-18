# -*- coding: utf-8 -*-
"""v509: tai khoan nhan tien cua nha cung cap sua duoc tren app, va phieu
chi in ra co so tai khoan.

Uyen bao 18/09/2026: phieu APP-26-09-663 in ra khong co so tai khoan nha cung
cap, va danh muc nha cung cap khong co cho nao de nhap. Ba cua sua:
  1. ncc.luu_tai_khoan: tao hoac SUA dung mot Bank Account cua nha cung cap.
  2. Phieu tra truoc va ho so thanh toan gan party_bank_account tu cung mot
     nguon ncc.tk_mac_dinh.
  3. Mau in doc tai khoan mac dinh cua doi tac khi o tren phieu trong, va ke
     ten chung tu dinh kem.
"""

import io
import os
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import ncc
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	return io.open(os.path.join(GOC, *duong), encoding="utf-8").read()


@ca("v509: soat so tai khoan - bo dau cham va khoang trang, tu choi ky tu la")
def _soat():
	la("số sạch", ncc.soat_so_tk(" 3156 1568 ")[0], "31561568")
	la("bỏ dấu chấm", ncc.soat_so_tk("0315.917.706")[0], "0315917706")
	la("chữ cái lên hoa", ncc.soat_so_tk("vgb123456")[0], "VGB123456")
	dung("trống thì báo", "Chưa nhập" in ncc.soat_so_tk("")[1])
	dung("ký tự lạ thì báo", "ký tự lạ" in ncc.soat_so_tk("123456@78")[1])
	dung("quá ngắn thì báo", "6 tới 20" in ncc.soat_so_tk("123")[1])
	dung("quá dài thì báo", "6 tới 20" in ncc.soat_so_tk("1" * 21)[1])


class _To(SimpleNamespace):
	def __init__(self, **k):
		super().__init__(**k)
		self.flags = SimpleNamespace()
		self.da_luu = 0

	def get(self, k, d=None):
		return getattr(self, k, d)

	def save(self, ignore_permissions=False):
		self.da_luu += 1


def _chay(co_san, so_tk="31561568", ngan_hang="MB", chu_tk="", co_phieu_tro=False):
	giu = {}

	def _get_all(dt, **k):
		if dt == "Bank Account":
			return [{"name": "TK-CU"}] if co_san else []
		return []

	def _get_doc(dt, ten):
		giu["sua"] = _To(name=ten, party_type="Supplier", party="NCC-1", is_default=1)
		return giu["sua"]

	def _new_doc(dt):
		giu["moi"] = _To()
		return giu["moi"]

	gia = SimpleNamespace(
		get_all=_get_all, get_doc=_get_doc, new_doc=_new_doc,
		db=SimpleNamespace(
			exists=lambda dt, n: (co_phieu_tro if dt == "Payment Entry" else True),
			set_value=lambda dt, n, f, v, **k: giu.setdefault("bo_mac_dinh", []).append((n, f, v)),
			get_value=lambda dt, n, f=None, **k: (
				{"account_name": "A", "bank_account_no": "31561568", "bank": "MB - Ngân hàng TMCP Quân đội"}
				if isinstance(f, list) else "CÔNG TY DUY LỢI"),
		),
		throw=lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[0])),
		get_roles=lambda: ["Thu mua"],
	)
	from vagabond import ngan_hang as nh
	with patch.object(ncc, "frappe", gia), \
			patch.object(nh, "chuan_hoa_hoac_bao", lambda t, o="": "MB - Ngân hàng TMCP Quân đội"):
		ra = ncc.luu_tai_khoan("NCC-1", so_tk, ngan_hang, chu_tk)
	return ra, giu


@ca("v509: luu_tai_khoan - chua co thi TAO mot ban ghi gan nha cung cap, mac dinh")
def _tao_moi():
	ra, giu = _chay(co_san=False, chu_tk="")
	la("lưu được", ra["ok"], 1)
	t = giu.get("moi")
	dung("có tạo bản ghi mới", t is not None)
	la("gắn đúng nhà cung cấp", (t.party_type, t.party), ("Supplier", "NCC-1"))
	la("là tài khoản mặc định", t.is_default, 1)
	la("số tài khoản đã làm sạch", t.bank_account_no, "31561568")
	la("ngân hàng đã chuẩn hoá", t.bank, "MB - Ngân hàng TMCP Quân đội")
	la("chủ tài khoản trống thì lấy tên nhà cung cấp", t.account_name, "CÔNG TY DUY LỢI")
	la("đã save", t.da_luu, 1)


@ca("v509: luu_tai_khoan - da co thi SUA dung ban ghi do, khong tao cai thu hai")
def _sua_cu():
	ra, giu = _chay(co_san=True, so_tk="0315917706", chu_tk="DUY LOI JSC")
	dung("không tạo mới", "moi" not in giu)
	t = giu["sua"]
	la("sửa đúng bản ghi cũ", t.name, "TK-CU")
	la("số mới", t.bank_account_no, "0315917706")
	la("chủ tài khoản theo người nhập", t.account_name, "DUY LOI JSC")
	la("đã save", t.da_luu, 1)


@ca("v509: tai khoan da co phieu chi tro toi thi GIU NGUYEN, tao ban moi lam mac dinh")
def _co_phieu_tro():
	# Codex #346: sua de len la phieu da duyet in lai ra nguoi nhan khac.
	ra, giu = _chay(co_san=True, so_tk="0315917706", co_phieu_tro=True)
	dung("bản cũ không bị sửa", "sua" not in giu)
	la("bản cũ bỏ cờ mặc định", giu.get("bo_mac_dinh"), [("TK-CU", "is_default", 0)])
	t = giu.get("moi")
	dung("tạo bản mới", t is not None)
	la("bản mới là mặc định, đúng nhà", (t.is_default, t.party), (1, "NCC-1"))
	la("bản mới mang số mới", t.bank_account_no, "0315917706")


@ca("v509: luu_tai_khoan - so tai khoan sai thi tu choi truoc khi cham co so du lieu")
def _tu_choi():
	loi = ""
	try:
		_chay(co_san=False, so_tk="12@3")
	except AssertionError as e:
		loi = str(e)
	dung("bị chặn", "ký tự lạ" in loi)


@ca("v509: phieu tra truoc va ho so thanh toan gan tai khoan nhan tien tu MOT nguon")
def _mot_nguon():
	tt = _doc("vagabond", "tra_truoc.py")
	hs = _doc("vagabond", "ho_so_tt.py")
	dung("trả trước dùng ncc.tk_mac_dinh", "pe.party_bank_account = _ncc.tk_mac_dinh(d.supplier)" in tt)
	dung("hồ sơ thanh toán dùng ncc.tk_mac_dinh", "pe.party_bank_account = _ncc.tk_mac_dinh(ma_ncc)" in hs)
	# Khong con cho nao tu doc Bank Account theo party de gan len phieu.
	dung("không chỗ nào khác gán party_bank_account", tt.count("party_bank_account") == 2 and hs.count("party_bank_account") == 1)


@ca("v509: mau in doc tai khoan mac dinh cua doi tac khi phieu trong, va ke ten tep dinh kem")
def _mau_in():
	m = _doc("vagabond", "mau_in", "chung_tu_thanh_toan.html")
	dung("có đường lùi theo đối tác", 'filters={"party_type": doc.party_type, "party": doc.party, "disabled": 0}' in m)
	dung("chỉ lùi khi ô trên phiếu trống VÀ phiếu còn nháp", "{% if not pb_ten and doc.docstatus == 0 and doc.party_type and doc.party %}" in m)
	dung("kê tên tệp đính kèm", '"attached_to_doctype": doc.doctype' in m and "Chứng từ đính kèm:" in m)
	dung("chi_tiet trả tai_khoan cho màn", '"tai_khoan": _tai_khoan(ncc),' in _doc("vagabond", "ncc.py"))
	j = _doc("vagabond", "public", "js", "bep", "20-danh-muc-quyen.js")
	dung("màn nhà cung cấp có nút lưu tài khoản", "vagabond.ncc.luu_tai_khoan" in j and "id=\"nccTkNh\"" in j)

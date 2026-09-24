"""v526, chị Dung và anh Việt 24/09/2026.

1. Ghi sổ thẳng có bước hạch toán từng dòng. Ca thật: hoá đơn xăng
   HDM-26-09-00335 (Xăng dầu Khu vực II, 92.081 đ) ghi thẳng rơi vào 632 vì
   dòng không gắn Món. Anh Việt chọn: chọn tài khoản từng dòng, máy gợi ý theo
   lần trước của đúng nhà cung cấp.
2. Hoá đơn đến sau của phiếu Chi từ TK công ty: nối đủ thì hồ sơ thành hợp lệ
   tính thuế, tờ hoá đơn đã nối không ghi sổ (anh Việt chọn "chặn ghi sổ,
   không tách VAT").
3. Quyền Repost cho kế toán FIN để sửa tài khoản trên tờ đã ghi sổ.

Mọi ca chạy HÀM THẬT, chỉ thay lớp dữ liệu. Không dò chuỗi.
"""
import json
from types import SimpleNamespace

from vagabond.khung.kiem_thu.nen import ca, dung, la


class _Loi(Exception):
	pass


def _throw(msg, *a, **k):
	raise _Loi(msg)


class _D(dict):
	def __getattr__(self, k):
		try:
			return self[k]
		except KeyError:
			raise AttributeError(k)

	def __setattr__(self, k, v):
		self[k] = v


CTY = "CÔNG TY TNHH PATISSERIE VAGABOND"
TK = {
	"6417 - Chi phí dịch vụ mua ngoài - TV": dict(company=CTY, is_group=0, disabled=0, root_type="Expense", account_type=""),
	"632 - Giá vốn hàng bán - TV": dict(company=CTY, is_group=0, disabled=0, root_type="Expense", account_type="Cost of Goods Sold"),
	"242 - Chi phí chờ phân bổ - TV": dict(company=CTY, is_group=0, disabled=0, root_type="Asset", account_type=""),
	"641 - Chi phí bán hàng - TV": dict(company=CTY, is_group=1, disabled=0, root_type="Expense", account_type=""),
	"6418 - Chi phí khác - TV": dict(company=CTY, is_group=0, disabled=1, root_type="Expense", account_type=""),
	"3311 - Phải trả - TV": dict(company=CTY, is_group=0, disabled=0, root_type="Liability", account_type="Payable"),
	"1331 - Thuế GTGT - TV": dict(company=CTY, is_group=0, disabled=0, root_type="Asset", account_type="Tax"),
	"6417 - Chi phí - TVD": dict(company="The Vagabond (Demo)", is_group=0, disabled=0, root_type="Expense", account_type=""),
}
T6417, T632, T242 = "6417 - Chi phí dịch vụ mua ngoài - TV", "632 - Giá vốn hàng bán - TV", "242 - Chi phí chờ phân bổ - TV"
HANG_KHO = {"NVLT00001": 1, "DV-XANG": 0}


class _Phieu:
	"""Tờ giả có .items là DANH SÁCH như Document thật (dict thì .items là hàm)."""

	def __init__(self, **k):
		self.__dict__.update(k)

	def get(self, k, mac_dinh=None):
		return self.__dict__.get(k, mac_dinh)

	def __getitem__(self, k):
		return self.__dict__[k]


def _to(dong, **k):
	"""Tờ hoá đơn mua giả: dong = [(tên dòng, mã, phiếu nhập, tài khoản)]."""
	doc = _Phieu(name="HDM-26-09-00334", company=CTY, supplier="XDKV2", supplier_name="Xăng dầu KV II",
		docstatus=0, status="Draft", grand_total=80000, vgb_tk_chi_phi=None,
		items=[_D(name=t, idx=i + 1, item_code=m, item_name="Xăng E10 RON 95" if not m else m,
			purchase_receipt=p, expense_account=tk, amount=80000) for i, (t, m, p, tk) in enumerate(dong)])
	doc.flags = _D()
	doc.__dict__.update(k)
	return doc


def _fr(**k):
	def get_value(dt, ten, truong=None, as_dict=False):
		if dt == "Item":
			return HANG_KHO.get(ten, 0)
		if dt == "Account":
			return _D(TK[ten]) if ten in TK else None
		return None
	ns = SimpleNamespace(throw=_throw, db=SimpleNamespace(get_value=get_value))
	for kk, v in k.items():
		setattr(ns, kk, v)
	return ns


def _voi(mod, fr, ham):
	cu = mod.frappe
	mod.frappe = fr
	try:
		return ham()
	finally:
		mod.frappe = cu


# ------------------------------------------------------------ phần thuần

@ca("#526 gợi ý tài khoản: khai trên Món trước, rồi tài khoản đang có khác mặc định, rồi lần trước của NCC")
def _goi_y():
	from vagabond.hach_toan_thang import goi_y
	la("khai trên Món thắng", goi_y(T632, T632, T6417, T242), (T242, "mon"))
	la("đang có khác mặc định thì giữ", goi_y(T242, T632, T6417, ""), (T242, "dang_co"))
	la("đang là 632 mặc định thì lấy lần trước của NCC", goi_y(T632, T632, T6417, ""), (T6417, "lan_truoc"))
	la("không có gì thì về mặc định", goi_y(T632, T632, "", ""), (T632, "mac_dinh"))


@ca("#526 nhắc đỏ khi dòng chi phí để 632 giá vốn")
def _canh_bao():
	from vagabond.hach_toan_thang import canh_bao
	dung("632 bị nhắc", "giá vốn" in canh_bao(T632))
	la("6417 không nhắc", canh_bao(T6417), "")


@ca("#526 soát bộ tài khoản: dòng thiếu, dòng hàng kho, dòng lạ đều bị gọi tên")
def _loi_chon():
	from vagabond.hach_toan_thang import loi_chon
	cp, khac = {"D1": 1, "D2": 2}, {"D3": 3}
	la("đủ thì không lỗi", loi_chon(cp, khac, {"D1": T6417, "D2": T242}), [])
	loi = loi_chon(cp, khac, {"D1": T6417})
	dung("gọi tên dòng 2 thiếu", any("Dòng 2 chưa chọn" in x for x in loi))
	loi = loi_chon(cp, khac, {"D1": T6417, "D2": T242, "D3": T6417})
	dung("chặn đổi dòng hàng kho", any("Dòng 3 là hàng qua kho" in x for x in loi))
	loi = loi_chon(cp, khac, {"D1": T6417, "D2": T242, "LA": T6417})
	dung("chặn dòng không còn trên tờ", any("không còn trên hoá đơn" in x for x in loi))


@ca("#526 tài khoản không nhận chi phí: tổng hợp, ngừng dùng, công ty khác, công nợ, thuế, nợ phải trả")
def _loi_tai_khoan():
	from vagabond.hach_toan_thang import loi_tai_khoan
	la("6417 dùng được", loi_tai_khoan(TK[T6417], CTY), "")
	la("242 tài sản dùng được", loi_tai_khoan(TK[T242], CTY), "")
	dung("tổng hợp", "tổng hợp" in loi_tai_khoan(TK["641 - Chi phí bán hàng - TV"], CTY))
	dung("ngừng dùng", "ngừng" in loi_tai_khoan(TK["6418 - Chi phí khác - TV"], CTY))
	dung("công ty demo", "công ty khác" in loi_tai_khoan(TK["6417 - Chi phí - TVD"], CTY))
	dung("công nợ", "Payable" in loi_tai_khoan(TK["3311 - Phải trả - TV"], CTY))
	dung("thuế", "Tax" in loi_tai_khoan(TK["1331 - Thuế GTGT - TV"], CTY))
	dung("không tồn tại", "không tồn tại" in loi_tai_khoan(None, CTY))


# ------------------------------------------------------------ đặt tài khoản

@ca("#526 ca xăng: dòng không mã đang 632, chọn 6417 thì đặt đúng 6417 và báo hook đừng đè")
def _ap_xang():
	from vagabond import hach_toan_thang as H
	doc = _to([("R1", "", "", T632)])
	_voi(H, _fr(), lambda: H.ap_tai_khoan(doc, {"R1": T6417}))
	la("dòng xăng về 6417", doc.items[0].expense_account, T6417)
	dung("cờ người chọn đã đặt", H.nguoi_da_chon(doc, "R1"))


@ca("#526 chọn tài khoản cho dòng hàng kho hay tài khoản sai thì dừng, CHƯA đổi dòng nào")
def _ap_chan():
	from vagabond import hach_toan_thang as H
	doc = _to([("R1", "", "", T632), ("R2", "NVLT00001", "PNK-1", "Kho chờ")])
	try:
		_voi(H, _fr(), lambda: H.ap_tai_khoan(doc, {"R1": T6417, "R2": T6417}))
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("báo dòng 2 là hàng kho", "Dòng 2 là hàng qua kho" in loi)
	la("dòng 1 chưa bị đổi", doc.items[0].expense_account, T632)
	doc = _to([("R1", "", "", T632)])
	try:
		_voi(H, _fr(), lambda: H.ap_tai_khoan(doc, {"R1": "3311 - Phải trả - TV"}))
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("chặn tài khoản công nợ", "Payable" in loi)
	la("dòng chưa bị đổi", doc.items[0].expense_account, T632)


@ca("#526 phiếu dịch vụ có ô tài khoản đầu phiếu: khớp theo người chọn, chọn khác nhau thì bỏ trống ô đó")
def _ap_dich_vu():
	from vagabond import hach_toan_thang as H
	doc = _to([("R1", "", "", T632), ("R2", "", "", T632)], vgb_tk_chi_phi=T632)
	_voi(H, _fr(), lambda: H.ap_tai_khoan(doc, {"R1": T6417, "R2": T6417}))
	la("cùng một tài khoản thì ô đầu phiếu theo", doc.vgb_tk_chi_phi, T6417)
	doc = _to([("R1", "", "", T632), ("R2", "", "", T632)], vgb_tk_chi_phi=T632)
	_voi(H, _fr(), lambda: H.ap_tai_khoan(doc, {"R1": T6417, "R2": T242}))
	la("khác nhau thì bỏ trống ô đầu phiếu", doc.vgb_tk_chi_phi, None)


@ca("#526 hook khai trên Món KHÔNG đè dòng kế toán vừa chọn, dòng khác vẫn theo Món")
def _hook_mon():
	from vagabond import dung_lai_hddt as L
	doc = _to([("R1", "DV-XANG", "", T6417), ("R2", "DV-XANG", "", T6417)], custom_minvoice_id="MV1")
	doc.flags["vgb_tk_nguoi_chon"] = {"R1": T6417}

	def get_value(dt, ten, truong=None, as_dict=False):
		if dt == "Item":
			return 0
		if dt == "Item Default":
			return T242
		return None
	_voi(L, SimpleNamespace(throw=_throw, db=SimpleNamespace(get_value=get_value),
		log_error=lambda *a, **k: None, get_traceback=lambda: ""), lambda: L.tk_theo_mon(doc))
	la("dòng người chọn giữ 6417", doc.items[0].expense_account, T6417)
	la("dòng không chọn theo Món 242", doc.items[1].expense_account, T242)


@ca("#526 hook tài khoản đầu phiếu dịch vụ KHÔNG đè dòng kế toán vừa chọn")
def _hook_dich_vu():
	import sys
	from vagabond import mua_dich_vu as M
	doc = _to([("R1", "", "", T6417), ("R2", "", "", T6417)], vgb_loai_chung_tu=M.LOAI_DICH_VU, vgb_tk_chi_phi=T242)
	doc.flags["vgb_tk_nguoi_chon"] = {"R1": T6417}
	doc.set_against_expense_account = lambda: None
	goi = []
	gia = SimpleNamespace(validate_account_head=lambda idx, tk, cty, loai: goi.append(idx))
	cu = sys.modules.get("erpnext.controllers.accounts_controller")
	sys.modules["erpnext.controllers.accounts_controller"] = gia
	for ten in ("erpnext", "erpnext.controllers"):
		sys.modules.setdefault(ten, SimpleNamespace())
	try:
		_voi(M, SimpleNamespace(throw=_throw, db=SimpleNamespace(get_value=lambda *a, **k: 0)),
			lambda: M.gan_tai_khoan_chi_phi(doc, "validate"))
	finally:
		if cu is None:
			sys.modules.pop("erpnext.controllers.accounts_controller", None)
		else:
			sys.modules["erpnext.controllers.accounts_controller"] = cu
	la("dòng người chọn giữ 6417", doc.items[0].expense_account, T6417)
	la("dòng kia theo đầu phiếu 242", doc.items[1].expense_account, T242)


# ------------------------------------------------------------ ghi sổ thẳng

def _chay_ghi(doc, tk, doc_sau=None, lech=False, gl=None):
	"""gl: sổ cái ERPNext sinh ra sau submit, {tài khoản: Nợ trừ Có}. Bỏ trống
	thì sổ cái Nợ đúng tài khoản trên dòng (ERPNext bình thường)."""
	from vagabond import doi_chieu_mua as DC, hach_toan_thang as H
	ghi = {"submit": 0, "rollback": 0, "commit": 0}

	def submit():
		ghi["submit"] += 1
	doc.submit = submit

	def tk_dong(d):
		return "sai" if lech else d.expense_account

	def get_value(dt, ten, truong=None, as_dict=False):
		if dt == "Purchase Invoice Item":
			if truong == "idx":
				return 1
			return next(tk_dong(d) for d in doc.items if d.name == ten)
		if dt == "Purchase Invoice":
			return doc.company
		if dt == "Item":
			return HANG_KHO.get(ten, 0)
		if dt == "Account":
			return _D(TK[ten]) if ten in TK else None
		return None

	def get_all(dt, filters=None, fields=None, **k):
		# Dòng đọc lại từ sổ sau submit.
		return [_D(name=d.name, idx=d.idx, expense_account=tk_dong(d),
			base_net_amount=d.get("base_net_amount", d.get("amount")),
			enable_deferred_expense=d.get("enable_deferred_expense", 0),
			deferred_expense_account=d.get("deferred_expense_account")) for d in doc.items]

	def sql(q, v=None, as_dict=False):
		if "tabGL Entry" in q:
			if gl is not None:
				return tuple((k, v) for k, v in gl.items())
			so = {}
			for d in doc.items:
				so[tk_dong(d)] = so.get(tk_dong(d), 0) + d.get("amount")
			return tuple(so.items())
		return ()
	fr = SimpleNamespace(
		throw=_throw, get_doc=lambda dt, n: doc, parse_json=json.loads, get_roles=lambda: ["Accounts User"],
		get_all=get_all, get_cached_value=lambda dt, ten, truong: T632,
		db=SimpleNamespace(get_value=get_value, sql=sql, commit=lambda: ghi.__setitem__("commit", ghi["commit"] + 1),
			rollback=lambda: ghi.__setitem__("rollback", ghi["rollback"] + 1)),
	)
	cu_q, cu_g = DC._kiem_quyen, DC._ghi_so_duoc
	DC._kiem_quyen = lambda: None
	DC._ghi_so_duoc = lambda: True
	cu1, cu2 = DC.frappe, H.frappe
	DC.frappe = fr
	H.frappe = fr
	try:
		try:
			return DC.ghi_so_thang(doc.name, tk), "", ghi
		except _Loi as e:
			return None, str(e), ghi
	finally:
		DC.frappe, H.frappe = cu1, cu2
		DC._kiem_quyen, DC._ghi_so_duoc = cu_q, cu_g


@ca("#526 ghi sổ thẳng tờ xăng: đi đúng tài khoản chọn, rồi mới ghi sổ")
def _ghi_xang():
	doc = _to([("R1", "", "", T632)])
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}))
	la("không lỗi", loi, "")
	la("dòng đi 6417", doc.items[0].expense_account, T6417)
	la("ghi sổ một lần", ghi["submit"], 1)
	la("chốt giao dịch", ghi["commit"], 1)


@ca("#526 ghi sổ thẳng mà không gửi tài khoản (app cũ) thì dừng, không ghi 632 im lặng")
def _ghi_khong_tk():
	doc = _to([("R1", "", "", T632)])
	kq, loi, ghi = _chay_ghi(doc, None)
	dung("báo chưa chọn tài khoản", "Chưa chọn tài khoản" in loi)
	la("không ghi sổ", ghi["submit"], 0)


@ca("#526 sau ghi sổ mà sổ khác người chọn thì huỷ giao dịch, báo lỗi, không báo xong")
def _ghi_lech():
	doc = _to([("R1", "", "", T632)])
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), lech=True)
	dung("báo lệch", "khác với chị chọn" in loi)
	la("huỷ giao dịch", ghi["rollback"], 1)
	la("không chốt", ghi["commit"], 0)


# Codex #368 finding 1 (97c0c41): bản cũ chỉ đọc lại ô tài khoản của DÒNG,
# không đọc SỔ CÁI. Một hook on_submit hay luật ghi sổ của ERPNext Nợ tài
# khoản khác mà để nguyên ô trên dòng thì bản cũ vẫn chốt. Ba ca dưới đây
# dựng đúng tình huống đó: dòng ghi 6417, sổ cái ghi khác.

@ca("#526 v1 dòng ghi 6417 mà sổ cái Nợ 632 thì huỷ giao dịch, không chốt")
def _gl_632():
	doc = _to([("R1", "", "", T632)])
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T632: 80000, "3311 - Phải trả - TV": -80000})
	dung("báo lệch sổ cái", "sổ cái" in loi)
	la("huỷ giao dịch", ghi["rollback"], 1)
	la("không chốt", ghi["commit"], 0)


@ca("#526 v1 sổ cái chỉ Nợ 6417 một phần, phần còn lại rơi vào 632, thì huỷ giao dịch")
def _gl_mot_phan():
	doc = _to([("R1", "", "", T632)])
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T6417: 50000, T632: 30000})
	dung("báo lệch sổ cái", "sổ cái" in loi)
	la("không chốt", ghi["commit"], 0)


# Hai ca trên đổ vì CẢ HAI luật cùng bắt (thiếu Nợ tài khoản chọn và 632 bị
# Nợ). Đột biến gỡ từng luật một thì không ca nào đổ (điều 17c). Hai ca dưới
# tách riêng từng luật để mỗi luật có ca giữ của mình.

@ca("#526 v1 chỉ luật 1: phần thiếu của 6417 rơi sang tài khoản khác không phải 632, vẫn huỷ")
def _gl_luat_1():
	doc = _to([("R1", "", "", T632)])
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T6417: 50000, "6427 - Chi phí khác - TV": 30000})
	dung("báo thiếu Nợ 6417", T6417 in loi and "sổ cái" in loi)
	la("không chốt", ghi["commit"], 0)


@ca("#526 v1 chỉ luật 2: 6417 đủ mà 632 bị Nợ thêm, không dòng nào mang 632, vẫn huỷ")
def _gl_luat_2():
	doc = _to([("R1", "", "", T632)])
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T6417: 80000, T632: 10000})
	dung("báo 632 bị Nợ", T632 in loi and "không dòng nào" in loi)
	la("không chốt", ghi["commit"], 0)


@ca("#526 v1 dòng chi phí trả trước: sổ cái Nợ tài khoản chờ phân bổ của dòng, không báo lệch giả")
def _gl_tra_truoc():
	doc = _to([("R1", "", "", T632)])
	doc.items[0].enable_deferred_expense = 1
	doc.items[0].deferred_expense_account = T242
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T242: 80000})
	la("không lỗi", loi, "")
	la("chốt", ghi["commit"], 1)


@ca("#526 v1 tờ có dòng nối phiếu nhập đi 632 hợp lệ: không coi 632 của dòng đó là lệch")
def _gl_632_hop_le():
	doc = _to([("R1", "", "", T632), ("R2", "NVLT00001", "PN-1", T632)])
	doc.items[1].amount = 10000
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T6417: 80000, T632: 10000})
	la("không lỗi", loi, "")
	la("chốt", ghi["commit"], 1)


# Codex #368 vòng 3 (c1674cf): tờ TRẢ HÀNG (is_return) có tiền âm, sổ cái Có
# thay vì Nợ. Luật một chiều "được Nợ ít nhất bằng" thì với -80.000 luôn đạt,
# nên Có rơi vào 632 vẫn chốt. Luật nay so CÙNG CHIỀU theo dấu.

@ca("#526 v3 tờ trả hàng: dòng chọn 6417 mà sổ cái Có vào 632 thì huỷ giao dịch")
def _gl_tra_hang_lech():
	doc = _to([("R1", "", "", T632)], is_return=1)
	doc.items[0].amount = -80000
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T632: -80000})
	dung("báo lệch sổ cái", "sổ cái" in loi)
	la("không chốt", ghi["commit"], 0)


@ca("#526 v3 tờ trả hàng, chỉ luật 1: phần Có của 6417 rơi sang tài khoản khác không phải 632, vẫn huỷ")
def _gl_tra_hang_luat_1():
	# Ca trên vi phạm cả hai luật (632 bị Có) nên gỡ riêng luật chiều âm thì
	# luật 632 vẫn đỡ (điều 17c). Ca này chỉ vi phạm luật 1.
	doc = _to([("R1", "", "", T632)], is_return=1)
	doc.items[0].amount = -80000
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={"6427 - Chi phí khác - TV": -80000})
	dung("báo thiếu Có 6417", T6417 in loi and "sổ cái" in loi)
	la("không chốt", ghi["commit"], 0)


@ca("#526 v3 tờ trả hàng đúng: sổ cái Có 6417 đủ số thì chốt, không báo lệch giả")
def _gl_tra_hang_dung():
	doc = _to([("R1", "", "", T632)], is_return=1)
	doc.items[0].amount = -80000
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T6417: -80000})
	la("không lỗi", loi, "")
	la("chốt", ghi["commit"], 1)


@ca("#526 v3 tờ trả hàng: Có đủ 6417 nhưng 632 bị Có thêm mà không dòng nào mang 632, vẫn huỷ")
def _gl_tra_hang_632():
	doc = _to([("R1", "", "", T632)], is_return=1)
	doc.items[0].amount = -80000
	kq, loi, ghi = _chay_ghi(doc, json.dumps({"R1": T6417}), gl={T6417: -80000, T632: -5000})
	dung("báo 632", T632 in loi and "không dòng nào" in loi)
	la("không chốt", ghi["commit"], 0)


# ------------------------------------------------------------ hoá đơn đến sau

@ca("#526 hồ sơ thành hợp lệ khi MỌI khoản đều chờ hoá đơn và đã nối đủ")
def _nen_hop_le():
	from vagabond.ho_so_bo_sung import nen_hop_le
	a = _D(cho_hoa_don=1, hoa_don_bo_sung="HDM-1")
	b = _D(cho_hoa_don=1, hoa_don_bo_sung="")
	c = _D(cho_hoa_don=0, hoa_don_bo_sung="")
	la("nối đủ", nen_hop_le([a]), True)
	la("còn khoản chưa nối", nen_hop_le([a, b]), False)
	la("có khoản không hoá đơn thật", nen_hop_le([a, c]), False)
	la("hồ sơ rỗng", nen_hop_le([]), False)


@ca("#526 chỉ nối tờ còn nháp, không nối tờ đã ghi sổ, đã huỷ, hay đã nằm ở hồ sơ khác")
def _loi_noi():
	from vagabond.ho_so_bo_sung import loi_noi_hoa_don
	la("nháp nối được", loi_noi_hoa_don(0, ""), "")
	dung("đã ghi sổ", "hai lần" in loi_noi_hoa_don(1, ""))
	dung("đã huỷ", "huỷ" in loi_noi_hoa_don(2, ""))
	dung("hồ sơ khác", "APP-9" in loi_noi_hoa_don(0, "APP-9"))


def _noi(loai, dong, cp="Chi phi khong hop le"):
	from unittest.mock import Mock, patch
	import frappe
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs
	d = SimpleNamespace(dong=dong, save=Mock(), add_comment=Mock(), loai=loai, loai_cp_thue=cp)
	with patch.object(frappe, "db", SimpleNamespace(sql=Mock())), \
		patch.object(frappe, "get_doc", return_value=d), patch.object(hs, "_kiem"):
		kq = bo.noi_hoa_don("APP-THU", 1, "PI-THU")
	return d, kq


@ca("#526 nối đủ hoá đơn cho hồ sơ chi từ TK công ty thì chuyển Hợp lệ tính thuế")
def _noi_hop_le():
	r = _D(cho_hoa_don=1, hoa_don_bo_sung="")
	d, kq = _noi("TK cong ty", [r])
	la("chuyển hợp lệ", d.loai_cp_thue, "Chi phi hop le")
	la("báo màn", kq["hop_le"], 1)
	la("lưu một lần", d.save.call_count, 1)


@ca("#526 còn khoản không hoá đơn thật thì nối xong vẫn giữ Không hợp lệ")
def _noi_giu():
	r1 = _D(cho_hoa_don=1, hoa_don_bo_sung="")
	r2 = _D(cho_hoa_don=0, hoa_don_bo_sung="")
	d, kq = _noi("TK cong ty", [r1, r2])
	la("giữ không hợp lệ", d.loai_cp_thue, "Chi phi khong hop le")
	la("không báo hợp lệ", kq["hop_le"], 0)


@ca("#526 hồ sơ loại khác (công nợ NCC) nối hoá đơn bổ sung không bị đổi loại chi phí thuế")
def _noi_loai_khac():
	r = _D(cho_hoa_don=1, hoa_don_bo_sung="")
	d, kq = _noi("NCC", [r], cp="")
	la("không đổi", d.loai_cp_thue, "")


@ca("#526 tờ hoá đơn đã nối làm hoá đơn đến sau thì chặn ghi sổ, gọi tên hồ sơ")
def _chan_ghi():
	from vagabond import ho_so_bo_sung as bo
	cu = bo.ho_so_dang_giu
	cu_fr = bo.frappe
	bo.frappe = SimpleNamespace(throw=_throw)
	try:
		bo.frappe = SimpleNamespace(throw=_throw, db=SimpleNamespace(sql=lambda *a, **k: (), has_column=lambda dt, cot: True))
		bo.ho_so_dang_giu = lambda ten, bo_qua_dong=None, **k: "APP-26-09-100"
		try:
			bo.chan_ghi_so_hd_da_chi(_D(name="HDM-1"))
			loi = ""
		except _Loi as e:
			loi = str(e)
		dung("chặn và gọi tên hồ sơ", "APP-26-09-100" in loi and "không ghi sổ" in loi)
		bo.ho_so_dang_giu = lambda ten, bo_qua_dong=None, **k: ""
		bo.chan_ghi_so_hd_da_chi(_D(name="HDM-2"))
	finally:
		bo.ho_so_dang_giu = cu
		bo.frappe = cu_fr


# Codex #368 finding 2 (97c0c41): nối và ghi sổ đua nhau. Frappe chạy
# REPEATABLE READ: câu select thường đọc ẢNH CHỤP lúc giao dịch mở, không thấy
# dấu nối hay lần ghi sổ mà giao dịch kia vừa chốt. Chỉ câu đọc có khoá
# (for update) mới đọc bản hiện hành. Lớp dữ liệu giả dưới đây mô phỏng đúng
# điều đó: select thường trả ảnh chụp cũ, select có khoá trả bản hiện hành.
# Tái hiện trên MariaDB thật (hai kết nối) ghi trong comment bàn giao v1.

def _db_hai_mat(docstatus_hien_hanh=0, giu_hien_hanh="", huy_hien_hanh=0):
	"""db.sql: ảnh chụp cũ nói tờ nháp, chưa ai nối; bản hiện hành theo tham số.
	Ghi lại thứ tự câu hỏi để kiểm khoá tờ trước rồi mới đọc dấu nối."""
	so = []

	def sql(q, v=None, as_dict=False):
		khoa = "for update" in q.lower()
		if "`tabPurchase Invoice`" in q:
			so.append(("hd", khoa))
			return ((docstatus_hien_hanh, huy_hien_hanh) if khoa else (0, 0),)
		if "tabVagabond Ho So TT Dong" in q:
			so.append(("noi", khoa))
			return ((giu_hien_hanh,),) if (khoa and giu_hien_hanh) else ()
		return ()
	return sql, so


def _db(sql):
	return SimpleNamespace(sql=sql, has_column=lambda dt, cot: True)


def _kiem_noi(sql, hd_huy=0, loai="TK cong ty"):
	"""Chạy THẬT kiem_bo_sung trên hồ sơ nối khoản 1 vào tờ HDM-X."""
	from unittest.mock import patch
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs
	dong = _D(name="D1", idx=1, hoa_don_bo_sung="HDM-X", cho_hoa_don=1, hoa_don="")
	ho_so = SimpleNamespace(dong=[dong], nha_cung_cap="XDKV2", trang_thai="Da thanh toan", loai=loai,
		get_doc_before_save=lambda: None)
	hd_anh_chup = _D(name="HDM-X", docstatus=0, supplier="XDKV2", company=CTY, vgb_huy=hd_huy)
	fr = SimpleNamespace(throw=_throw, get_doc=lambda dt, n: hd_anh_chup, db=_db(sql))
	with patch.object(hs, "_kiem"), patch.object(hs, "_cong_ty_chung_tu", return_value=CTY):
		try:
			_voi(bo, fr, lambda: bo.kiem_bo_sung(ho_so))
			return ""
		except _Loi as e:
			return str(e)


@ca("#526 v1 nối khi tờ vừa được người khác ghi sổ (ảnh chụp còn nháp): đọc bản hiện hành, chặn")
def _dua_ghi_so_truoc():
	sql, so = _db_hai_mat(docstatus_hien_hanh=1)
	loi = _kiem_noi(sql)
	dung("chặn vì đã ghi sổ", "đã ghi sổ" in loi)
	dung("đọc tờ bằng câu có khoá", ("hd", True) in so)


@ca("#526 v1 nối khi hồ sơ khác vừa nối cùng tờ (ảnh chụp chưa thấy): đọc dấu nối hiện hành, chặn")
def _dua_hai_ho_so():
	sql, so = _db_hai_mat(giu_hien_hanh="APP-B")
	loi = _kiem_noi(sql)
	dung("chặn, gọi tên hồ sơ kia", "APP-B" in loi)
	dung("khoá tờ TRƯỚC khi đọc dấu nối", so and so[0] == ("hd", True) and ("noi", True) in so)


@ca("#526 v1 ghi sổ khi hồ sơ vừa nối tờ này (ảnh chụp chưa thấy): before_submit đọc hiện hành, chặn")
def _dua_noi_truoc():
	from vagabond import ho_so_bo_sung as bo
	sql, so = _db_hai_mat(giu_hien_hanh="APP-A")
	try:
		_voi(bo, SimpleNamespace(throw=_throw, db=_db(sql)),
			lambda: bo.chan_ghi_so_hd_da_chi(_D(name="HDM-X")))
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("chặn, gọi tên hồ sơ", "APP-A" in loi)
	dung("khoá tờ TRƯỚC khi đọc dấu nối", so and so[0] == ("hd", True) and ("noi", True) in so)


# Codex #368 vòng 2 (dd47991): tờ hoá đơn nháp đã ĐÁNH DẤU HUỶ (huỷ mềm của
# chung_tu.danh_dau_huy) vẫn là docstatus 0, chỉ có vgb_huy 1. Bản dd47991 chỉ
# xét docstatus nên nhận nối tờ đó, và noi_hoa_don đổi hồ sơ sang hợp lệ tính
# thuế bằng một chứng từ đã bỏ.

@ca("#526 v2 không nối tờ nháp đã đánh dấu huỷ, kể cả khi ảnh chụp chưa thấy dấu huỷ")
def _noi_to_huy():
	from vagabond.ho_so_bo_sung import loi_noi_hoa_don
	dung("luật thuần gọi tên dấu huỷ", "đánh dấu huỷ" in loi_noi_hoa_don(0, "", 1))
	sql, so = _db_hai_mat(huy_hien_hanh=1)
	loi = _kiem_noi(sql, hd_huy=1)
	dung("chặn tờ đã huỷ mềm", "đánh dấu huỷ" in loi)
	sql, so = _db_hai_mat(huy_hien_hanh=1)
	loi = _kiem_noi(sql, hd_huy=0)
	dung("dấu huỷ vừa chốt ở giao dịch khác cũng chặn", "đánh dấu huỷ" in loi)


@ca("#526 v2 danh sách chọn hoá đơn và nút nối trên Desk bỏ qua tờ đã đánh dấu huỷ")
def _chon_bo_to_huy():
	from unittest.mock import patch
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs
	loc = {}

	def get_list(dt, filters=None, **k):
		loc.update(filters or {})
		return []
	fr = SimpleNamespace(throw=_throw, get_list=get_list,
		get_doc=lambda dt, n: SimpleNamespace(nha_cung_cap="XDKV2"),
		db=SimpleNamespace(has_column=lambda dt, cot: True,
			get_value=lambda dt, n, f, as_dict=False: _D(name="HDM-X", supplier="XDKV2", company=CTY, docstatus=0, vgb_huy=1),
			# Có sẵn một khoản chờ hoá đơn đúng NCC: nút nối sẽ đưa ra nếu
			# không xét dấu huỷ (ca đầu tiên không có dòng này nên đột biến
			# bỏ xét dấu huỷ không làm ca đổ, điều 17a).
			sql=lambda q, *a, **k: [_D(ho_so="APP-1", ngay="2026-09-20", trang_thai="Da thanh toan", dong=1,
				noi_dung="Xăng", so_tien=80000, ngay_hd="")] if "p.nha_cung_cap" in q else ()))
	with patch.object(hs, "_kiem"), patch.object(hs, "_cong_ty_chung_tu", return_value=CTY):
		_voi(bo, fr, lambda: bo.danh_sach_hoa_don("APP-1"))
		kq = _voi(bo, fr, lambda: bo.khoan_cho_hoa_don("HDM-X"))
	la("danh sách lọc bỏ tờ huỷ", loc.get("vgb_huy"), 0)
	la("nút nối không đưa khoản nào cho tờ huỷ", kq.get("khoan"), [])


@ca("#526 v2 không đánh dấu huỷ tờ đang là hoá đơn đến sau của một hồ sơ; tờ chưa nối thì huỷ bình thường")
def _huy_to_da_noi():
	from vagabond import chung_tu as C, ho_so_bo_sung as bo
	ghi = []
	sql, so = _db_hai_mat(giu_hien_hanh="APP-A")
	fr_bo = SimpleNamespace(throw=_throw, db=_db(sql))
	fr_c = SimpleNamespace(throw=_throw, session=SimpleNamespace(user="dung@x"),
		db=SimpleNamespace(set_value=lambda *a, **k: ghi.append(a[1]), commit=lambda: None))
	cu_bo, cu_c = bo.frappe, C.frappe
	import vagabond.bao_ve_hddt as B
	cu_bv = B.chan_huy
	B.chan_huy = lambda doc: None
	bo.frappe, C.frappe = fr_bo, fr_c
	try:
		try:
			C.danh_dau_huy(_D(doctype="Purchase Invoice", name="HDM-X", docstatus=0), "nhập trùng", ghi_vet=False)
			loi = ""
		except _Loi as e:
			loi = str(e)
		dung("chặn, gọi tên hồ sơ", "APP-A" in loi)
		la("không ghi dấu huỷ", ghi, [])
		sql2, so2 = _db_hai_mat()
		bo.frappe = SimpleNamespace(throw=_throw, db=_db(sql2))
		C.danh_dau_huy(_D(doctype="Purchase Invoice", name="HDM-Y", docstatus=0), "nhập trùng", ghi_vet=False)
		la("tờ chưa nối huỷ được", ghi, ["HDM-Y"])
	finally:
		B.chan_huy = cu_bv
		bo.frappe, C.frappe = cu_bo, cu_c


# Codex #368 vòng 3 (c1674cf): danh_dau_huy xét docstatus trên doc đã nạp từ
# trước. Một giao dịch ghi sổ chen vào thì khoá tờ trả docstatus 1 hiện hành
# nhưng chan_huy_hd_da_noi bỏ qua kết quả đó, và tờ ĐÃ GHI SỔ bị gắn dấu huỷ
# mà sổ cái không đảo.

@ca("#526 v3 huỷ mềm khi tờ vừa bị người khác ghi sổ (doc đã nạp còn nháp): đọc hiện hành, chặn, không gắn dấu huỷ")
def _huy_to_vua_ghi_so():
	from vagabond import chung_tu as C, ho_so_bo_sung as bo
	import vagabond.bao_ve_hddt as B
	ghi = []
	sql, so = _db_hai_mat(docstatus_hien_hanh=1)
	cu_bo, cu_c, cu_bv = bo.frappe, C.frappe, B.chan_huy
	B.chan_huy = lambda doc: None
	bo.frappe = SimpleNamespace(throw=_throw, db=_db(sql))
	C.frappe = SimpleNamespace(throw=_throw, session=SimpleNamespace(user="dung@x"),
		db=SimpleNamespace(set_value=lambda *a, **k: ghi.append(a[1]), commit=lambda: None))
	try:
		try:
			C.danh_dau_huy(_D(doctype="Purchase Invoice", name="HDM-Z", docstatus=0), "nhập trùng", ghi_vet=False)
			loi = ""
		except _Loi as e:
			loi = str(e)
	finally:
		B.chan_huy = cu_bv
		bo.frappe, C.frappe = cu_bo, cu_c
	dung("chặn vì đã ghi sổ", "đã ghi sổ" in loi)
	la("không gắn dấu huỷ", ghi, [])
	dung("đọc tờ bằng câu có khoá", ("hd", True) in so)


# Codex #368 vòng 4 (a38b6e5): hồ sơ bị TỪ CHỐI vẫn sống lại được (gui_fin
# nhận cả Tu choi), nên không được coi là hết hiệu lực. Bản a38b6e5 coi Tu choi
# như Huy: tờ đang nối vào hồ sơ bị trả lại thì ghi sổ được và nối được sang hồ
# sơ khác, rồi hồ sơ cũ gửi lại vẫn giữ dấu nối, chi phí hai lần. Lớp dữ liệu
# giả dưới đây LỌC THẬT theo bộ trạng thái hết hiệu lực mà code truyền vào.

def _db_theo_trang_thai(giu, docstatus=0):
	"""giu: [(hồ sơ, trạng thái)] hoặc [(hồ sơ, trạng thái, loại)] đang nối tờ
	HDM-X. sql áp ĐÚNG tham số mà câu hỏi truyền vào: bộ trạng thái hết hiệu
	lực, và cờ "chỉ hồ sơ Chi từ TK công ty" kèm tên loại."""
	TKCT = "TK cong ty"
	dong = [(g[0], g[1], g[2] if len(g) > 2 else TKCT) for g in giu]

	def sql(q, v=None, as_dict=False):
		if "`tabPurchase Invoice`" in q:
			return ((docstatus, 0),)
		if "tabVagabond Ho So TT Dong" in q:
			v = tuple(v or ())
			het = next((x for x in v if isinstance(x, tuple) and x and x[0] in ("Huy", "Tu choi")), ())
			if "d.hoa_don_bo_sung in" in q:
				# _ho_so_chi_theo_hd: có mệnh đề "p.loai = %s" thì lọc theo tham số thứ hai.
				chi = "p.loai = %s" in q
				return tuple(("HDM-X", hs) for hs, tt, lo in dong if tt not in het and (not chi or lo == v[1]))
			# ho_so_dang_giu: (tờ, bỏ qua dòng, hết hiệu lực, cờ chỉ TKCT, tên loại)
			chi = "p.loai = %s" in q and len(v) > 4 and v[3]
			return tuple((hs,) for hs, tt, lo in dong if tt not in het and (not chi or lo == v[4]))[:1]
		return ()
	return sql


@ca("#526 v4 hồ sơ bị trả lại (Từ chối) vẫn giữ tờ đã nối: chặn ghi sổ, chặn nối sang hồ sơ khác, màn Đối chiếu vẫn xếp Xong")
def _tu_choi_van_giu():
	from vagabond import ho_so_bo_sung as bo, doi_chieu_mua as DC
	sql = _db_theo_trang_thai([("APP-TC", "Tu choi")])
	try:
		_voi(bo, SimpleNamespace(throw=_throw, db=_db(sql)), lambda: bo.chan_ghi_so_hd_da_chi(_D(name="HDM-X")))
		loi = ""
	except _Loi as e:
		loi = str(e)
	dung("chặn ghi sổ, gọi tên hồ sơ bị trả lại", "APP-TC" in loi)
	loi = _kiem_noi(sql)
	dung("chặn nối sang hồ sơ khác", "APP-TC" in loi)
	la("màn Đối chiếu biết tờ thuộc hồ sơ", _voi(DC, SimpleNamespace(db=_db(sql)), lambda: DC._ho_so_chi_theo_hd(["HDM-X"])), {"HDM-X": "APP-TC"})
	sql = _db_theo_trang_thai([("APP-H", "Huy")])
	_voi(bo, SimpleNamespace(throw=_throw, db=_db(sql)), lambda: bo.chan_ghi_so_hd_da_chi(_D(name="HDM-X")))


@ca("#526 v4 nút nối trên Desk không đưa khoản của hồ sơ bị trả lại (hồ sơ đó không nhận nối thêm)")
def _desk_bo_tu_choi():
	from unittest.mock import patch
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs
	khoan = [("APP-TC", "Tu choi", "TK cong ty"), ("APP-OK", "Da thanh toan", "TK cong ty"),
		("APP-NCC", "Da thanh toan", "NCC")]

	def sql(q, v=None, *a, **k):
		if "p.nha_cung_cap" in q:
			chi = "p.loai = %s" in q
			return [_D(ho_so=x, ngay="2026-09-20", trang_thai=tt, dong=1, noi_dung="Xăng", so_tien=80000, ngay_hd="")
				for x, tt, lo in khoan if tt not in v[-1] and (not chi or lo == v[1])]
		return ()
	fr = SimpleNamespace(throw=_throw, db=SimpleNamespace(has_column=lambda dt, cot: True, sql=sql,
		get_value=lambda dt, n, f, as_dict=False: _D(name="HDM-X", supplier="XDKV2", company=CTY, docstatus=0, vgb_huy=0)))
	with patch.object(hs, "_kiem"), patch.object(hs, "_cong_ty_chung_tu", return_value=CTY):
		kq = _voi(bo, fr, lambda: bo.khoan_cho_hoa_don("HDM-X"))
	la("chỉ khoản của hồ sơ Chi từ TK công ty còn nhận nối", [x["ho_so"] for x in kq.get("khoan")], ["APP-OK"])


# Bench v526 (bd6849d) bắt được: luật "chỉ nối tờ nháp" và "tờ đã nối không
# ghi sổ" là của hồ sơ Chi từ TK công ty (chi phí đã ghi qua bút toán của hồ
# sơ). Áp chung cho mọi loại thì làm hỏng luồng hồ sơ trả NCC, vốn nối tờ ĐÃ
# ghi sổ (tờ tạo công nợ mà hồ sơ trả) - ca tích hợp #263 đổ vì đúng lẽ đó.

@ca("#526 v5 hồ sơ trả NCC: nối tờ đã ghi sổ vẫn được như trước v526, tờ nháp nối vào vẫn ghi sổ được")
def _ncc_giu_luong_cu():
	from vagabond import ho_so_bo_sung as bo, doi_chieu_mua as DC
	la("luật thuần: NCC nhận tờ đã ghi sổ", bo.loi_noi_hoa_don(1, "", 0, chi_nhap=False), "")
	dung("luật thuần: TKCT vẫn chặn tờ đã ghi sổ", "đã ghi sổ" in bo.loi_noi_hoa_don(1, "", 0, chi_nhap=True))
	la("nối tờ đã ghi sổ vào hồ sơ NCC", _kiem_noi(_db_theo_trang_thai([], docstatus=1), loai="NCC"), "")
	dung("nối tờ đã ghi sổ vào hồ sơ TKCT vẫn chặn", "đã ghi sổ" in _kiem_noi(_db_theo_trang_thai([], docstatus=1)))
	sql = _db_theo_trang_thai([("APP-NCC", "Da duyet", "NCC")])
	_voi(bo, SimpleNamespace(throw=_throw, db=_db(sql)), lambda: bo.chan_ghi_so_hd_da_chi(_D(name="HDM-X")))
	la("màn Đối chiếu không xếp tờ của hồ sơ NCC vào Xong",
		_voi(DC, SimpleNamespace(db=_db(sql)), lambda: DC._ho_so_chi_theo_hd(["HDM-X"])), {})
	dung("một tờ vẫn chỉ nằm ở một hồ sơ, kể cả hồ sơ NCC đang giữ", "APP-NCC" in _kiem_noi(sql))


@ca("#526 v5 danh sách chọn hoá đơn: hồ sơ TKCT chỉ tờ nháp, hồ sơ NCC gồm cả tờ đã ghi sổ")
def _chon_theo_loai():
	from unittest.mock import patch
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs
	for loai, mong in (("TK cong ty", 0), ("NCC", ["<", 2])):
		loc = {}

		def get_list(dt, filters=None, **k):
			loc.update(filters or {})
			return []
		fr = SimpleNamespace(throw=_throw, get_list=get_list,
			get_doc=lambda dt, n: SimpleNamespace(nha_cung_cap="XDKV2", loai=loai),
			db=SimpleNamespace(has_column=lambda dt, cot: True))
		with patch.object(hs, "_kiem"), patch.object(hs, "_cong_ty_chung_tu", return_value=CTY):
			_voi(bo, fr, lambda: bo.danh_sach_hoa_don("APP-1"))
		la("lọc trạng thái tờ cho hồ sơ " + loai, loc.get("docstatus"), mong)


# Codex #368 vòng 4: màn hạch toán phải có ảnh món cạnh tên (AGENTS.md mục
# ảnh món), chip "chứng từ của hồ sơ" phải gọn (mục 18).

@ca("#526 v4 màn hạch toán trả ảnh món của từng dòng; dòng không mã thì rỗng để app hiện ô 🍰")
def _anh_dong():
	from vagabond import hach_toan_thang as H
	anh = {"NVLT00001": "/files/bot-mi.jpg"}

	def get_value(dt, ten, truong=None, as_dict=False):
		if dt == "Item" and truong == "image":
			return anh.get(ten)
		if dt == "Item":
			return HANG_KHO.get(ten, 0)
		if dt == "Item Default":
			return None
		return None
	fr = SimpleNamespace(throw=_throw, get_cached_value=lambda *a: T632,
		db=SimpleNamespace(get_value=get_value, sql=lambda *a, **k: []))
	doc = _to([("R1", "", "", T632), ("R2", "NVLT00001", "PN-1", "2331 - Hàng chờ - TV")])
	dong = _voi(H, fr, lambda: H.dong_hach_toan(doc))
	la("ảnh từng dòng", [d.get("anh") for d in dong], ["", "/files/bot-mi.jpg"])


# Codex #368 vòng 5 (bd6849d).
# (1) Tờ đã nối là tờ NHÁP, vẫn sửa được trên Desk. Chặn chỉ ở before_submit
#     nên đổi nhà cung cấp hay công ty sau khi nối là lọt luật "đúng NCC, đúng
#     công ty" của kiem_bo_sung, hồ sơ vẫn Hợp lệ tính thuế.
# (2) Màn chi tiết Đối chiếu gọi dcmChip mà không truyền ho_so_chi, nên tờ
#     nháp đã nối (nhom "xong") hiện chip xanh "Đã ghi sổ" sai sự thật.

def _hd_sua(truoc, sau, giu="APP-A"):
	"""Chạy THẬT giu_hd_da_noi: tờ nháp đã lưu, bản trước và bản đang lưu."""
	from vagabond import ho_so_bo_sung as bo
	sql = _db_hai_mat(giu_hien_hanh=giu)[0]
	cu = _D(name="HDM-X", docstatus=0, **truoc)
	doc = _D(name="HDM-X", docstatus=0, **sau)
	doc["get_doc_before_save"] = lambda: cu
	doc["is_new"] = lambda: False
	try:
		_voi(bo, SimpleNamespace(throw=_throw, db=_db(sql)), lambda: bo.giu_hd_da_noi(doc))
		return ""
	except _Loi as e:
		return str(e)


@ca("#526 v5 tờ đã nối: đổi nhà cung cấp hay công ty khi lưu nháp thì chặn, gọi tên hồ sơ")
def _khoa_ncc_cong_ty():
	loi = _hd_sua({"supplier": "XDKV2", "company": CTY}, {"supplier": "NCC-KHAC", "company": CTY})
	dung("chặn đổi NCC", "APP-A" in loi)
	loi = _hd_sua({"supplier": "XDKV2", "company": CTY}, {"supplier": "XDKV2", "company": "The Vagabond (Demo)"})
	dung("chặn đổi công ty", "APP-A" in loi)
	la("sửa chỗ khác thì lưu bình thường", _hd_sua({"supplier": "XDKV2", "company": CTY}, {"supplier": "XDKV2", "company": CTY}), "")
	la("tờ chưa nối đổi NCC thoải mái", _hd_sua({"supplier": "XDKV2", "company": CTY}, {"supplier": "NCC-KHAC", "company": CTY}, giu=""), "")


@ca("#526 v5 hook giữ tờ đã nối đăng ký ở validate của Hoá đơn mua (mọi lần lưu nháp, mọi đường)")
def _hook_giu():
	from vagabond import hooks
	la("có trong validate", "vagabond.ho_so_bo_sung.giu_hd_da_noi" in hooks.doc_events["Purchase Invoice"]["validate"], True)


@ca("#526 v5 màn chi tiết Đối chiếu của tờ nháp đã nối: chip hồ sơ, KHÔNG hiện Đã ghi sổ")
def _chip_chi_tiet():
	from vagabond.khung.kiem_thu.thu_doi_chieu_252 import _ve_man, _xem_mau, _so_sanh_mau
	ra = _ve_man(_xem_mau(nhom="xong", ho_so_chi="APP-26-09-00123", goi_y=[]), _so_sanh_mau([]))
	dung("không có chip Đã ghi sổ", "Đã ghi sổ" not in ra["khung"])
	dung("có chip hồ sơ", "Hồ sơ · 0123" in ra["khung"])


# ------------------------------------------------------------ quyền Repost

@ca("#526 quyền Repost chỉ mở cho đúng vai kế toán FIN, đủ bốn quyền để đổi tài khoản tờ đã ghi sổ")
def _quyen():
	from vagabond import quyen_ap
	can = quyen_ap.can_cap_them()
	la("đúng bốn dòng", sorted(can), sorted([
		("Repost Accounting Ledger", "AP Kiểm soát (FIN)", q) for q in ("read", "write", "create", "submit")]))
	dung("không mở cho Accounts User", all(v != "Accounts User" for _, v, _ in can))
	# Bảng Purchase Order của luồng duyệt giữ nguyên sáu dòng.
	la("bảng cũ giữ nguyên", len(quyen_ap.can_cap()), 6)


@ca("#526 patch cấp quyền Repost: cấp rồi mà vẫn thiếu thì làm hỏng migrate, không báo xong giả")
def _quyen_nem():
	from vagabond import quyen_ap as Q
	import sys
	goi = []
	sys.modules["frappe.permissions"] = SimpleNamespace(
		add_permission=lambda dt, vai, lv: goi.append(("add", dt, vai)),
		update_permission_property=lambda dt, vai, lv, q, v: goi.append(("set", q)))
	cu_thieu = Q._thieu
	Q._thieu = lambda dt, vai, q: True
	try:
		try:
			_voi(Q, SimpleNamespace(throw=_throw, clear_cache=lambda: None,
				db=SimpleNamespace(exists=lambda dt, ten: True)), Q.cap_repost_v526)
			loi = ""
		except _Loi as e:
			loi = str(e)
	finally:
		Q._thieu = cu_thieu
		sys.modules.pop("frappe.permissions", None)
	dung("báo thiếu", "chưa đủ" in loi)
	dung("đã đi qua add_permission của Frappe", ("add", "Repost Accounting Ledger", "AP Kiểm soát (FIN)") in goi)

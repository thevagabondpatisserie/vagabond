"""v552: chị Dung 02/10/2026 trên khoản trả trước khi lên ERP (PKT-2026-00067):
"cho c Nợ 331 / 112 luôn ... thêm giúp chị số hiệu kế toán vào, và cho quyền
chỉnh sửa luôn". Ba việc: màn Bút toán hiện số hiệu tài khoản, kế toán đổi
được tài khoản dòng không gắn công nợ trên bút toán nháp, vế Có mặc định
11211 MB Bank. Thêm: ghi sổ ở màn Bút toán cho loại bút toán này phải đi qua
đường duyệt có khóa và kiểm dư sống (Codex #403), không ghi thẳng.
"""
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, la, dung, Doi
from vagabond import but_toan as bt
from vagabond import cong_no_ncc as cn


@ca("v552 nhãn tài khoản có số hiệu: 331 - Phải trả cho người bán")
def _nhan():
	la("ghép số hiệu", bt.nhan_tk("331", "Phải trả cho người bán"), "331 - Phải trả cho người bán")
	la("MB Bank", bt.nhan_tk("11211", "Tiền gửi MB Bank 31561568"), "11211 - Tiền gửi MB Bank 31561568")
	la("tài khoản không số hiệu giữ tên", bt.nhan_tk(None, "Temporary Opening"), "Temporary Opening")
	la("tên đã có số hiệu không ghép hai lần", bt.nhan_tk("331", "331 Phải trả"), "331 Phải trả")
	la("thiếu tên dùng số hiệu", bt.nhan_tk("331", ""), "331")


@ca("v552 chỉ dòng không gắn NCC/khách/hoá đơn mới đổi tài khoản được")
def _doi_duoc():
	dung("vế Có ngân hàng đổi được", bt.dong_doi_duoc({"account": "Temporary Opening - TV"}))
	dung("vế Nợ 331 gắn NCC và hoá đơn không đổi", not bt.dong_doi_duoc(
		{"account": "331 - TV", "party_type": "Supplier", "party": "NCC", "reference_type": "Purchase Invoice",
		 "reference_name": "PI-1"}))
	dung("dòng chỉ gắn chứng từ cũng không đổi", not bt.dong_doi_duoc({"reference_name": "PI-1"}))
	dung("đọc được cả dòng dạng đối tượng", bt.dong_doi_duoc(types.SimpleNamespace(party=None, party_type=None,
		reference_type=None, reference_name=None)))


def tk(**doi):
	x = {"name": "11211 - Tiền gửi MB Bank 31561568 - TV", "company": "TV", "is_group": 0, "disabled": 0,
		"account_type": "Bank", "account_currency": "VND"}
	x.update(doi)
	return x


@ca("v552 tài khoản mới phải chi tiết, đúng công ty, đang dùng, không phải công nợ, đúng tiền tệ")
def _kiem_tk():
	la("MB Bank hợp lệ", bt.kiem_tk_moi(tk(), "TV", "VND"), None)
	dung("không thấy", bt.kiem_tk_moi(None, "TV"))
	dung("khác công ty", bt.kiem_tk_moi(tk(company="TVD"), "TV"))
	dung("tài khoản nhóm", bt.kiem_tk_moi(tk(is_group=1), "TV"))
	dung("đã ngừng", bt.kiem_tk_moi(tk(disabled=1), "TV"))
	dung("tài khoản phải trả", bt.kiem_tk_moi(tk(account_type="Payable"), "TV"))
	dung("tài khoản phải thu", bt.kiem_tk_moi(tk(account_type="Receivable"), "TV"))
	dung("lệch tiền tệ", bt.kiem_tk_moi(tk(account_currency="USD"), "TV", "VND"))


class _Dong(types.SimpleNamespace):
	pass


def _je(docstatus=0):
	no = _Dong(name="r1", idx=1, account="331 - Phải trả cho người bán - TV", party_type="Supplier", party="NCC",
		reference_type="Purchase Invoice", reference_name="PI-1", account_currency="VND")
	co = _Dong(name="r2", idx=2, account="Temporary Opening - TV", party_type=None, party=None,
		reference_type=None, reference_name=None, account_currency="VND")
	ghi = {"luu": 0, "nhan_xet": []}
	je = types.SimpleNamespace(name="PKT-2026-00067", docstatus=docstatus, company="TV", accounts=[no, co],
		flags=types.SimpleNamespace(), user_remark="[Trả trước khi lên ERP] Cấn hóa đơn PI-1")
	je.save = lambda **k: ghi.__setitem__("luu", ghi["luu"] + 1)
	je.add_comment = lambda loai, nd: ghi["nhan_xet"].append(nd)
	return je, ghi


def _goi(je, ma_dong, tk_moi, vai=("AP Kiểm soát (FIN)",)):
	f = bt.frappe
	with patch.object(f, "get_roles", lambda *a, **k: list(vai)), \
			patch.object(f, "get_doc", lambda *a, **k: je), \
			patch.object(f.db, "get_value", lambda *a, **k: Doi(tk_moi) if tk_moi else None):
		try:
			return bt.doi_tai_khoan(je.name, ma_dong, (tk_moi or {}).get("name", "X")), None
		except Exception as e:
			return None, str(e)


@ca("v552 đổi vế Có tạm thành 11211 MB Bank trên bút toán nháp, giữ số tiền và vế Nợ 331")
def _doi_that():
	je, ghi = _je()
	kq, loi = _goi(je, "r2", tk())
	la("không lỗi", loi, None)
	la("vế Có đổi sang MB Bank", je.accounts[1].account, "11211 - Tiền gửi MB Bank 31561568 - TV")
	la("vế Nợ giữ nguyên 331", je.accounts[0].account, "331 - Phải trả cho người bán - TV")
	la("lưu đúng một lần", ghi["luu"], 1)
	dung("có dấu vết ai đổi gì", ghi["nhan_xet"] and "Temporary Opening - TV" in ghi["nhan_xet"][0])


@ca("v552 đổi tài khoản bị chặn: dòng 331, bút toán đã ghi sổ, không quyền ghi sổ, tài khoản công nợ")
def _doi_chan():
	je, ghi = _je()
	_, loi = _goi(je, "r1", tk())
	dung("dòng 331 gắn NCC/hoá đơn bị chặn", loi and "không đổi tài khoản" in loi)
	la("dòng 331 không đổi", je.accounts[0].account, "331 - Phải trả cho người bán - TV")
	je2, ghi2 = _je(docstatus=1)
	_, loi = _goi(je2, "r2", tk())
	dung("đã ghi sổ bị chặn", loi and "nháp" in loi)
	je3, ghi3 = _je()
	_, loi = _goi(je3, "r2", tk(), vai=("Accounts User",))
	dung("Accounts User không có quyền ghi sổ thì không sửa được", loi and "quyền" in loi)
	je4, ghi4 = _je()
	_, loi = _goi(je4, "r2", tk(account_type="Payable"))
	dung("đổi sang tài khoản công nợ bị chặn", loi and "công nợ" in loi)
	la("không lần lưu nào khi bị chặn", ghi["luu"] + ghi2["luu"] + ghi3["luu"] + ghi4["luu"], 0)
	je5, _ = _je()
	_, loi = _goi(je5, "r9", tk())
	dung("dòng không tồn tại", loi and "Không thấy dòng" in loi)


@ca("v552 chị Dung (Accounts Manager + AP Kiểm soát FIN) có quyền đổi và ghi sổ")
def _quyen_dung():
	vai = {"Accounts Manager", "Accounts User", "AP Kiểm soát (FIN)", "Stock Manager"}
	dung("có quyền ghi sổ, sửa", bool(bt.QUYEN_GHI & vai))
	je, _ = _je()
	_, loi = _goi(je, "r2", tk(), vai=tuple(vai))
	la("đổi được", loi, None)


@ca("v552 Ghi sổ ở màn Bút toán với khoản trả trước ERP đi qua đường duyệt có kiểm dư sống")
def _ghi_qua_duyet():
	je, _ = _je()
	da_nop = []
	je.submit = lambda: da_nop.append(1)
	goi = []
	f = bt.frappe
	with patch.object(f, "get_roles", lambda *a, **k: ["AP Kiểm soát (FIN)"]), \
			patch.object(f, "get_doc", lambda *a, **k: je), \
			patch.object(cn, "duyet_truoc_erp", lambda ten: goi.append(ten) or {"je": ten}):
		kq = bt.ghi_so(je.name)
	la("gọi đường duyệt đúng bút toán", goi, ["PKT-2026-00067"])
	la("không ghi thẳng", da_nop, [])
	dung("báo đã ghi sổ", "Đã ghi sổ" in kq["loi_nhan"])
	# Bút toán tay thường vẫn ghi thẳng.
	je2, _ = _je()
	je2.user_remark = "Trích lương tháng 09/2026"
	da2 = []
	je2.submit = lambda: da2.append(1)
	goi2 = []
	with patch.object(f, "get_roles", lambda *a, **k: ["AP Kiểm soát (FIN)"]), \
			patch.object(f, "get_doc", lambda *a, **k: je2), \
			patch.object(cn, "duyet_truoc_erp", lambda ten: goi2.append(ten)):
		bt.ghi_so(je2.name)
	la("bút toán tay ghi thẳng", (da2, goi2), ([1], []))


@ca("v552 vế Có mặc định 11211 MB Bank; công ty thiếu 11211 thì lùi về tài khoản tạm")
def _tk_co_mac_dinh():
	f = cn.frappe
	loc = []

	def ga(dt, filters=None, **k):
		loc.append(dict(filters or {}))
		if (filters or {}).get("account_number") == "11211":
			return ["11211 - Tiền gửi MB Bank 31561568 - TV"]
		return ["Temporary Opening - TV"]
	with patch.object(f, "get_all", ga):
		la("có 11211", cn._tk_co_truoc_erp("TV"), "11211 - Tiền gửi MB Bank 31561568 - TV")
	dung("tìm theo số hiệu, chỉ tài khoản chi tiết đang dùng",
		loc[0].get("account_number") == "11211" and loc[0].get("is_group") == 0 and loc[0].get("disabled") == 0)

	def thieu(dt, filters=None, **k):
		if (filters or {}).get("account_number"):
			return []
		return ["Temporary Opening - TV"]
	with patch.object(f, "get_all", thieu):
		la("thiếu 11211 thì tạm", cn._tk_co_truoc_erp("TV"), "Temporary Opening - TV")
	dung("lap_truoc_erp dùng vế Có mặc định mới",
		"_tk_co_truoc_erp(hd.company)" in __import__("inspect").getsource(cn.lap_truoc_erp))

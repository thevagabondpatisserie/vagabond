# -*- coding: utf-8 -*-
"""v512: kho DICH cua lenh san xuat la luat theo chang, khong phai lua chon.

Khai 18/09/2026 chup man Ton kho theo chang: banh thanh pham nam o kho
Pastry - Nguyen lieu ("sai kho"). Truy vet tren site: LSX-180926-000201 co
fg_warehouse = Pastry - Nguyen lieu vi o "Nhap thanh pham vao kho" tren app
cho chon moi kho bep va nho lua chon do. Ba lop sua:
  1. kho_san_xuat.kho_dich_bat_buoc: kho bep sai chang thi tra ve kho dung.
  2. Hook Work Order va Stock Entry (Manufacture) goi ham do, sua va bao.
  3. Man Ton kho theo chang danh dau "sai kho"; app chi cho chon kho Thanh pham.
"""

import io
import os
import re

from vagabond import kho_san_xuat as ks
from vagabond import ton_chang as tc
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	return io.open(os.path.join(GOC, *duong), encoding="utf-8").read()


@ca("v512: thanh pham chon kho Nguyen lieu cua bep thi tra ve kho Thanh pham")
def _tp_vao_nl():
	la("sửa về kho thành phẩm", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Pastry - Nguyên liệu - TV"),
		"Pastry - Thành phẩm - TV")
	la("chọn nhầm kho bếp khác", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Baker - Thành phẩm - TV"),
		"Pastry - Thành phẩm - TV")
	la("BTP vào kho Thành phẩm cũng sai", ks.kho_dich_bat_buoc(ks.BTP_SAN_SANG, "baker", "Baker - Thành phẩm - TV"),
		"Baker - Nguyên liệu - TV")


@ca("v512: kho dung, kho ngoai bep, thieu du kien thi KHONG dung")
def _khong_dung():
	la("đã đúng", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Pastry - Thành phẩm - TV"), None)
	la("BTP về kho Nguyên liệu là đúng luật 28/08", ks.kho_dich_bat_buoc(ks.BTP_SO_CAP, "pastry", "Pastry - Nguyên liệu - TV"), None)
	la("kho tổng 307 không đụng", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Kho tổng 307 - TV"), None)
	la("kho điểm bán không đụng", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Kho Sales Online - TV"), None)
	la("trống thì để hook điền", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", ""), None)
	la("không rõ chặng", ks.kho_dich_bat_buoc(None, "pastry", "Pastry - Nguyên liệu - TV"), None)
	la("không rõ bếp", ks.kho_dich_bat_buoc(ks.THANH_PHAM, None, "Pastry - Nguyên liệu - TV"), None)


@ca("v512: hook lenh va hook phieu deu di qua kho_dich_bat_buoc")
def _hook():
	s = _doc("vagabond", "kho_san_xuat.py")
	doan = s.split("def gan_kho_lenh")[1].split("\ndef ")[0]
	dung("lệnh: sửa fg_warehouse", "doc.fg_warehouse = dung" in doan and "_kho_dich_cua_ma(doc.production_item, doc.get(\"fg_warehouse\"))" in doan)
	dung("lệnh: khối v512 nằm NGOÀI try nuốt lỗi", doan.index("except Exception:") < doan.index("_kho_dich_cua_ma(doc.production_item"))
	doan2 = s.split("def gan_kho_thanh_pham")[1].split("\ndef ")[0]
	dung("phiếu: chỉ Manufacture", '"Manufacture"' in doan2)
	dung("phiếu: sửa t_warehouse dòng thành phẩm", "d.t_warehouse = dung" in doan2 and "is_finished_item" in doan2)
	h = _doc("vagabond", "hooks.py")
	dung("hook Stock Entry đăng ký", '"vagabond.kho_san_xuat.gan_kho_thanh_pham"' in h)
	dung("hook Work Order còn nguyên", '"before_validate": "vagabond.kho_san_xuat.gan_kho_lenh"' in h)


@ca("v512: man Ton kho theo chang danh dau sai kho theo dung luat kho dich")
def _sai_kho():
	dung("TP ở kho NL là sai", tc.kho_sai_chang(ks.THANH_PHAM, ks.NGUYEN_LIEU))
	dung("BTP ở kho NL là đúng", not tc.kho_sai_chang(ks.BTP_SAN_SANG, ks.NGUYEN_LIEU))
	dung("NL ở kho TP là sai", tc.kho_sai_chang(ks.NGUYEN_LIEU, ks.THANH_PHAM))
	dung("chưa phân chặng không kết luận", not tc.kho_sai_chang("", ks.NGUYEN_LIEU))
	ds = [
		{"ma": "BAWC1", "chang": ks.THANH_PHAM, "sl": 10, "kho": [{"kho": "Pastry - Nguyên liệu - TV", "sl": 10}]},
		{"ma": "BTP1", "chang": ks.BTP_SO_CAP, "sl": 3, "kho": [{"kho": "Pastry - Nguyên liệu - TV", "sl": 3}]},
		{"ma": "BAWC2", "chang": ks.THANH_PHAM, "sl": 5, "kho": [{"kho": "Pastry - Thành phẩm - TV", "sl": 5}]},
	]
	so = tc.danh_dau_sai_kho(ds, {"Pastry - Nguyên liệu - TV": ks.NGUYEN_LIEU, "Pastry - Thành phẩm - TV": ks.THANH_PHAM})
	la("đếm đúng 1 mã sai", so, 1)
	la("dòng sai gắn cờ", [d["sai_kho"] for d in ds], [True, False, False])
	dung("kho sai gắn cờ", ds[0]["kho"][0]["sai"] and not ds[1]["kho"][0]["sai"])
	js = _doc("vagabond", "public", "js", "bep", "37-ton-chang.js")
	dung("chip sai kho", "data-tcc=\"sai_kho\"" in js and "(sai kho)" in js)


@ca("v512: app KHONG loc kho theo ten nua (Codex #349), kho dich do may chu quyet theo chang")
def _app_picker():
	js = _doc("vagabond", "public", "js", "bep", "05-san-xuat.js")
	# Codex #349: loc "thanh pham" theo ten la sai voi ban thanh pham (kho dich
	# la Nguyen lieu). Bo loc; bep khong con o chon (y1), quan ly thay du kho,
	# may chu sua theo chang o moi duong ghi.
	dung("không còn bản lọc theo tên", "function mfgFgOpts()" not in js and "mfgLaKhoThanhPham" not in js)
	dung("ô fg của quản lý dùng danh sách kho bếp đầy đủ", "sheet(k === 'src' ? 'Kho nguyên liệu' : 'Kho thành phẩm', mfgWhOpts()" in js)


@ca("v512 Codex #349: hook phieu san xuat KHONG nuot loi, loi thi dung phieu")
def _fail_closed():
	s = _doc("vagabond", "kho_san_xuat.py")
	doan = s.split("def gan_kho_thanh_pham")[1].split("\ndef ")[0]
	dung("không còn try bao cả hàm", not doan.lstrip().startswith('"""') or "\n\ttry:\n\t\tif doc.docstatus" not in doan)
	dung("lỗi tra kho thì throw", "frappe.throw(" in doan and "Chưa rõ kho đích theo chặng" in doan)
	doan2 = s.split("def nhac_nhap_sai_kho")[1].split("\ndef ")[0]
	dung("chuyển kho tay chỉ NHẮC, không throw (anh Việt 20/09)", "frappe.msgprint(" in doan2 and "frappe.throw(" not in doan2)
	dung("ca kiểm thật đăng ký", "thu_kho_dich_512" in _doc("vagabond", "khung", "kiem_that", "cua.py"))
	# Chay that ham: tra kho nem loi thi phieu phai DUNG (dot bien 19/09 chen
	# `continue` truoc throw van xanh voi phep do chuoi, nen them ca nay).
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	def _dong(**kw):
		o = NS(**kw)
		o.get = lambda k, _o=o: getattr(_o, k, None)
		return o
	d = NS(docstatus=0, purpose="Manufacture", items=[_dong(item_code="BAWC00046", t_warehouse="Pastry - Nguyên liệu - TV", is_finished_item=1)], to_warehouse="")
	d.get = lambda k, _d=d: getattr(_d, k, None)
	f = NS(throw=lambda m, **k: (_ for _ in ()).throw(ValueError(m)), msgprint=lambda *a, **k: None,
		log_error=lambda *a, **k: None, get_traceback=lambda: "", db=NS(exists=lambda *a: True))
	with patch.object(ks, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda *a: (_ for _ in ()).throw(RuntimeError("db"))):
		try:
			ks.gan_kho_thanh_pham(d)
			dung("lỗi tra kho phải dừng phiếu", False)
		except ValueError as e:
			dung("nói rõ mã hàng", "BAWC00046" in str(e))
	# Duong thuong: kho sai thi doi va bao
	bao = []
	f2 = NS(throw=f.throw, msgprint=lambda *a, **k: bao.append(a[0]), log_error=f.log_error, get_traceback=f.get_traceback, db=NS(exists=lambda *a: True))
	with patch.object(ks, "frappe", f2), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: "Pastry - Thành phẩm - TV"):
		ks.gan_kho_thanh_pham(d)
	la("t_warehouse đã đổi", d.items[0].t_warehouse, "Pastry - Thành phẩm - TV")
	la("có báo", len(bao), 1)


# ---------------- bon y anh Viet duyet 19/09/2026 ----------------


@ca("v512 y1: bep khong bam duoc o kho thanh pham, chi quan ly san xuat con o chon")
def _y1_khoa_o():
	js = _doc("vagabond", "public", "js", "bep", "05-san-xuat.js")
	doan = js.split("function mfgWhCard")[1].split("\nfunction ")[0]
	dung("có nhánh quản lý mới có data-mw=fg", "mfgQuanLy()" in doan and doan.count('data-mw="fg"') == 1)
	dung("nhánh bếp là chữ đọc, ghi rõ máy tự chọn", "máy tự chọn theo chặng" in doan)


@ca("v512 y2 (doi 20/09): chuyen kho, nhap tay vao kho bep sai chang chi NHAC, khong chan; kiem ke cung chi nhac")
def _y2_nhac():
	# Anh Viet 20/09/2026: "khong can chan gi ca... cu de hang hoa thoai mai
	# tu do luu chuyen". Ban 19/09 chan ba loai phieu; nay chi nhac.
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	def _phieu(purpose, items, docstatus=0):
		d = NS(docstatus=docstatus, purpose=purpose, items=items)
		d.get = lambda k, _d=d: getattr(_d, k, None)
		return d

	def _dong(**kw):
		o = NS(**kw)
		o.get = lambda k, _o=o: getattr(_o, k, None)
		return o

	nhac = []
	f = NS(throw=lambda m, **k: (_ for _ in ()).throw(ValueError(m)), msgprint=lambda *a, **k: nhac.append(a[0]),
		log_error=lambda *a, **k: None, get_traceback=lambda: "")
	with patch.object(ks, "frappe", f), patch.object(ks, "_kho_dich_cua_ma",
			lambda ma, kho: "Pastry - Thành phẩm - TV" if ma.startswith("BAWC") and "Nguyên liệu" in kho else None):
		dong = [_dong(item_code="BAWC00046", t_warehouse="Pastry - Nguyên liệu - TV")]
		for muc in ("Material Transfer", "Material Receipt", "Material Transfer for Manufacture"):
			ks.nhac_nhap_sai_kho(_phieu(muc, dong))
		la("ba loại phiếu: ba lời nhắc, không ném", len(nhac), 3)
		dung("nhắc có tên kho theo chặng", all("Pastry - Thành phẩm - TV" in x for x in nhac))
		ks.nhac_nhap_sai_kho(_phieu("Material Transfer", [_dong(item_code="BAWC00046", t_warehouse="Pastry - Thành phẩm - TV")]))
		ks.nhac_nhap_sai_kho(_phieu("Material Transfer", [_dong(item_code="NBTP00029", t_warehouse="Pastry - Nguyên liệu - TV")]))
		ks.nhac_nhap_sai_kho(_phieu("Manufacture", dong))
		ks.nhac_nhap_sai_kho(_phieu("Material Transfer", dong, docstatus=1))
		la("đúng kho, BTP về NL, Manufacture, đã ghi sổ: không nhắc thêm", len(nhac), 3)
	# Tra kho loi cung khong lam hong phieu
	with patch.object(ks, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: (_ for _ in ()).throw(RuntimeError("db"))):
		ks.nhac_nhap_sai_kho(_phieu("Material Transfer", [_dong(item_code="BAWC00046", t_warehouse="Pastry - Nguyên liệu - TV")]))
	la("lỗi tra kho: bỏ qua, không nhắc, không ném", len(nhac), 3)
	# kiem ke: chi canh bao
	with patch.object(ks, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: "Pastry - Thành phẩm - TV"):
		kk = _phieu("", [_dong(item_code="BAWC00046", warehouse="Pastry - Nguyên liệu - TV", qty=3)])
		ks.canh_bao_kiem_ke_sai_kho(kk)
	la("kiểm kê cảnh báo một lần", len(nhac), 4)
	h = _doc("vagabond", "hooks.py")
	dung("hook nhắc đăng ký ở validate Stock Entry, hook chặn cũ không còn",
		'"vagabond.kho_san_xuat.nhac_nhap_sai_kho"' in h and "chan_nhap_sai_kho" not in h)
	dung("hook kiểm kê đăng ký", '"vagabond.kho_san_xuat.canh_bao_kiem_ke_sai_kho"' in h)


@ca("v512 (20/09): bep lay theo kho dang chon, may khong doi bep cua hang, chi sua chang")
def _bep_theo_kho():
	from unittest.mock import patch
	with patch.object(ks, "_ho_so_mon", lambda ma: (None, None)), patch.object(ks, "_co_btp_con", lambda ma: False), \
			patch.object(ks, "_bep_cua_mon", lambda ma: "pastry"):
		la("món Pastry ở kho Baker - Thành phẩm: đúng chặng, để yên", ks._kho_dich_cua_ma("BAWC00046", "Baker - Thành phẩm - TV"), None)
		la("món Pastry ở kho Baker - Nguyên liệu: sửa chặng trong Baker", ks._kho_dich_cua_ma("BAWC00046", "Baker - Nguyên liệu - TV"), "Baker - Thành phẩm - TV")
		la("kho tổng: không đụng", ks._kho_dich_cua_ma("BAWC00046", "Kho tổng 307 - TV"), None)
		la("hậu tố theo kho", ks._kho_dich_cua_ma("BAWC00046", "Pastry - Nguyên liệu - VK"), "Pastry - Thành phẩm - VK")
	s = _doc("vagabond", "kho_san_xuat.py")
	doan = s.split("def _kho_dich_cua_ma")[1].split("\ndef ")[0]
	dung("không còn ưu tiên bếp phụ trách trên món", "_bep_cua_mon" not in doan)


@ca("v512 y3: kho dung cua dong sai kho, va cua tao phieu chuyen nhap dang ky cua ngo")
def _y3_phieu():
	la("TP ở kho NL Pastry thì về Pastry - Thành phẩm", tc.kho_dung_cua(ks.THANH_PHAM, "pastry"), "Pastry - Thành phẩm - TV")
	la("NL ở kho TP Baker thì về Baker - Nguyên liệu", tc.kho_dung_cua(ks.NGUYEN_LIEU, "baker"), "Baker - Nguyên liệu - TV")
	# Dot bien 19/09: ban dau thieu ca nay nen bo LUAT_KHO_DICH van xanh (dieu 17a).
	la("BTP ở kho TP thì về kho Nguyên liệu theo luật 28/08", tc.kho_dung_cua(ks.BTP_SAN_SANG, "pastry"), "Pastry - Nguyên liệu - TV")
	d = {"chang": ks.THANH_PHAM, "kho": [{"kho": "Pastry - Nguyên liệu - TV", "sl": 3, "sai": True}]}
	la("kho đúng của dòng", tc.kho_dung_cua_dong(d, {"Pastry - Nguyên liệu - TV": "pastry"}), "Pastry - Thành phẩm - TV")
	la("dòng không sai thì None", tc.kho_dung_cua_dong({"chang": ks.THANH_PHAM, "kho": [{"kho": "x", "sai": False}]}, {}), None)
	from vagabond.khung.kiem_thu import thu_cua_ngo
	dung("cửa ngõ đăng ký", "tao_phieu_ve_dung_kho" in (thu_cua_ngo.CUA_NGO.get("ton_chang.py") or []))
	s = _doc("vagabond", "ton_chang.py")
	doan = s.split("def tao_phieu_ve_dung_kho")[1].split("\n@frappe")[0]
	dung("chỉ lập NHÁP, không submit", "se.insert()" in doan and ".submit()" not in doan)
	dung("gác quyền QUYEN_GHI", "QUYEN_GHI" in doan)
	dung("số gửi phải bằng tồn hiện tại (Codex vòng 4 thay cho 'chặn quá tồn')", "Số tồn đã đổi" in doan)
	js = _doc("vagabond", "public", "js", "bep", "37-ton-chang.js")
	dung("nút chỉ hiện khi sai kho và có quyền", "x.sai_kho && d.lap_duoc && x.kho_dung" in js)
	dung("hỏi xác nhận rồi mới gọi", "confirmSheet('Chuyển về đúng kho'" in js and "vagabond.ton_chang.tao_phieu_ve_dung_kho" in js)


@ca("v512 y4: Viec can lam co loai sai_kho, dung vai, mo ra man Ton kho theo chang")
def _y4_viec():
	from vagabond import viec_can_lam as v
	dung("có loại sai_kho", any(k == "sai_kho" for k, _, _ in v.LOAI_PHIEU))
	dung("bếp (Stock User) thấy", v.thay_duoc("sai_kho", {"Stock User"}))
	dung("quản lý sản xuất thấy", v.thay_duoc("sai_kho", {"Manufacturing Manager"}))
	dung("kế toán không thấy", not v.thay_duoc("sai_kho", {"Accounts User"}))
	s = _doc("vagabond", "viec_can_lam.py")
	dung("nguồn gom có sai_kho, truyền kho mình giữ", '("sai_kho", lambda: _viec_sai_kho(vai, bp, kho)),' in s)
	dung("đọc từ cùng một nguồn ton_theo_chang, chip SAI_KHO", "chang=ton_chang.SAI_KHO" in s)
	js = _doc("vagabond", "public", "js", "bep", "02-trang-chu.js")
	dung("app mở màn Tồn kho theo chặng lọc Sai kho", "if (l === 'sai_kho') return go(function () { tch.chang = 'sai_kho';" in js)
	dung("có icon", "sai_kho: '⚠️'" in js)


# ---------------- Codex #349 vong 2 (2ef823d) + bench CI do 19/09 ----------------


@ca("v512 Codex I1: nguyen lieu nhap vao kho Thanh pham cung la sai kho")
def _i1_nvl_vao_tp():
	la("NVLT vào kho Thành phẩm thì kho đúng là Nguyên liệu",
		ks.kho_dich_bat_buoc(ks.NGUYEN_LIEU, "pastry", "Pastry - Thành phẩm - TV"), "Pastry - Nguyên liệu - TV")
	la("NVLT ở kho Nguyên liệu là đúng", ks.kho_dich_bat_buoc(ks.NGUYEN_LIEU, "pastry", "Pastry - Nguyên liệu - TV"), None)
	la("NVLT ở kho tổng không đụng", ks.kho_dich_bat_buoc(ks.NGUYEN_LIEU, "pastry", "Kho tổng 307 - TV"), None)
	dung("LUAT_KHO_DICH của lệnh sản xuất không bị đổi", ks.NGUYEN_LIEU not in ks.LUAT_KHO_DICH)
	la("cùng câu trả lời với màn Tồn kho theo chặng", tc.kho_sai_chang(ks.NGUYEN_LIEU, ks.THANH_PHAM), True)


@ca("v512 CI: hau to kho doc tu kho dang chon, khong ghep cung ' - TV'")
def _hau_to():
	la("site thật", ks.hau_to_cua_kho("Pastry - Nguyên liệu - TV"), " - TV")
	la("bench CI", ks.hau_to_cua_kho("Pastry - Nguyên liệu - VK"), " - VK")
	la("kho không phải kho bếp thì mặc định", ks.hau_to_cua_kho("Kho tổng 307 - VK"), " - TV")
	la("trống thì mặc định", ks.hau_to_cua_kho(""), " - TV")
	la("kho đích trên site VK phải là VK",
		ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Pastry - Nguyên liệu - VK"), "Pastry - Thành phẩm - VK")
	la("BTP trên site VK", ks.kho_dich_bat_buoc(ks.BTP_SO_CAP, "baker", "Baker - Thành phẩm - VK"), "Baker - Nguyên liệu - VK")
	la("truyền hậu tố tay vẫn được", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Pastry - Nguyên liệu - VK", " - XX"), "Pastry - Thành phẩm - XX")


@ca("v512 Codex I2: kho dung chua duoc tao thi DUNG phieu va lenh, khong bo qua lang")
def _i2_thieu_kho():
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	def _dong(**kw):
		o = NS(**kw)
		o.get = lambda k, _o=o: getattr(_o, k, None)
		return o

	def _throw(m, **k):
		raise ValueError(m)
	f = NS(throw=_throw, msgprint=lambda *a, **k: None, log_error=lambda *a, **k: None,
		get_traceback=lambda: "", db=NS(exists=lambda *a: False))
	# Phieu Manufacture
	d = NS(docstatus=0, purpose="Manufacture", to_warehouse="",
		items=[_dong(item_code="BAWC00046", t_warehouse="Pastry - Nguyên liệu - VK", is_finished_item=1)])
	d.get = lambda k, _d=d: getattr(_d, k, None)
	with patch.object(ks, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: "Pastry - Thành phẩm - VK"):
		try:
			ks.gan_kho_thanh_pham(d)
			dung("phiếu: thiếu kho đích phải dừng", False)
		except ValueError as e:
			dung("phiếu: nói rõ kho thiếu", "Pastry - Thành phẩm - VK" in str(e) and "BAWC00046" in str(e))
	la("phiếu: kho khai không bị đổi nửa chừng", d.items[0].t_warehouse, "Pastry - Nguyên liệu - VK")
	# Lenh san xuat: khoi v512 nam ngoai try nen loi phai thoat ra
	w = NS(docstatus=0, production_item="BAWC00046", fg_warehouse="Pastry - Nguyên liệu - VK",
		source_warehouse="", wip_warehouse="")
	w.get = lambda k, _w=w: getattr(_w, k, None)
	w.set = lambda k, v, _w=w: setattr(_w, k, v)
	import sys
	from types import ModuleType
	gia = ModuleType("vagabond.san_xuat_desktop")
	gia.dien_kho_mon = lambda doc: None
	with patch.object(ks, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: "Pastry - Thành phẩm - VK"), \
			patch.dict(sys.modules, {"vagabond.san_xuat_desktop": gia}), \
			patch.object(ks, "_bep_cua_mon", lambda ma: "pastry"), patch.object(ks, "_ho_so_mon", lambda ma: (None, None)), \
			patch.object(ks, "_co_btp_con", lambda ma: False):
		try:
			ks.gan_kho_lenh(w)
			dung("lệnh: thiếu kho đích phải dừng", False)
		except ValueError as e:
			dung("lệnh: nói rõ kho thiếu", "Pastry - Thành phẩm - VK" in str(e))
		# Co kho thi doi
		f.db.exists = lambda *a: True
		ks.gan_kho_lenh(w)
		la("lệnh: có kho thì đổi fg_warehouse", w.fg_warehouse, "Pastry - Thành phẩm - VK")


@ca("v512 Codex I3: giam doc that KHONG thay viec sai kho (luat 31/08), System Manager thay")
def _i3_giam_doc():
	from vagabond import viec_can_lam as v
	dung("Giám đốc bị siết, đúng ý anh Việt 31/08", not v.thay_duoc("sai_kho", {"Giám đốc", "Stock User"}))
	dung("AP Giám đốc cũng vậy", not v.thay_duoc("sai_kho", {"AP Giám đốc"}))
	dung("System Manager thấy (vai kỹ thuật)", v.thay_duoc("sai_kho", {"System Manager"}))
	dung("sai_kho không nằm trong việc hệ trọng", "sai_kho" not in v.VIEC_HE_TRONG)


# ---------------- Codex #349 vong 3 (8a88db4): phieu chuyen ve dung kho ----------------


@ca("v512 Codex J1: kho dung cua dong doc hau to tu kho dang chua, khong ghep cung TV")
def _j1_hau_to_hien_thi():
	d = {"chang": ks.THANH_PHAM, "kho": [{"kho": "Pastry - Nguyên liệu - VK", "sl": 3, "sai": True}]}
	la("hiển thị trên site VK", tc.kho_dung_cua_dong(d, {"Pastry - Nguyên liệu - VK": "pastry"}), "Pastry - Thành phẩm - VK")
	la("kho_dung_cua nhận hậu tố", tc.kho_dung_cua(ks.THANH_PHAM, "pastry", " - VK"), "Pastry - Thành phẩm - VK")
	la("không truyền thì như cũ", tc.kho_dung_cua(ks.THANH_PHAM, "pastry"), "Pastry - Thành phẩm - TV")


@ca("v512 Codex J1+J2: phieu chuyen ve dung kho dung CUNG ham kho dich voi hook (bep tren mon, hau to tu kho sai)")
def _j2_cung_nguon():
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	s = _doc("vagabond", "ton_chang.py")
	doan = s.split("def tao_phieu_ve_dung_kho")[1].split("\n@frappe")[0]
	dung("không còn tự tính chặng rồi ghép kho", "kho_dung_cua(chang, bep)" not in doan and "_chang_cua_ma(" not in doan)
	dung("đi qua ksx._kho_dich_cua_ma", "ksx._kho_dich_cua_ma(ma, kho_sai)" in doan)

	def _throw(m, **k):
		raise ValueError(m)
	tao = []

	class SE(object):
		def __init__(self):
			self.items = []
			self.name = "PCK-KT"
		def append(self, k, r):
			self.items.append(r)
		def insert(self):
			tao.append(self)
	f = NS(get_roles=lambda: ["Manufacturing Manager"], throw=_throw, log_error=lambda *a, **k: None,
		get_traceback=lambda: "", new_doc=lambda dt: SE(),
		db=NS(get_value=lambda dt, n, f=None, as_dict=False, **k: (NS(item_name="Bánh", stock_uom="Cái") if dt == "Item" else (None if dt == "Stock Entry" else 5)),
			exists=lambda *a: True))
	goi = []

	def _kd(ma, kho):
		goi.append((ma, kho))
		# Mon Pastry nam o kho Baker: hook quyet ve Pastry, khong phai Baker -> Baker
		return "Pastry - Thành phẩm - VK"
	with patch.object(tc, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", _kd):
		kq = tc.tao_phieu_ve_dung_kho("BAWC00046", "Baker - Thành phẩm - VK", 5)
	la("gọi đúng hàm với kho sai", goi, [("BAWC00046", "Baker - Thành phẩm - VK")])
	la("kho đến là kho hook quyết", kq["den"], "Pastry - Thành phẩm - VK")
	la("dòng phiếu cùng kho đến", tao[0].items[0]["t_warehouse"], "Pastry - Thành phẩm - VK")
	# Hook noi "dang dung kho" thi khong lap
	with patch.object(tc, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: None):
		try:
			tc.tao_phieu_ve_dung_kho("BAWC00046", "Pastry - Thành phẩm - VK", 5)
			dung("đúng kho thì phải từ chối", False)
		except ValueError as e:
			dung("nói đúng kho", "đúng kho" in str(e))
	# Kho dich chua duoc tao thi dung, khong de insert vo
	f2 = NS(**{**f.__dict__, "db": NS(get_value=f.db.get_value, exists=lambda dt, n: n != "Pastry - Thành phẩm - VK")})
	with patch.object(tc, "frappe", f2), patch.object(ks, "_kho_dich_cua_ma", _kd):
		try:
			tc.tao_phieu_ve_dung_kho("BAWC00046", "Baker - Thành phẩm - VK", 5)
			dung("thiếu kho đích phải dừng", False)
		except ValueError as e:
			dung("nói rõ kho thiếu", "chưa được tạo" in str(e))


# ---------------- Codex #349 vong 4 (f41b415) ----------------


@ca("v512 Codex K1: so man gui khac ton hien tai thi tu choi, khong lap phieu mot phan")
def _k1_ton_doi():
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	def _throw(m, **k):
		raise ValueError(m)
	tao = []

	class SE(object):
		def __init__(self):
			self.items = []
			self.name = "PCK"
		def append(self, k, r):
			self.items.append(r)
		def insert(self):
			tao.append(self)
	f = NS(get_roles=lambda: ["Manufacturing Manager"], throw=_throw, log_error=lambda *a, **k: None,
		get_traceback=lambda: "", new_doc=lambda dt: SE(),
		db=NS(get_value=lambda dt, n, f=None, as_dict=False, **k: (NS(item_name="Bánh", stock_uom="Cái") if dt == "Item" else (7 if dt == "Bin" else (None if dt == "Stock Entry" else "Cty"))),
			exists=lambda *a: True))
	with patch.object(tc, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: "Pastry - Thành phẩm - TV"):
		for sl in (2, 9):
			try:
				tc.tao_phieu_ve_dung_kho("BAWC00046", "Pastry - Nguyên liệu - TV", sl)
				dung("gửi %s khi tồn 7 phải bị từ chối" % sl, False)
			except ValueError as e:
				dung("bắt tải lại màn", "Tải lại" in str(e) and "7" in str(e))
		la("chưa lập phiếu nào", len(tao), 0)
		kq = tc.tao_phieu_ve_dung_kho("BAWC00046", "Pastry - Nguyên liệu - TV", 7)
		la("đúng tồn thì lập, chuyển hết", (kq["sl"], tao[0].items[0]["qty"]), (7, 7))
	s = _doc("vagabond", "ton_chang.py")
	doan = s.split("def tao_phieu_ve_dung_kho")[1].split("\n@frappe")[0]
	dung("không còn cho phép sl nhỏ hơn tồn", "if sl > ton + 0.0001" not in doan)


@ca("v512 Codex K2: kho dich tinh cho TUNG kho sai, man xac nhan doc theo kho dang bam")
def _k2_tung_kho():
	d = {"ma": "BAWC00046", "chang": ks.THANH_PHAM, "kho": [
		{"kho": "Baker - Nguyên liệu - TV", "sl": 2, "sai": True},
		{"kho": "Pastry - Nguyên liệu - TV", "sl": 3, "sai": True},
		{"kho": "Pastry - Thành phẩm - TV", "sl": 1, "sai": False},
	]}
	tc.kho_dung_tung_kho(d, {"Baker - Nguyên liệu - TV": "baker", "Pastry - Nguyên liệu - TV": "pastry"})
	la("Baker về Baker", d["kho"][0]["kho_dung"], "Baker - Thành phẩm - TV")
	la("Pastry về Pastry", d["kho"][1]["kho_dung"], "Pastry - Thành phẩm - TV")
	dung("kho đúng không gắn", "kho_dung" not in d["kho"][2])
	s = _doc("vagabond", "ton_chang.py")
	doan = s.split("def ton_theo_chang")[1].split("\ndef ")[0]
	dung("máy chủ gắn kho_dung từng kho, ưu tiên hàm của hook", "kho_dung_tung_kho(d, bep_kho)" in doan and 'k["kho_dung"] = _kho_dung_that(d["ma"], k["kho"])' in doan)
	js = _doc("vagabond", "public", "js", "bep", "37-ton-chang.js")
	dung("app hỏi xác nhận theo kho của dòng đang bấm", "var den = k.kho_dung || x.kho_dung;" in js and "sang ' + shortWh(den)" in js)
	dung("không còn xác nhận bằng kho của dòng", "sang ' + shortWh(x.kho_dung)" not in js)


# ---------------- Codex #349 vong 5 (fdc4a41) ----------------


@ca("v512 Codex L1+L3: viec sai kho loc theo kho minh giu, moi kho sai ghi kem kho dich cua no")
def _l1_l3_viec():
	from vagabond import viec_can_lam as v
	x = {"ma": "BAWC00046", "ten": "Bánh", "kho_dung": "Baker - Thành phẩm - TV", "kho": [
		{"kho": "Baker - Nguyên liệu - TV", "sl": 2, "sai": True, "kho_dung": "Baker - Thành phẩm - TV"},
		{"kho": "Pastry - Nguyên liệu - TV", "sl": 3, "sai": True, "kho_dung": "Pastry - Thành phẩm - TV"},
		{"kho": "Pastry - Thành phẩm - TV", "sl": 1, "sai": False},
	]}
	r = v.dong_sai_kho(x, {"Stock User"}, ["Pastry - Nguyên liệu - TV", "Pastry - Thành phẩm - TV"])
	dung("người giữ kho Pastry chỉ thấy kho Pastry", "Baker" not in r["phu"] and "Pastry - Nguyên liệu - TV -> Pastry - Thành phẩm - TV" in r["phu"])
	la("người giữ kho không dính kho nào thì không có việc", v.dong_sai_kho(x, {"Stock User"}, ["Kho tổng 307 - TV"]), None)
	r2 = v.dong_sai_kho(x, {"Stock User"}, [])
	dung("không khai kho thì thấy hết, mỗi kho một đích", "Baker - Nguyên liệu - TV -> Baker - Thành phẩm - TV" in r2["phu"] and "Pastry - Nguyên liệu - TV -> Pastry - Thành phẩm - TV" in r2["phu"])
	r3 = v.dong_sai_kho(x, {"Manufacturing Manager"}, ["Kho tổng 307 - TV"])
	dung("quản lý sản xuất (không phải VAI_KHO) thấy hết", r3 and "Baker" in r3["phu"] and "Pastry" in r3["phu"])
	r4 = v.dong_sai_kho(x, {"Stock User", "System Manager"}, ["Kho tổng 307 - TV"])
	dung("System Manager kèm vai kho vẫn thấy hết", r4 is not None)
	dung("không còn dùng kho_dung của dòng làm đích chung", "x.get(\"kho_dung\") or \"?\"" not in _doc("vagabond", "viec_can_lam.py").split("def _viec_sai_kho")[1].split("\ndef ")[0])


@ca("v512 Codex L2: bam hai lan khong ra hai phieu nhap trung")
def _l2_idempotent():
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	def _throw(m, **k):
		raise ValueError(m)
	tao = []

	class SE(object):
		def __init__(self):
			self.items = []
			self.name = "PCK-MOI"
		def append(self, k, r):
			self.items.append(r)
		def insert(self):
			tao.append(self)
	nhap = {"co": None}

	def gv(dt, n, f=None, as_dict=False, **k):
		if dt == "Item":
			return NS(item_name="Bánh", stock_uom="Cái")
		if dt == "Bin":
			return 7
		if dt == "Stock Entry":
			nhap["loc"] = n
			return nhap["co"]
		return "Cty"
	f = NS(get_roles=lambda: ["Manufacturing Manager"], throw=_throw, log_error=lambda *a, **k: None,
		get_traceback=lambda: "", new_doc=lambda dt: SE(), db=NS(get_value=gv, exists=lambda *a: True))
	with patch.object(tc, "frappe", f), patch.object(ks, "_kho_dich_cua_ma", lambda ma, kho: "Pastry - Thành phẩm - TV"):
		kq1 = tc.tao_phieu_ve_dung_kho("BAWC00046", "Pastry - Nguyên liệu - TV", 7)
		la("lần đầu lập phiếu mới", (kq1["name"], len(tao)), ("PCK-MOI", 1))
		dung("tra phiếu nháp cùng mã, cùng kho đi, kho đến", nhap["loc"]["docstatus"] == 0 and nhap["loc"]["from_warehouse"] == "Pastry - Nguyên liệu - TV"
			and nhap["loc"]["to_warehouse"] == "Pastry - Thành phẩm - TV" and "BAWC00046" in nhap["loc"]["remarks"][1])
		nhap["co"] = NS(name="PCK-CU", posting_date="2026-09-19")
		kq2 = tc.tao_phieu_ve_dung_kho("BAWC00046", "Pastry - Nguyên liệu - TV", 7)
		la("lần hai trả lại phiếu cũ, không lập thêm", (kq2["name"], kq2.get("da_co"), len(tao)), ("PCK-CU", 1, 1))

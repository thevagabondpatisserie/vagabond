# -*- coding: utf-8 -*-
"""v630: ảnh thẻ tuyển dụng trên web (Minh Vũ phản hồi 02/11/2026).

Minh Vũ báo hai việc: trình biên tập web không đổi được ảnh của các vị trí
đang tuyển (thẻ Tuyển dụng chỉ xem), và màn sửa vị trí trên app chỉ cho chọn
bốn ảnh có sẵn, không tải ảnh riêng được. Ca nào giữ điều gì:
  1. Marketing đổi ảnh một vị trí ngay ở trình biên tập; chỉ ô ảnh được ghi,
     cùng luật ảnh với form app, người không có vai Marketing bị chặn TRƯỚC khi
     chạm dữ liệu (_doi_anh, _doi_anh_quyen).
  2. Màn sửa vị trí tải ảnh qua cửa riêng chặn vai Tuyển dụng; cả hai cửa tải
     dùng MỘT phép kiểm, lưu ảnh (_tai_anh_quyen, _anh_that).
  3. Thẻ Tuyển dụng của trình biên tập biết ảnh đang dùng và ảnh đã chọn
     (_ds_bien_tap).
Phần bấm thật ở hanh_vi/anh_tuyen_dung_630.js.
"""

import io
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_tuyen_dung_622 import _Site, _chay, _loi, _vt, td
from vagabond import noi_dung_web as nw  # noqa: E402
from vagabond import tuyen_dung_form as tf  # noqa: E402

VAI_TD = (td.VAI_TUYEN_DUNG,)
VAI_MKT = ("Marketing",)


def _luu(site):
	return [g for g in site.ghi if g[0] == "save"]


@ca("v630 đổi ảnh một vị trí: ghi đúng ô ảnh, để trống là trả về ảnh tự chọn, ảnh lạ bị chặn mà không ghi")
def _doi_anh():
	site = _Site(vt=[_vt(anh_web="")])
	_chay(site, lambda: td.dat_anh_web("VTT-0001", " /files/web-abc123.jpg "), VAI_MKT)
	vt = site.lay(td.VT, "VTT-0001")
	la("ghi ảnh đã gọt khoảng trắng", vt["anh_web"], "/files/web-abc123.jpg")
	la("một lần lưu", len(_luu(site)), 1)
	la("các ô khác giữ nguyên", (vt["tieu_de"], vt["dang_tuyen"], vt["muc_luong"]), ("Thu ngân ca tối", 1, "25.000 đ/giờ"))
	_chay(site, lambda: td.dat_anh_web("VTT-0001", "/files/web-abc123.jpg"), VAI_MKT)
	la("cùng ảnh thì không lưu lại", len(_luu(site)), 1)
	_chay(site, lambda: td.dat_anh_web("VTT-0001", ""), VAI_MKT)
	la("để trống là về ảnh tự chọn", vt["anh_web"], "")
	for sai in ("/private/files/cv.jpg", "javascript:alert(1)", "/files/logo.svg", "/files/a.jpg\" onerror=\"x",
			"http://la.vn/a.jpg", "/files/../private/a.jpg", "data:image/png;base64,AA"):
		truoc = len(_luu(site))
		cau = _loi(lambda: _chay(site, lambda: td.dat_anh_web("VTT-0001", sai), VAI_MKT))
		dung("chặn " + sai + ": " + cau, "ảnh công khai" in cau)
		la("không ghi khi chặn " + sai, (len(_luu(site)), vt["anh_web"]), (truoc, ""))
	dung("vị trí không có", "Không tìm thấy vị trí" in _loi(lambda: _chay(site, lambda: td.dat_anh_web("VTT-0099", "/files/a.jpg"), VAI_MKT)))
	dung("thiếu mã vị trí", "Không tìm thấy vị trí" in _loi(lambda: _chay(site, lambda: td.dat_anh_web("", "/files/a.jpg"), VAI_MKT)))


@ca("v630 cửa trình biên tập: chỉ vai Marketing đổi được ảnh, chặn trước khi chạm vị trí; xong trả cả bảng như các hàm lưu khác")
def _doi_anh_quyen():
	site = _Site(vt=[_vt(anh_web="")])
	vet = []
	bang = {"tuyen_dung_erp": ["bảng mới"]}
	with um.patch.object(nw, "bang_moi", lambda: vet.append("bang") or bang):
		for vai in ((), VAI_TD, ("Sales User",)):
			cau = _loi(lambda: _chay(site, lambda: nw.doi_anh_tuyen_dung("VTT-0001", "/files/web-a.jpg"), vai))
			dung("vai %r bị chặn: %s" % (vai, cau), "quyền Marketing" in cau)
		la("bị chặn thì vị trí không đổi", (site.lay(td.VT, "VTT-0001")["anh_web"], len(_luu(site)), vet), ("", 0, []))
		ra = _chay(site, lambda: nw.doi_anh_tuyen_dung("VTT-0001", "/files/web-a.jpg"), VAI_MKT)
	la("Marketing đổi được", site.lay(td.VT, "VTT-0001")["anh_web"], "/files/web-a.jpg")
	la("trả cả bảng để trình biên tập vẽ lại", ra, bang)


@ca("v630 cửa tải ảnh: màn sửa vị trí chặn vai Tuyển dụng, trình biên tập chặn vai Marketing; cả hai đi qua MỘT phép lưu ảnh")
def _tai_anh_quyen():
	site = _Site()
	vet = []
	with um.patch.object(nw, "luu_anh_cong_khai", lambda: vet.append("luu") or {"url": "/files/web-hhh.jpg"}):
		dung("app: không có vai Tuyển dụng bị chặn", "Phân hệ Tuyển dụng" in _loi(lambda: _chay(site, td.tai_anh_web, VAI_MKT)))
		dung("biên tập: không có vai Marketing bị chặn", "quyền Marketing" in _loi(lambda: _chay(site, nw.tai_anh, VAI_TD)))
		la("bị chặn thì không lưu tệp nào", vet, [])
		la("app tải được", _chay(site, td.tai_anh_web, VAI_TD), {"url": "/files/web-hhh.jpg"})
		la("biên tập tải được", _chay(site, nw.tai_anh, VAI_MKT), {"url": "/files/web-hhh.jpg"})
	la("hai cửa cùng một phép lưu", vet, ["luu", "luu"])


@ca("v630 phép lưu ảnh chung: nhận PNG thật, chặn SVG, tệp giả ảnh, ảnh quá 10 MB; tên tệp do máy chủ đặt")
def _anh_that():
	try:
		from PIL import Image
	except ImportError:
		# Máy CI không có Pillow: phần kiểm ảnh thật chạy ở máy có Pillow (cổng kiểm tay).
		return
	buf = io.BytesIO()
	Image.new("RGB", (8, 6), (41, 189, 179)).save(buf, "PNG")
	png = buf.getvalue()
	luu = []

	def _save_file(ten, nd, *a, **k):
		luu.append((ten, len(nd), k.get("is_private")))
		return types.SimpleNamespace(file_url="/files/" + ten)

	fm = types.ModuleType("frappe.utils.file_manager")
	fm.save_file = _save_file

	def chay(noi_dung, ten="anh.png"):
		tep = types.SimpleNamespace(stream=io.BytesIO(noi_dung), filename=ten)
		req = types.SimpleNamespace(files={"file": tep})
		with um.patch.dict(sys.modules, {"frappe.utils.file_manager": fm}), \
				um.patch.object(nw.frappe, "request", req, create=True), \
				um.patch.object(nw.frappe, "generate_hash", lambda length=10: "h" * length, create=True):
			return nw.luu_anh_cong_khai()

	la("PNG thật", chay(png, "../../x.svg"), {"url": "/files/web-hhhhhhhhhhhh.png"})
	la("lưu công khai, tên máy đặt", luu, [("web-hhhhhhhhhhhh.png", len(png), 0)])
	svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
	dung("chặn SVG", "Không đọc được ảnh" in _loi(lambda: chay(svg, "a.png")))
	dung("chặn tệp giả ảnh", "Không đọc được ảnh" in _loi(lambda: chay(b"\x89PNG\r\n\x1a\nkhong-phai-anh", "a.png")))
	dung("chặn ảnh quá 10 MB", "lớn hơn 10 MB" in _loi(lambda: chay(png + b"0" * (10 * 1024 * 1024), "a.png")))
	la("bị chặn thì không lưu", len(luu), 1)


@ca("v630 thẻ Tuyển dụng của trình biên tập: có ảnh khách đang thấy và ảnh đã chọn (trống là tự chọn theo bộ phận)")
def _ds_bien_tap():
	site = _Site(vt=[_vt(anh_web="/files/web-rieng.jpg"),
		_vt(name="VTT-0002", tieu_de="Phụ bếp Pastry", bo_phan="Bếp Pastry - TV", anh_web="", dang_tuyen=0),
		_vt(name="VTT-0003", tieu_de="Phục vụ", bo_phan="Phục vụ - TV", anh_web="/private/files/cu.jpg")])
	ds = {r["ma_vi_tri"]: r for r in _chay(site, td.ds_web_bien_tap, VAI_MKT)}
	la("ảnh tải riêng", (ds["VTT-0001"]["anh_web"], ds["VTT-0001"]["anh_the"]), ("/files/web-rieng.jpg", "/files/web-rieng.jpg"))
	la("chưa chọn: ảnh theo bộ phận", (ds["VTT-0002"]["anh_web"], ds["VTT-0002"]["anh_the"]), ("", tf.anh_theo_nhom("Bếp Pastry", "Phụ bếp Pastry")))
	la("vị trí đang tắt vẫn đổi ảnh được (có trong danh sách)", ds["VTT-0002"]["khach_thay"], 0)
	dung("ảnh cũ không hợp lệ: khách thấy ảnh theo bộ phận", ds["VTT-0003"]["anh_the"].startswith("/assets/vagabond/"))

"""v644 bench: bánh trên web quản một nơi, chạy trên ERPNext thật.

Tầng khung đã kiểm các phép thuần và hai nhánh web với Frappe giả. Ở đây
chứng minh trên site dựng thật: bảng Bánh trên web có sau migrate; nút Đưa
lên web tạo đúng một thẻ cho hai size của cùng bánh; bánh Chờ ảnh bị ẩn khỏi
nhóm web; ảnh tải lên đọc từ ĐĨA của site, băm bằng Pillow thật, nên bản nén
khác (JPG nhỏ) của cùng tấm bị chặn như ca Very Berry 07/11/2026; bật Hiện
trên web thì nhóm lên lại mang đúng ảnh và mô tả của thẻ.
"""
import io
import json

import frappe

from vagabond import banh_web as bw
from vagabond import kiem_banh as kb
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la


@ca("v644 bench: bảng Bánh trên web có sau migrate, đủ ô, trạng thái đúng ba lựa chọn, không lỗi gieo")
def _():
	m = frappe.get_meta(bw.DT)
	dung("đủ ô", all(m.has_field(f) for f in ("khoa", "ten", "trang_thai", "ma_hang", "anh", "mo_ta", "tang")))
	la("ba trạng thái", m.get_field("trang_thai").options.split("\n"), list(bw.TRANG_THAI))
	la("không lỗi xếp việc gieo", frappe.db.count("Error Log", {"method": "Bánh trên web: chưa xếp được việc gieo"}), 0)


def _mon(duoi, cm, gia):
	from vagabond.khung.kiem_that import nen

	d = frappe.get_doc({"doctype": "Item", "item_code": "BAWC-KIEM-644-%s-%d" % (duoi, cm),
		"item_name": "Bánh Ổ Thử Web %s, size %dcm" % (duoi, cm),
		"item_group": nen._mot("Item Group", {"is_group": 0}), "stock_uom": nen._mot("UOM", {}),
		"is_stock_item": 0, "is_sales_item": 1, "standard_rate": gia})
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return d.name


def _anh(ten, co, kieu):
	from PIL import Image, ImageDraw
	from frappe.utils.file_manager import save_file

	a = Image.new("RGB", (400, 300), (30, 20, 20))
	d = ImageDraw.Draw(a)
	d.ellipse((60, 40, 340, 260), fill=(200, 30, 40))
	d.rectangle((150, 120, 250, 180), fill=(250, 240, 230))
	if kieu == "khac":
		a = Image.new("RGB", (400, 300), (10, 10, 60))
		d = ImageDraw.Draw(a)
		for i in range(10):
			d.rectangle((i * 40, 0, i * 40 + 20, 300), fill=(240, 200, 40))
	a = a.resize(co)
	b = io.BytesIO()
	if kieu == "JPEG":
		a.save(b, "JPEG", quality=55)
	else:
		a.save(b, "PNG")
	f = save_file(ten, b.getvalue(), None, None, is_private=0)
	_DA_TAO.append(("File", f.name))
	return f.file_url


@ca("v644 bench: Đưa lên web, ẩn khi Chờ ảnh, chặn ảnh trùng nội dung, bật hiện thì nhóm web mang đúng ảnh và mô tả")
def _():
	duoi = frappe.generate_hash(length=6)
	m12, m16 = _mon(duoi, 12, 620000), _mon(duoi, 16, 900000)
	r1 = bw.dua_len_web(m12)
	r2 = bw.dua_len_web(m16)
	ten = "Thử Web %s" % duoi
	khoa = bw.khoa_banh(ten)
	la("một thẻ cho hai size", (r1["moi"], r2["moi"], r1["khoa"], r2["khoa"]), (1, 0, khoa, khoa))
	bg = frappe.db.get_value(bw.DT, {"khoa": khoa}, ["name", "trang_thai", "ma_hang"], as_dict=True)
	_DA_TAO.append((bw.DT, bg.name))
	la("Chờ ảnh, đủ hai mã", (bg.trang_thai, bw.tach_dong(bg.ma_hang)), (bw.CHO_ANH, [m12, m16]))

	def nhom():
		return [{"ten": ten, "anh": "", "sizes": [{"ma": m12, "cm": 12, "_anh_erp": "", "_anh_dong": ""}]}]
	la("Chờ ảnh thì khách không thấy", kb._anh_noi_dung_web(nhom()), [])

	u1 = _anh("web-644-%s-a.png" % duoi, (400, 300), "PNG")
	u2 = _anh("web-644-%s-b.jpg" % duoi, (160, 120), "JPEG")
	u3 = _anh("web-644-%s-c.png" % duoi, (400, 300), "khac")
	a1 = bw.them_anh(khoa, u1)
	a2 = bw.them_anh(khoa, u2)
	a3 = bw.them_anh(khoa, u3)
	la("ảnh nén khác của cùng tấm bị chặn (băm từ tệp trên đĩa)", (a1["trung"], a2["trung"], a3["trung"]), ("", u1, ""))
	luu = json.loads(frappe.db.get_value(bw.DT, bg.name, "anh"))
	la("hai ảnh, có mã băm", ([x["url"] for x in luu], all(len(x["bam"]) == 16 for x in luu)), ([u1, u3], True))

	try:
		bw.luu(khoa, json.dumps([]), "", "", bw.DANG_HIEN)
		chan = ""
	except Exception as e:
		chan = str(e)
	dung("bật hiện mà bỏ hết ảnh bị chặn", bw.CAU_CAN_ANH in chan)
	bw.luu(khoa, json.dumps([{"url": u3}, {"url": u1}, {"url": "/files/khong-thuoc-bo.png"}]), "Mô tả web.\nDòng hai.", "Vỏ - shell", bw.DANG_HIEN)
	g = kb._anh_noi_dung_web(nhom())
	la("khách thấy, ảnh bìa theo thứ tự đã lưu, ảnh lạ không lọt", [(x["ten"], x["anh"], x["anhs"]) for x in g], [(ten, u3, [u3, u1])])
	la("mô tả và tầng của thẻ", (g[0]["mo_ta"], g[0]["tang"], g[0]["tu_web"]), ("Mô tả web. Dòng hai.", ["Vỏ - shell"], 1))
	ds = bw.ds_bien_tap()
	x = next(b for b in ds["banh"] if b["khoa"] == khoa)
	la("thẻ Bánh của trình biên tập", (x["trang_thai"], [s["cm"] for s in x["sizes"]]), (bw.DANG_HIEN, [12, 16]))
	la("trạng thái web từng mã trên màn Danh mục", bw.trang_thai_theo_ma([{"name": m16, "item_name": "Bánh Ổ Thử Web %s, size 16cm" % duoi}]),
		{m16: bw.DANG_HIEN})

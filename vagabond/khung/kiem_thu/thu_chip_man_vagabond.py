# -*- coding: utf-8 -*-
"""Ca kiểm cho chip trạng thái trên các màn danh sách riêng của Vagabond.

CA KIỂM ĐÁNG GIÁ NHẤT Ở ĐÂY LÀ CA ĐỐI CHIẾU
--------------------------------------------
Tệp vagabond_list.js chép tay tên các trạng thái để gán màu. Chỗ hỏng dễ
xảy ra nhất không phải là logic, mà là GÕ LỆCH MỘT CHỮ so với doctype
thật: viết "Cho ke toan" trong khi doctype ghi "Cho ké toán", hoặc phiên
sau thêm một trạng thái vào doctype mà quên khai màu bên này.

Cả hai kiểu hỏng đó đều KHÔNG làm màn hình vỡ, chỉ làm chip ra màu xám.
Nghĩa là không ai phát hiện được cho tới lúc có người nhìn kỹ. Đúng kiểu
hỏng lặng lẽ mà repo này đã dính nhiều lần.

Nên ca kiểm dưới đây đọc thẳng tệp JSON của từng doctype rồi so từng chữ
với bảng khai trong JS. Lệch một dấu là cổng đỏ ngay tại máy.
"""

import io
import json
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung


def _goc():
	return os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.dirname(os.path.abspath(__file__)))))


def _doc(duong):
	return io.open(os.path.join(_goc(), duong), encoding="utf-8").read()


def _bang_khai():
	"""Đọc bảng khai trong vagabond_list.js ra cấu trúc Python.

	Không dùng thư viện JS nào, chỉ bóc bằng biểu thức chính quy, vì bảng
	đó viết theo đúng một khuôn cố định. Bóc được là đủ để đối chiếu.
	"""
	js = _doc("vagabond/public/js/vagabond_list.js")
	than = js.split("var KHAI = {", 1)[1].split("\n\tfunction gan(", 1)[0]

	khai = {}
	# Mỗi khối doctype mở bằng dòng có dấu nháy đơn rồi dấu hai chấm và {
	for m in re.finditer(r"'([^']+)':\s*\{\s*truong:\s*'([^']+)',\s*mau:\s*\{(.*?)\n\t\t\},", than, re.S):
		dt, truong, than_mau = m.group(1), m.group(2), m.group(3)
		gia_tri = re.findall(r"'([^']+)':\s*'([a-z]+)'", than_mau)
		khai[dt] = {"truong": truong, "mau": dict(gia_tri)}
	return khai


def _thu_muc_doctype(ten_hien_thi):
	"""Tên thư mục doctype suy từ tên hiển thị: bỏ dấu cách, viết thường."""
	return ten_hien_thi.lower().replace(" ", "_")


def _options_cua(ten_hien_thi, truong):
	"""Đọc danh sách giá trị của một trường Select từ tệp JSON của doctype."""
	tm = _thu_muc_doctype(ten_hien_thi)
	duong = os.path.join(_goc(), "vagabond", "vagabond", "doctype", tm, tm + ".json")
	if not os.path.exists(duong):
		return None
	d = json.load(io.open(duong, encoding="utf-8"))
	for f in d.get("fields") or []:
		if f.get("fieldname") == truong:
			return [x.strip() for x in str(f.get("options") or "").split("\n") if x.strip()]
	return None


@ca("chip màn Vagabond: bảng khai bóc ra được và không rỗng")
def _boc_duoc():
	khai = _bang_khai()
	dung("bóc được bảng khai từ tệp JS", len(khai) >= 10)
	for dt, k in khai.items():
		dung("màn %s có khai tên trường trạng thái" % dt, bool(k["truong"]))
		dung("màn %s có khai màu cho ít nhất hai trạng thái" % dt, len(k["mau"]) >= 2)


@ca("chip màn Vagabond: mọi trạng thái khai trong JS phải CÓ THẬT trong doctype")
def _khai_dung_ten():
	"""Gõ lệch một chữ thì chip ra màu xám mà không ai biết. Ca này bắt.

	Cũng bắt luôn trường hợp phiên sau đổi tên một trạng thái bên doctype
	mà quên sửa bảng màu.
	"""
	khai = _bang_khai()
	for dt, k in sorted(khai.items()):
		opts = _options_cua(dt, k["truong"])
		dung("tìm thấy tệp doctype và trường %s của màn %s" % (k["truong"], dt),
			opts is not None)
		if opts is None:
			continue
		for tt in sorted(k["mau"]):
			dung("màn %s: trạng thái %r có thật trong doctype" % (dt, tt),
				tt in opts)


@ca("chip màn Vagabond: mọi trạng thái của doctype đều phải có màu")
def _khai_du_mau():
	"""Thiếu màu thì chip vẫn hiện đúng chữ nhưng ra xám, tức là mất hết
	tác dụng phân biệt. Ca này chốt để phiên sau thêm trạng thái vào
	doctype thì buộc phải khai màu luôn.
	"""
	khai = _bang_khai()
	for dt, k in sorted(khai.items()):
		opts = _options_cua(dt, k["truong"])
		if opts is None:
			continue
		for tt in opts:
			dung("màn %s: trạng thái %r đã được khai màu" % (dt, tt),
				tt in k["mau"])


@ca("chip màn Vagabond: ba luật màu, đỏ không được tràn lan")
def _luat_mau():
	"""Đỏ khắp nơi thì đỏ mất nghĩa, đúng bài học chữ "Quá hạn" cũ ở v420.

	Đỏ chỉ dành cho việc ĐANG KẸT hoặc ĐÃ HỎNG, và mỗi màn nhiều nhất hai
	trạng thái đỏ.
	"""
	khai = _bang_khai()
	for dt, k in sorted(khai.items()):
		so_do = len([1 for v in k["mau"].values() if v == "red"])
		dung("màn %s không quá hai trạng thái màu đỏ" % dt, so_do <= 2)
		dung("màn %s có ít nhất một trạng thái kết thúc màu xanh lá" % dt,
			"green" in k["mau"].values())
		mau_hop_le = set(["red", "orange", "blue", "green", "gray", "purple", "yellow"])
		for tt, m in sorted(k["mau"].items()):
			dung("màn %s: màu %r của %r là màu Frappe hiểu được" % (dt, m, tt),
				m in mau_hop_le)


@ca("chip màn Vagabond: đã nối dây và không tự tính lại nghiệp vụ")
def _noi_day():
	js = _doc("vagabond/public/js/vagabond_list.js")
	dung("gộp chứ không gán đè phần của người khác",
		"frappe.listview_settings[dt] || {}" in js)
	dung("giữ lại hàm cũ để gọi khi mình không xử lý được",
		"_vgb_ind_cu" in js and "ind_cu(doc)" in js)
	dung("có kéo về ô trạng thái", "CU.add_fields" in js)
	dung("không dùng dấu gạch dài", "—" not in js and "–" not in js)

	h = _doc("vagabond/hooks.py")
	khai = _bang_khai()
	for dt in sorted(khai):
		dung("hooks đã khai màn %s" % dt, '"%s"' % dt in h)
	dung("hooks trỏ đúng tệp chung",
		'doctype_list_js[_dt_vgb] = "public/js/vagabond_list.js"' in h)
	dung("biến tạm của vòng lặp đã được xoá, không rớt lại trong hooks",
		"del _dt_vgb" in h)

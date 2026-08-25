"""Ca kiểm tầng khung chốt lại khung KIỂM THỬ TÍCH HỢP.

Nghe vòng vo nhưng cần thiết: bộ kiểm tích hợp chỉ chạy được trên site
thật, tức là nó KHÔNG chạy ở máy chạy CI của GitHub. Nếu không có ai canh
thì một phiên vô tình xoá nó đi, đổi tên nó, hay bỏ mất lớp bảo vệ dữ liệu
mà không cổng nào kêu.

Mọi ca ở đây đọc mã nguồn BẰNG CHỮ, không import: các mô đun kia mở đầu
bằng `import frappe`, nạp chúng ở CI là nổ ngay.
"""

import ast
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))
THU_MUC = os.path.join(GOC, "vagabond", "khung", "kiem_that")


def _doc(ten):
	with open(os.path.join(THU_MUC, ten), encoding="utf-8") as f:
		return f.read()


@ca("kiem that: khung kiem thu tich hop phai con day du")
def _con_du():
	for ten in ("__init__.py", "nen.py", "cua.py", "thu_nhap_kho.py"):
		dung("còn tệp %s" % ten, os.path.exists(os.path.join(THU_MUC, ten)))


@ca("kiem that: ba lop bao ve du lieu that khong duoc mat cai nao")
def _ba_lop():
	# Mất một trong ba là chứng từ thử nằm lại trong sổ thật, hoặc một cái
	# chuông bắn vào điện thoại người thật. Chốt cứng ở đây.
	nguon = _doc("nen.py")
	dung("lớp 1: có mở điểm lưu", "frappe.db.savepoint(DIEM_LUU)" in nguon)
	dung("lớp 1: có lùi về điểm lưu",
		"frappe.db.rollback(save_point=DIEM_LUU)" in nguon)
	dung("lớp 2: có khoá tay lái giao dịch",
		"_disable_transaction_control" in nguon)
	dung("lớp 3: có bật cờ cấm gửi ra ngoài",
		"frappe.flags.vagabond_kiem_that = True" in nguon)
	dung("lớp 3: có tắt cờ lại",
		"frappe.flags.vagabond_kiem_that = False" in nguon)
	# Hàng rào sau khi chạy.
	dung("có kiểm chứng từ còn sót", "chung_tu_con_sot" in nguon)
	dung("có kiểm số lượng lệch", "so_luong_lech" in nguon)


@ca("kiem that: TUYET DOI khong duoc goi frappe.db.commit trong tang nay")
def _khong_commit():
	# Một lời gọi commit duy nhất là điểm lưu thành vô nghĩa và chứng từ ảo
	# nằm lại trong sổ thật vĩnh viễn.
	#
	# Dò bằng AST chứ không dò bằng chữ: chú thích trong chính các tệp đó
	# có nhắc tên `frappe.db.commit` để dặn người sau, dò bằng chữ thì ca
	# kiểm đỏ vì đúng lời dặn của mình.
	for ten in ("nen.py", "cua.py", "thu_nhap_kho.py"):
		cay = ast.parse(_doc(ten))
		goi = [n for n in ast.walk(cay)
			if isinstance(n, ast.Call)
			and isinstance(n.func, ast.Attribute)
			and n.func.attr == "commit"]
		la("%s số lời gọi commit" % ten, len(goi), 0)


@ca("kiem that: duong gui thong bao phai ton trong co cam gui ra ngoai")
def _thong_bao_ton_trong_co():
	tep = os.path.join(GOC, "vagabond", "thong_bao.py")
	with open(tep, encoding="utf-8") as f:
		nguon = f.read()
	dung("thong_bao.gui đọc cờ kiểm thật",
		'frappe.flags.get("vagabond_kiem_that")' in nguon)


@ca("kiem that: duong gui tin Zalo phai ton trong co cam gui ra ngoai")
def _zalo_ton_trong_co():
	# Sinh ra 25/08/2026. Soi lại thì `thong_bao.py` có cửa này còn `zalo.py`
	# thì KHÔNG, suốt từ 06/08/2026. Nghĩa là chạy bộ kiểm thử tích hợp trên
	# site thật thì chuông đẩy bị chặn, còn tin ZNS vẫn bay ra ngoài.
	#
	# Ba đường đang gọi zalo.gui_tin: dang_nhap.py, diem_otp.py và
	# thanh_toan.py. Đường thứ ba gửi tin yêu cầu khách chuyển tiền. Một lần
	# chạy kiểm thử là một lần khách thật nhận tin đòi tiền cho một đơn không
	# có thật.
	#
	# Cửa phải nằm trong CHÍNH `gui_tin` chứ không nằm ở từng nơi gọi, nên ca
	# kiểm đọc luôn thân hàm đó bằng AST: chặn kiểu "có chuỗi ấy đâu đó trong
	# tệp" thì một dòng chú thích nhắc tên cờ cũng làm ca kiểm xanh giả.
	tep = os.path.join(GOC, "vagabond", "zalo.py")
	with open(tep, encoding="utf-8") as f:
		nguon = f.read()
	than = ""
	for nut in ast.walk(ast.parse(nguon)):
		if isinstance(nut, ast.FunctionDef) and nut.name == "gui_tin":
			than = ast.dump(nut)
	dung("zalo.py còn hàm gui_tin", bool(than))
	dung("zalo.gui_tin đọc cờ kiểm thật", "vagabond_kiem_that" in than)


@ca("kiem that: bo ca kiem phai duoc nap trong cua, khong bo quen bo nao")
def _nap_du_bo():
	nguon = _doc("cua.py")
	co_tep = sorted(x for x in os.listdir(THU_MUC)
		if x.startswith("thu_") and x.endswith(".py"))
	for ten in co_tep:
		mo_dun = ten[:-3]
		dung("cửa có nạp %s" % mo_dun,
			("import %s" % mo_dun) in nguon)


@ca("kiem that: ca kiem chot vu 3311 phai con nguyen")
def _con_ca_3311():
	# Ca kiểm sinh ra từ sự cố ngày 21/08/2026. Xoá nó đi là mở lại đúng cái
	# cửa đã làm cả tiệm không nhập được hàng.
	nguon = _doc("thu_nhap_kho.py")
	dung("còn ca ghi sổ phiếu nhập thật", "phieu_nhap_ao" in nguon)
	dung("còn ca chốt dòng tài khoản chờ không có đối tác",
		"khong_duoc_co_doi_tac" in nguon.replace("-", "_")
		or "không được có đối tác" in nguon)
	dung("còn ca chốt không ghi đè lớp",
		"override_doctype_class" in nguon)

"""v585: ô Link Warehouse do app tự thêm phải bỏ qua User Permission.

Ca thật 08/10/2026: người có quyền theo kho tìm "Chocolatine" không ra
"Bánh Chocolatine, Mini size" vì món khai "Kho nguyên liệu mặc định khi sản
xuất" ngoài danh sách kho của họ. Frappe áp User Permission lên MỌI ô Link
tới doctype bị giới hạn, kể cả ô chỉ để cấu hình. Đường chạy thật có ca bench
thu_kho_quyen_585 (người dùng thường, quyền một kho, gọi cửa tim). Ở tầng này
chốt điều không chạy được ngoài site: mọi khai báo ô Link Warehouse trong mã
nguồn app đều có cờ, kể cả ô thêm sau này.
"""
import ast
import os

from vagabond import kho_san_xuat, san_xuat_desktop
from vagabond.khung.kiem_thu.nen import ca, dung, la

_GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_BO_QUA = {"kiem_thu", "kiem_that", "bench_thu", "staging"}


def _o_link_kho():
	ra = []
	for goc, thu_muc, tep in os.walk(_GOC):
		thu_muc[:] = [t for t in thu_muc if t not in _BO_QUA]
		for t in tep:
			if not t.endswith(".py"):
				continue
			p = os.path.join(goc, t)
			for n in ast.walk(ast.parse(open(p, encoding="utf-8").read())):
				if not isinstance(n, ast.Dict):
					continue
				kv = {k.value: (v.value if isinstance(v, ast.Constant) else "?")
					for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant)}
				if kv.get("fieldtype") == "Link" and kv.get("options") == "Warehouse":
					ra.append((os.path.relpath(p, _GOC), n.lineno, kv.get("ignore_user_permissions")))
	return ra


@ca("v585: ô kho cấu hình trên Item và Warehouse bỏ qua User Permission, không ẩn món với người có quyền theo kho")
def _():
	o = san_xuat_desktop.TRUONG_MOI["Item"][0]
	la("Item.custom_kho_nguyen_lieu_sx", (o["fieldname"], o.get("ignore_user_permissions")),
		("custom_kho_nguyen_lieu_sx", 1))
	kho = {d["fieldname"]: d.get("ignore_user_permissions") for d in kho_san_xuat.TRUONG_MOI["Warehouse"]
		if d.get("options") == "Warehouse"}
	la("Warehouse.custom_kho_nguon và kho nguồn phụ", kho, {"custom_kho_nguon": 1, "custom_kho_nguon_phu": 1})
	ds = _o_link_kho()
	# Chốt số ô đã dò lớn hơn 0 để ca không xanh khi phép dò hụt (bài học v584).
	dung("dò thấy ít nhất 3 ô Link Warehouse trong mã nguồn (được %d)" % len(ds), len(ds) >= 3)
	thieu = [x for x in ds if x[2] != 1]
	la("mọi ô Link Warehouse đều có ignore_user_permissions", thieu, [])

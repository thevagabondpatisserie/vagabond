# -*- coding: utf-8 -*-
"""#469: xuất BOM, dịch lịch sử và quyền thật của Khải, Linh.

Sự cố gốc có hai mặt: bảng khai triển làm Version nhiễu, còn đường ghi cờ
bằng db.set_value lại không có Version. Các ca này chốt bộ lọc nhiễu, vai,
cửa API và hành vi ẩn nút ở mã JS thật.
"""
import io
import os
import subprocess
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu import nen
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

nen.gia_lap()
from vagabond import cong_thuc as ct
from vagabond.vai_cua_hang import VAI_BAR, VAI_QLCT

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS = os.path.join(GOC, "public", "js", "bep", "26-cong-thuc.js")


def _vai(ds):
	return patch.object(ct.frappe, "get_roles", lambda *a: ds, create=True)


@ca("#469: Khải và Linh xuất được, ba bộ vai ngoài gọi thẳng bị chặn")
def _():
	khai = ["Accounts Manager", "Manufacturing User", "Stock Manager", "Stock User", VAI_QLCT]
	linh = ["Manufacturing Manager", "Manufacturing User", "Bếp phó"]
	for ds in (khai, linh):
		with _vai(ds):
			ct._kiem_xuat()
	for ds in (["Bếp phó"], [VAI_BAR], ["Stock User"]):
		with _vai(ds):
			nem("API chặn %s" % ds, ct._kiem_xuat, Exception)


@ca("#469: Version thật bỏ exploded_items và dịch đúng lượng nguyên liệu")
def _():
	du_lieu = {
		"added": [["exploded_items", {"item_code": "NVL-NHIEU", "qty": 99}]],
		"row_changed": [["items", 0, "ROW-1", [
			["item_name", None, "Đường"], ["uom", None, "G"], ["qty", 120, 150]
		]]],
	}
	la("chỉ còn một câu nghiệp vụ", ct.dich_version(du_lieu), ["Đổi Đường 120 thành 150 G"])
	dung("không lọt tên bảng nhiễu", "exploded" not in " ".join(ct.dich_version(du_lieu)))


@ca("#469: thêm và bỏ nguyên liệu được dịch bằng tên, lượng, đơn vị")
def _():
	d = {"added": [["items", {"item_name": "Whipping cream Lescure", "qty": 600, "uom": "ML"}]],
		"removed": [["items", {"item_code": "NVLT00001", "qty": 2, "uom": "G"}]]}
	la("hai câu", ct.dich_version(d),
		["Thêm Whipping cream Lescure 600 ML", "Bỏ NVLT00001 2 G"])


@ca("#469: hành vi Node chốt nút Excel chỉ hiện cho đúng vai")
def _():
	ma = r'''
const fs=require('fs'),vm=require('vm');
const src=fs.readFileSync(process.argv[1],'utf8');
let roles=[]; const box={hasRole:r=>roles.includes(r),console,setTimeout,clearTimeout};
vm.createContext(box); vm.runInContext(src,box);
function q(r){roles=r;return box.ctGhiSoDuoc();}
const k=q(['VGB - Quản lý công thức']),l=q(['Manufacturing Manager']);
const ngoai=[q(['Bếp phó']),q(['Quầy Bar']),q(['Stock User'])];
if(!k||!l||ngoai.some(Boolean)) process.exit(3);
if(!src.includes("ctGhiSoDuoc() ? '<button")||!src.includes('id="ctExcel"')) process.exit(4);
'''
	r = subprocess.run(["node", "-e", ma, JS], check=False, capture_output=True, text=True)
	la("node chạy hành vi quyền và nút", r.returncode, 0)


@ca("#469: Excel theo đúng trạng thái, mã là chữ và số lượng là số")
def _():
	def doc(ten):
		n = 1 if ten == "BOM-A" else 2
		return types.SimpleNamespace(name=ten, item="0000%s" % n, item_name="Món %s" % n,
			docstatus=1, is_active=1, is_default=1, quantity=n, uom="Cái",
			total_cost=100 * n, owner="a@x", modified_by="b@x", modified="2026-10-13",
			items=[types.SimpleNamespace(item_code="000NVL%s" % n, item_name="NVL", qty=1.5 * n,
				uom="G", rate=10, amount=15 * n)])

	cac_bang = []
	def ds(_tab, tt, *_a, **_k):
		return {"ds": [{"bom": "BOM-A"}] if tt == "dang_dung" else
			[{"bom": "BOM-A"}, {"bom": "BOM-B"}]}

	import frappe.utils.xlsxutils as xl
	with patch.object(ct, "danh_sach", ds), \
			patch.object(ct.frappe, "get_doc", lambda _dt, ten: doc(ten)), \
			patch.object(xl, "make_xlsx", lambda bang, _ten: cac_bang.append(bang) or b"xlsx"):
		with _vai(["Manufacturing Manager"]):
			a = ct.xuat_excel(trang_thai="dang_dung")
			b = ct.xuat_excel(trang_thai="ban_cu")
	la("đang dùng có một dòng", a["so_dong"], 1)
	la("đổi trạng thái thành hai dòng", b["so_dong"], 2)
	dong = cac_bang[0][3]
	dung("mã món giữ dạng chữ có số 0 đầu", isinstance(dong[0], str) and dong[0].startswith("0"))
	dung("mã NVL giữ dạng chữ", isinstance(dong[6], str))
	dung("số lượng là số", isinstance(dong[8], float))
	dung("đầu tệp ghi bộ lọc", cac_bang[0][0][0].startswith("Bộ lọc:"))


@ca("#469: điều 17 chỉ bày tối đa ba câu rồi đếm phần còn lại")
def _():
	src = io.open(JS, encoding="utf-8").read()
	la("chi tiết giới hạn ba câu", src.count("x.cau.slice(0, 3)"), 1)
	la("nhật ký giới hạn hai câu", src.count("x.cau.slice(0, 2)"), 1)
	dung("cả hai chỗ đều báo số còn lại", src.count("thay đổi nữa") == 2)


@ca("#469: ghi sổ bù Comment cho cả bản mới và bản cũ")
def _():
	src = io.open(os.path.join(GOC, "cong_thuc.py"), encoding="utf-8").read()
	i = src.index("def ghi_so(")
	than = src[i:src.index("\n\n@frappe.whitelist()", i)]
	la("hai đường ghi Comment", than.count(".add_comment("), 2)
	dung("câu trên bản mới nói bản bị thay", '"Ghi sổ%s."' in than)
	dung("câu trên bản cũ nói bản mới", 'đã ghi sổ thay công thức này' in than)


@ca("#469: Excel chuyển đủ bộ lọc hướng dẫn tới cùng nguồn danh sách")
def _():
	import frappe.utils.xlsxutils as xl
	with _vai(["Manufacturing Manager"]), patch.object(ct, "danh_sach", return_value={"ds": []}) as ds, \
			patch.object(xl, "make_xlsx", return_value=b"xlsx"):
		ct.xuat_excel(tab="baker", trang_thai="ban_cu", tim="brioche", huong_dan="lech", chang="btp")
		ds.assert_called_once_with("baker", "ban_cu", "brioche", "lech", "btp", _tat_ca=True)


@ca("#469: BOM đã xoá đọc bản lưu, không gọi get_doc và không phục hồi")
def _():
	import json
	from types import SimpleNamespace as NS
	data = json.dumps({"doctype": "BOM", "name": "BOM-X", "item": "MON-X", "item_name": "Món X",
		"quantity": 2, "uom": "Cái", "items": [{"item_code": "NVL-X", "qty": 20, "uom": "Gram"}]})
	with _vai(["Manufacturing Manager"]), patch.object(ct.frappe.db, "get_value", return_value=NS(data=data)) as get, \
			patch.object(ct.frappe, "get_doc", side_effect=AssertionError("không gọi BOM đã xoá")):
		d = ct.ban_da_xoa("DEL-X")
		la("đúng bản", d["bom"], "BOM-X")
		la("đủ nguyên liệu", d["dong"][0]["sl"], 20)
		la("chỉ Deleted Document của BOM", get.call_args[0][1], {"name": "DEL-X", "deleted_doctype": "BOM"})
	la("không lộ chứng từ khác", ct._ban_da_xoa('{"doctype":"Payment Entry"}'), None)


@ca("#469: ghi BOM trực tiếp và Comment cùng request, lỗi Comment phải nổi lên")
def _():
	from vagabond import lich_su_bom as ls
	from unittest.mock import Mock
	doc = Mock()
	with patch.object(ls.frappe.db, "get_value", return_value={"is_active": 1}), \
			patch.object(ls.frappe.db, "set_value") as ghi, patch.object(ls.frappe, "get_doc", return_value=doc):
		ls.dat_bom("BOM", "BOM-X", "is_active", 0, nguon="Dọn bếp", update_modified=False)
		ghi.assert_called_once_with("BOM", "BOM-X", "is_active", 0, update_modified=False)
		cau = doc.add_comment.call_args[0][1]
		dung("nguồn và giá trị cũ mới", "Dọn bếp" in cau and "Bật thành Tắt" in cau and ls.frappe.session.user in cau)
		doc.add_comment.side_effect = RuntimeError("hỏng comment")
		nem("không nuốt lỗi", lambda: ls.dat_bom("BOM", "BOM-X", "is_active", 0, nguon="Dọn bếp"), RuntimeError)


@ca("#469: Version và bản xoá BOM được giữ ngoài lịch dọn")
def _():
	from vagabond import don_dep_db as dd
	dung("giữ BOM", "BOM" in dd.KHONG_DUOC_DON)
	dung("giữ dòng BOM", "BOM Item" in dd.KHONG_DUOC_DON)


@ca("#469: DOM lịch sử và nhật ký 0, 1, nhiều dòng, tải, lỗi và bản xoá")
def _():
	r = subprocess.run(["node", os.path.join(GOC, "khung", "kiem_thu", "hanh_vi", "bom_469.js")], capture_output=True, text=True)
	la("DOM chạy qua màn thật: " + r.stdout + r.stderr, r.returncode, 0)


@ca("#469: core Version chỉ đổi qty vẫn hiện tên và đơn vị dòng")
def _():
	# Core f33ac3f: (table, index, child.name, changed); tên/UOM không đổi không nằm trong diff.
	la("dùng metadata dòng", ct.dich_version({"row_changed": [["items", 0, "R1", [["qty", 120, 150]]]]},
		{"R1": {"item_name": "Đường", "uom": "G"}}), ["Đổi Đường 120 thành 150 G"])


@ca("#469: nhật ký có công thức đã xoá dù không còn BOM sống")
def _():
	from types import SimpleNamespace as NS
	import json
	def rows(dt, **kw):
		if dt == "Deleted Document":
			la("lọc đúng loại", kw["filters"]["deleted_doctype"], "BOM")
			return [NS(name="DEL-X", deleted_name="BOM-X", owner="linh", creation="2026-10-13",
				data=json.dumps({"doctype":"BOM", "name":"BOM-X", "item":"M", "item_name":"Món"}))]
		return []
	with _vai(["Manufacturing Manager"]), patch.object(ct.frappe, "get_all", rows), \
			patch.object(ct.frappe.db, "get_value", return_value="Linh"):
		kq = ct.nhat_ky(tu_ngay="2026-10-01", den_ngay="2026-10-13")
		la("đúng dòng xoá", kq["ds"][0]["da_xoa"], "DEL-X")
		la("đúng tên món", kq["mon"], [("M", "Món")])
		la("lọc món không khớp", ct.nhat_ky(mon="KHAC")["ds"], [])


@ca("#469: đường dọn thật gửi điều kiện loại BOM khỏi DELETE Version")
def _():
	from vagabond import don_dep_db as dd
	from unittest.mock import Mock
	db = Mock()
	with patch.object(dd.frappe, "db", db), patch.object(dd, "_so_dong_vua_xoa", return_value=0):
		dd.don_mot_bang("Version", lo=1)
		sql, args = db.sql.call_args[0]
		dung("có NOT IN loại doctype", "`ref_doctype` not in %s" in sql)
		dung("tham số thực giữ BOM", "BOM" in args[1] and "BOM Item" in args[1])


@ca("#594: quyền chặn ngay API Excel và nhật ký trước khi đọc dữ liệu")
def _():
	import frappe.utils.xlsxutils as xl
	for api in (ct.xuat_excel, ct.nhat_ky):
		with _vai(["Sales User"]), patch.object(ct.frappe, "get_all", return_value=[]), \
				patch.object(ct, "danh_sach", return_value={"ds": []}), \
				patch.object(xl, "make_xlsx", return_value=b"xlsx"):
			# Không mock helper quyền: bỏ lời gọi helper ở API phải làm ca này đỏ.
			nem(api.__name__, api, Exception)


@ca("#594: Excel Tất cả giữ null và ghi đúng bộ lọc")
def _():
	import frappe.utils.xlsxutils as xl
	bang = []
	with _vai(["Manufacturing Manager"]), patch.object(ct, "danh_sach", return_value={"ds": []}) as ds, \
			patch.object(xl, "make_xlsx", side_effect=lambda b, _: bang.append(b) or b"xlsx"):
		ct.xuat_excel(trang_thai=None)
		ds.assert_called_once_with(None, None, None, None, None, _tat_ca=True)
		dung("đầu tệp Tất cả", "trạng thái=tất cả;" in bang[0][0][0])


@ca("#594: Comment ghi thẳng dịch nhãn, bỏ giá vốn, đọc lại không escape hai lần")
def _():
	from vagabond import lich_su_bom as ls
	from unittest.mock import Mock
	from types import SimpleNamespace as NS
	doc = Mock()
	with patch.object(ls.frappe.db, "get_value", return_value={"custom_chang": "Bánh & kem", "total_cost": 10}), \
			patch.object(ls.frappe.db, "set_value"), patch.object(ls.frappe, "get_doc", return_value=doc):
		ls.dat_bom("BOM", "B", {"custom_chang": "BTP <mới>", "total_cost": 20}, nguon="Đổi & kiểm")
		noi = doc.add_comment.call_args[0][1]
		dung("nhãn Việt", "Chặng sản xuất:" in noi and "custom_chang" not in noi)
		dung("bỏ giá vốn", "total_cost" not in noi and "10 thành 20" not in noi)
		dung("lưu HTML an toàn", "&lt;mới&gt;" in noi)
		doc.reset_mock()
		ls.dat_bom("BOM", "B", {"total_cost": 20, "raw_material_cost": 20,
			"base_total_cost": 20, "base_raw_material_cost": 20}, nguon="Máy tính lại")
		doc.add_comment.assert_not_called()
	def rows(dt, **kw):
		return [NS(reference_name="B", owner="u", creation="2026-10-13", content=noi)] if dt == "Comment" else []
	with patch.object(ct.frappe, "get_all", rows), patch.object(ct, "_ten_nguoi", return_value={"u": "U"}):
		cau = ct._lich_su_cua(["B"])[0]["cau"][0]
		dung("chỉ giải mã một lần để UI tự escape", "Đổi & kiểm" in cau and "Bánh & kem" in cau and "BTP <mới>" in cau)
		dung("không còn entity", "&amp;" not in cau)


@ca("#595 lịch sử BOM dùng chữ cho mọi ô Check, chuỗi 0 không thành Có")
def _():
	from vagabond import lich_su_bom as ls
	from unittest.mock import Mock
	doc = Mock()
	with patch.object(ls.frappe.db, "get_value", return_value={"is_active": "0", "is_default": 1, "is_phantom_bom": 0}), \
			patch.object(ls.frappe.db, "set_value"), patch.object(ls.frappe, "get_doc", return_value=doc):
		ls.dat_bom("BOM", "B", {"is_active": 1, "is_default": "0", "is_phantom_bom": "1"}, nguon="Máy cập nhật")
		cau = doc.add_comment.call_args[0][1]
		for chu in ("Đang dùng: Tắt thành Bật", "Mặc định: Có thành Không", "Công thức ảo: Không thành Có"):
			dung(chu, chu in cau)
		doc.reset_mock()
		ls.dat_bom("BOM", "B", {"is_active": 0, "is_default": "1", "is_phantom_bom": "0"}, nguon="Máy cập nhật")
		doc.add_comment.assert_not_called()

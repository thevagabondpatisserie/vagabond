# -*- coding: utf-8 -*-
"""Danh mục công thức BOM trên app, cho bếp trưởng (anh Việt giao 21/08/2026).

Bếp trưởng cần một chỗ trên điện thoại để xem, tạo và sửa công thức mà
không phải mở Desk. Ba tab theo nơi làm: Bánh Pastry, Bánh Baker, Quầy
Bar; kèm ô tìm và chip lọc trạng thái.

CÁCH LÀM PHIÊN BẢN, ghi rõ vì đề bài nói "Cancel bản cũ" mà em làm khác:
ERPNext TỪ CHỐI cancel một BOM đã có lệnh sản xuất trỏ vào (linked
documents), nên đường cancel chỉ chạy được với công thức chưa ai dùng,
tức là vô dụng đúng lúc cần. Đường chuẩn của ERPNext, và là đường ở đây:

    Điều chỉnh  ->  tạo BẢN NHÁP sao chép từ bản đang chạy, trỏ ngược
                    về bản gốc qua ô custom_ban_truoc
    Ghi sổ      ->  bản mới thành mặc định; bản cũ BỎ mặc định và TẮT
                    hoạt động - biến khỏi ô chọn khi tạo lệnh nhưng vẫn
                    nằm nguyên trong sổ, tra lại được trọn lịch sử (QT-20)

Chuỗi phiên bản lần ngược qua custom_ban_truoc, không cần đánh số."""

# ------------------------------------------------------------ phần thuần

TRANG_THAI = ("nhap", "dang_dung", "ban_cu", "da_huy")

# Từ khoá suy bếp từ tên món, dùng khi món chưa khai Bếp phụ trách.
# Từ khoá Baker xét TRƯỚC: "Croissant Tart" là vỏ cuộn của Baker đem ráp,
# xét ngược lại là gán nhầm sang Pastry.
TU_BAKER = ("croissant", "brioche", "chocolatine", "shokupan", "shiopan",
	"danish", "foccacia", "focaccia", "bánh mì", "epi", "suisse")
TU_PASTRY = ("cheesecake", "verrine", "canelé", "canele", "mille crepe",
	"tuile", "slice", "hũ ", "bánh ổ", "tart", "entremet", "mousse",
	"sponge", "biscuit", "custard", "ganache", "compote", "confit",
	"glaze", "crumble", "crunchy")
TU_BAR = ("trà ", "cà phê", "coffee", "matcha latte", "cacao", "sữa hạt",
	"kem ", "ice cream", "đá xay", "sinh tố", "nước ép")


def trang_thai_bom(docstatus, is_active, is_default):
	"""Một BOM đang ở trạng thái nào theo cách bếp gọi. THUẦN."""
	ds = int(docstatus or 0)
	if ds == 0:
		return "nhap"
	if ds == 2:
		return "da_huy"
	if int(is_active or 0) and int(is_default or 0):
		return "dang_dung"
	return "ban_cu"


def phan_tab(nhom_nuoc, bep_phu_trach, ten):
	"""Món này thuộc tab nào: pastry, baker, bar hay khac. THUẦN.

	Ưu tiên theo thứ tự chắc chắn giảm dần: nhóm hàng thuộc nhánh Nước là
	Quầy Bar; ô Bếp phụ trách đã khai thì nghe theo; còn lại đoán qua tên.
	"""
	if nhom_nuoc:
		return "bar"
	b = (bep_phu_trach or "").strip()
	if b == "Bếp Pastry":
		return "pastry"
	if b == "Bếp Baker":
		return "baker"
	t = (ten or "").lower()
	if any(k in t for k in TU_BAKER):
		return "baker"
	if any(k in t for k in TU_PASTRY):
		return "pastry"
	if any(k in t for k in TU_BAR):
		return "bar"
	return "khac"


def duoi_phien_ban(ten_bom):
	"""Duoi so phien ban cua mot ma BOM. THUAN.

	ERPNext dat ten BOM kieu `BOM-BTPB00007-002`, duoi la so phien ban. Ban
	Khai 25/08/2026: *"Anh chinh keo rong cai nay giup em de em xem cai
	phien ban BOM"*. Danh sach tren Desk cat mat duoi do vi cot hep.

	Rut rieng ra thanh mot chuoi ngan de gan vao CHIP trang thai, cho ma
	chip thi khong bao gio bi cat. Rong khi ten khong co duoi so - luc do
	man hinh khong hien gi ca chu khong hien so 0 gia.
	"""
	t = str(ten_bom or "").strip()
	if "-" not in t:
		return ""
	duoi = t.rsplit("-", 1)[-1]
	return duoi if (duoi.isdigit() and duoi) else ""


def khop_tim(tim, ma, ten):
	"""Dòng có khớp ô tìm kiếm không. THUẦN, không phân biệt hoa thường."""
	t = (tim or "").strip().lower()
	if not t:
		return True
	return t in (ma or "").lower() or t in (ten or "").lower()


def tab_dang_loc(tab, tim):
	"""Tab thực sự đang lọc, sau khi cân nhắc ô tìm. THUẦN.

	Gõ chữ vào ô tìm là muốn tìm CẢ TIỆM, không phải tìm trong một tab.

	Ca thật 26/08/2026: anh Việt đứng ở tab Pastry gõ "Sable", màn báo
	"không có công thức nào khớp bộ lọc". Công thức Sable vẫn còn nguyên,
	nhưng nó nằm ở tab "Chưa phân" vì món chưa khai ô Bếp phụ trách và cái
	tên không chứa từ khoá nào để đoán ra. Người dùng không có cách nào biết
	điều đó, và kết luận là công thức đã mất.

	95 trên 382 công thức đang nằm ở "Chưa phân", nên đây không phải ca hiếm.
	"""
	return "" if (tim or "").strip() else (tab or "")


# ------------------------------------------------------- phần cần Frappe

import base64
import io
import json
import re

import frappe
from frappe.utils import add_days, cint, flt, get_datetime, now_datetime, nowdate

# Ô mới trên BOM: trỏ về bản trước trong chuỗi phiên bản.
#
# Ô "Note" trên DÒNG nguyên liệu thêm 25/08/2026. Bạn Khải xin: *"Trong BOM
# customize thêm 1 cột giúp em, tiêu đề Note: để ghi chú ạ"*. Chỗ dùng thật
# là ghi tính chất nguyên liệu mà con số không nói được, ví dụ dòng trứng
# ghi "Nguyên quả" để phân biệt với công thức chỉ lấy lòng trắng.
#
# `in_list_view` để ô hiện thẳng trong lưới, không phải mở từng dòng ra mới
# thấy. `columns` là bề rộng trong lưới, tính theo thang 10 của Frappe: bốn
# cột sẵn có của BOM Item đang chiếm 8, nên lấy 2 là vừa khít, lấy hơn thì
# Frappe đẩy cột cuối rơi xuống dòng dưới.
#
# Small Text chứ không phải Data: ghi chú chế biến hay dài hơn một dòng, mà
# Data thì cắt ở 140 ký tự không báo gì.
TRUONG_MOI = {
	"BOM": [{
		"fieldname": "custom_ban_truoc", "label": "Bản trước",
		"fieldtype": "Link", "options": "BOM", "read_only": 1,
		"insert_after": "item_name", "description":
			"Bản công thức mà bản này điều chỉnh từ đó. Lần ngược ô này là ra "
			"trọn lịch sử phiên bản.",
	}],
	"BOM Item": [{
		"fieldname": "custom_note", "label": "Note",
		"fieldtype": "Small Text", "insert_after": "uom",
		"in_list_view": 1, "columns": 2, "translatable": 0,
		"description":
			"Ghi chú tính chất của nguyên liệu ở dòng này, ví dụ nguyên quả, "
			"chỉ lấy lòng trắng, để lạnh, rây mịn. Chữ ở đây chảy sang màn "
			"Danh mục công thức và bản in Hướng dẫn chế biến.",
	}],
}


def _vai_xem():
	from vagabond.vai_cua_hang import VAI_BAR, VAI_QLCT

	return {"Manufacturing User", "Manufacturing Manager", "System Manager",
		"Giám đốc", "AP Giám đốc", "Bếp phó", VAI_BAR, VAI_QLCT}


def _vai_soan():
	"""Ai được TẠO và SỬA BẢN NHÁP. Anh Việt chốt 16/09/2026."""
	from vagabond.vai_cua_hang import VAI_BAR

	return _vai_ghi_so() | {"Bếp phó", VAI_BAR}


def _vai_ghi_so():
	"""Ai được GHI SỔ, tức chốt bản đang dùng. Hẹp hơn hẳn cửa soạn.

	Ghi sổ là lúc công thức bắt đầu quyết giá vốn và nổ Lệnh sản xuất, nên
	giữ nguyên bộ vai cũ. Bếp phó và Quầy Bar soạn nháp, bếp trưởng chốt.
	"""
	from vagabond.vai_cua_hang import VAI_QLCT

	return {"Manufacturing Manager", "System Manager", "Giám đốc",
		"AP Giám đốc", VAI_QLCT}


def _kiem_xem():
	if not _vai_xem() & set(frappe.get_roles()):
		frappe.throw("Màn Danh mục công thức dành cho bếp, quầy bar và quản lý sản xuất.")


def _kiem_soan():
	# VAI_QLCT them 25/08/2026. Ban Khai la ke toan gia thanh, nguoi nam
	# cong thuc va gia von, nhung chi co `Manufacturing User` nen mo duoc
	# man ma khong sua duoc. Tren Desk ban ay von SUA DUOC tu truoc (vai
	# do da co quyen ghi tren doctype BOM), cho ket chi la man nay.
	#
	# 16/09/2026 mo them `Bep pho` va `Quay Bar`: ho soan duoc ban nhap,
	# khong ghi so duoc. Xem `_vai_ghi_so`.
	if not _vai_soan() & set(frappe.get_roles()):
		frappe.throw(
			"Màn này chỉ bếp và quầy bar soạn công thức được. "
			"Anh chị cần sửa thì nhờ bếp trưởng mở quyền.")


def _kiem_ghi_so():
	if not _vai_ghi_so() & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ bếp trưởng (Manufacturing Manager) hoặc giám đốc mới ghi sổ "
			"công thức. Anh chị cứ lưu bản nháp rồi nhờ bếp trưởng chốt.")


def _nhom_nuoc():
	"""Các nhóm hàng thuộc nhánh Nước, tính cả cây con."""
	ra = set()
	goc = [g.name for g in frappe.get_all("Item Group",
		filters={"name": ["in", ["Thành phẩm Nước", "Bán thành phẩm Nước"]]},
		fields=["name"])]
	con = frappe.get_all("Item Group", fields=["name", "parent_item_group"],
		limit_page_length=0)
	cha = {x.name: x.parent_item_group for x in con}
	for g in cha:
		x = g
		for _ in range(6):
			if x in goc:
				ra.add(g)
				break
			x = cha.get(x) or ""
			if not x:
				break
	ra.update(goc)
	return ra


from vagabond.ton_chang import chang_cua_nhan, ten_chang


def ten_chang_gom(nhan):
	"""Nhãn chặng cũ hiện lên màn hình bằng tên đã gom. Rỗng thì để rỗng.

	Khải chốt 28/08/2026: năm nhãn cũ gom còn hai tên cho phần bán thành
	phẩm. Bảng gom nằm ở `ton_chang`, đây chỉ gọi sang - để hai chỗ không
	nói hai câu khác nhau về cùng một công thức.
	"""
	c = chang_cua_nhan(nhan)
	return ten_chang(c) if c else ((nhan or "").strip())


@frappe.whitelist()
def danh_sach(tab=None, trang_thai=None, tim=None, huong_dan=None, chang=None,
		_tat_ca=False):
	"""Toàn bộ công thức, gắn tab và trạng thái, lọc tại máy chủ.

	`chang` lọc theo chặng ĐÃ GOM, không phải nhãn cũ. Bấm chip "BTP sơ
	cấp" thì ra cả công thức ghi "BTP thành phần" lẫn công thức ghi "Ruột
	bánh (C1)" - đó chính là ý của việc gom.
	"""
	_kiem_xem()
	boms = frappe.get_all(
		"BOM",
		fields=["name", "item", "item_name", "docstatus", "is_active",
			"is_default", "quantity", "uom", "custom_chang",
			"custom_ban_truoc", "modified"],
		order_by="modified desc", limit_page_length=0 if _tat_ca else 1200)
	cac_ma = sorted({b.item for b in boms})
	meta = {}
	for i in range(0, len(cac_ma), 300):
		for it in frappe.get_all("Item",
				filters={"name": ["in", cac_ma[i:i + 300]]},
				fields=["name", "item_name", "item_group",
					"custom_bep_phu_trach"], limit_page_length=0):
			meta[it.name] = it
	nuoc = _nhom_nuoc()
	# Go chu vao o tim thi bo loc tab - xem tab_dang_loc.
	tab_loc = tab_dang_loc(tab, tim)
	theo_tab = {}
	ra = []
	for b in boms:
		it = meta.get(b.item) or {}
		ten = it.get("item_name") or b.item_name or b.item
		t = phan_tab(it.get("item_group") in nuoc,
			it.get("custom_bep_phu_trach"), ten)
		tt = trang_thai_bom(b.docstatus, b.is_active, b.is_default)
		if tab_loc and t != tab_loc:
			continue
		if trang_thai and tt != trang_thai:
			continue
		if not khop_tim(tim, b.item, ten):
			continue
		if chang and chang_cua_nhan(b.custom_chang) != chang:
			continue
		theo_tab[t] = theo_tab.get(t, 0) + 1
		ra.append({"bom": b.name, "ma": b.item, "ten": ten, "tab": t,
			"trang_thai": tt, "so_luong": b.quantity, "dvt": b.uom,
			"chang": ten_chang_gom(b.custom_chang),
			"ban_truoc": b.custom_ban_truoc or "",
			"phien_ban": duoi_phien_ban(b.name),
			"sua_luc": str(b.modified)[:16]})
	# Gan tinh trang huong dan che bien len tung the. Mot truy van cho ca
	# danh sach chu khong hoi tung mon: 378 cong thuc thi hoi tung mon la
	# 378 lan chay vong xuong co so du lieu.
	_gan_huong_dan(ra)
	if huong_dan == "lech":
		# "Cong thuc da doi" khong phai mot tinh trang thu tu, no la mot CO
		# gan them: mon van co huong dan, nhung huong dan do soan theo mot
		# ban cong thuc khac ban dang dung. Nen loc rieng chu khong so bang.
		ra = [x for x in ra if x.get("hd_lech")]
	elif huong_dan:
		ra = [x for x in ra if x.get("huong_dan") == huong_dan]
	if huong_dan:
		# Hai bo loc tren da cat bot danh sach nen bang dem phai dem lai,
		# khong thi con so hien ra to hon danh sach that.
		theo_tab = {}
		for x in ra:
			theo_tab[x["tab"]] = theo_tab.get(x["tab"], 0) + 1
	return {"ds": ra if _tat_ca else ra[:400], "tong": len(ra), "theo_tab": theo_tab,
		"bo_loc_tab": 1 if (tab and not tab_loc) else 0}


def _so_dep(x):
	"""Số trong câu lịch sử, không để đuôi .0 vô ích. THUẦN."""
	try:
		n = float(x)
		return str(int(n)) if n.is_integer() else ("%.6f" % n).rstrip("0").rstrip(".")
	except (TypeError, ValueError):
		return str(x or "")


def _cau_dong(loai, dong, cu=None):
	"""Dịch một dòng BOM Item thành câu người trong bếp đọc được. THUẦN."""
	dong = dong or {}
	ten = dong.get("item_name") or dong.get("item_code") or "nguyên liệu"
	sl = dong.get("qty")
	dvt = dong.get("uom") or dong.get("stock_uom") or ""
	if loai == "them":
		return "Thêm %s %s %s" % (ten, _so_dep(sl), dvt)
	if loai == "bo":
		return "Bỏ %s %s %s" % (ten, _so_dep(sl), dvt)
	return "Đổi %s %s thành %s %s" % (ten, _so_dep(cu), _so_dep(sl), dvt)


def dich_version(du_lieu, dong_theo=None):
	"""Dịch `Version.data` của BOM, bỏ bảng khai triển và trường máy tính. THUẦN."""
	if isinstance(du_lieu, str):
		try:
			du_lieu = json.loads(du_lieu or "{}")
		except (TypeError, ValueError):
			return []
	du_lieu = du_lieu or {}
	ra = []
	bo_qua = {"exploded_items", "modified", "modified_by", "total_cost",
		"raw_material_cost", "operating_cost", "base_total_cost"}
	nhan = {"quantity": "số lượng ra", "is_active": "hoạt động",
		"is_default": "mặc định", "docstatus": "trạng thái"}
	for d in du_lieu.get("changed") or []:
		if len(d) < 3 or d[0] in bo_qua:
			continue
		if d[0] in nhan:
			ra.append("Đổi %s %s thành %s" % (nhan[d[0]], _so_dep(d[1]), _so_dep(d[2])))
	for loai, cau in (("added", "them"), ("removed", "bo")):
		for d in du_lieu.get(loai) or []:
			if len(d) >= 2 and d[0] == "items":
				ra.append(_cau_dong(cau, d[1]))
	for d in du_lieu.get("row_changed") or []:
		if len(d) < 4 or d[0] != "items":
			continue
		thay = d[3] or []
		meta = (dong_theo or {}).get(str(d[2]), {})
		ten = meta.get("item_name") or meta.get("item_code") or "dòng %s" % d[2]
		dvt = meta.get("uom") or ""
		for x in thay:
			if len(x) >= 3 and x[0] in ("item_name", "item_code"):
				ten = x[2] or x[1] or ten
			if len(x) >= 3 and x[0] == "uom":
				dvt = x[2] or x[1] or ""
		for x in thay:
			if len(x) >= 3 and x[0] == "qty":
				ra.append("Đổi %s %s thành %s %s" % (ten, _so_dep(x[1]), _so_dep(x[2]), dvt))
	return ra


def _kiem_xuat():
	if not _vai_ghi_so() & set(frappe.get_roles()):
		frappe.throw("Chỉ bếp trưởng, quản lý công thức hoặc giám đốc được xuất Excel công thức.")


@frappe.whitelist()
def xuat_excel(tab=None, trang_thai=None, tim=None, huong_dan=None, chang=None,
		bom=None):
	"""Xuất đúng tập đang lọc, mỗi dòng nguyên liệu là một dòng Excel."""
	_kiem_xuat()
	if bom:
		cac_bom = [bom]
	else:
		trang_thai = trang_thai or "dang_dung"
		kq = danh_sach(tab, trang_thai, tim, huong_dan, chang, _tat_ca=True)
		cac_bom = [x["bom"] for x in kq["ds"]]
	bang = [["Bộ lọc: khu=%s; trạng thái=%s; tìm=%s; hướng dẫn=%s; chặng=%s; giờ xuất=%s; người xuất=%s" % (
		tab or "tất cả", trang_thai or "đang dùng", tim or "", huong_dan or "",
		chang or "", now_datetime(), frappe.session.user)], []]
	bang.append(["Mã món", "Tên món", "Mã BOM", "Trạng thái", "Số lượng ra", "Đơn vị",
		"Mã NVL", "Tên NVL", "Số lượng", "Đơn vị NVL", "Đơn giá", "Thành tiền",
		"Tổng giá vốn", "Giá vốn một đơn vị", "Người tạo", "Người sửa cuối", "Ngày sửa cuối"])
	for ten in cac_bom:
		b = frappe.get_doc("BOM", ten)
		trang = trang_thai_bom(b.docstatus, b.is_active, b.is_default)
		for d in b.items or []:
			bang.append([str(b.item), b.item_name or "", str(b.name),
				{"nhap": "Nháp", "dang_dung": "Đang dùng", "ban_cu": "Bản cũ", "da_huy": "Đã huỷ"}.get(trang, trang),
				flt(b.quantity), b.uom or "", str(d.item_code), d.item_name or "", flt(d.qty),
				d.uom or "", flt(d.rate), flt(d.amount), flt(b.total_cost),
				flt(b.total_cost) / flt(b.quantity) if flt(b.quantity) else 0,
				b.owner or "", b.modified_by or "", b.modified])
	from frappe.utils.xlsxutils import make_xlsx
	tep = make_xlsx(bang, "Cong thuc BOM")
	noi = tep.getvalue() if isinstance(tep, io.BytesIO) else tep
	return {"ten_file": "cong-thuc-bom-%s.xlsx" % nowdate(),
		"b64": base64.b64encode(noi).decode(), "so_dong": max(0, len(bang) - 3)}


def _chuoi_bom(name):
	"""Tên bản hiện tại và các bản trước, không để vòng liên kết làm treo."""
	ra, x = [], name
	for _ in range(30):
		if not x or x in ra:
			break
		ra.append(x)
		x = frappe.db.get_value("BOM", x, "custom_ban_truoc")
	return ra


def _ten_nguoi(cac_email):
	ra = {}
	for e in cac_email:
		ra[e] = frappe.db.get_value("User", e, "full_name") or e
	return ra


def _lich_su_cua(cac_bom, tu_ngay=None, den_ngay=None, nguoi=None):
	loc_v = {"ref_doctype": "BOM", "docname": ["in", cac_bom]}
	loc_c = {"reference_doctype": "BOM", "reference_name": ["in", cac_bom],
		"comment_type": ["in", ["Comment", "Info"]]}
	if tu_ngay:
		loc_v["creation"] = [">=", tu_ngay]
		loc_c["creation"] = [">=", tu_ngay]
	if den_ngay:
		loc_v["creation"] = ["between", [tu_ngay or "2000-01-01", "%s 23:59:59" % den_ngay]]
		loc_c["creation"] = ["between", [tu_ngay or "2000-01-01", "%s 23:59:59" % den_ngay]]
	if nguoi:
		loc_v["owner"] = nguoi
		loc_c["owner"] = nguoi
	versions = frappe.get_all("Version", filters=loc_v,
		fields=["name", "docname", "owner", "creation", "data"], limit_page_length=0)
	comments = frappe.get_all("Comment", filters=loc_c,
		fields=["name", "reference_name", "owner", "creation", "content"], limit_page_length=0)
	emails = {x.owner for x in versions + comments}
	ten = _ten_nguoi(emails)
	ra = []
	dong_theo = {x.name: x for x in frappe.get_all("BOM Item", filters={"parent": ["in", cac_bom]},
		fields=["name", "item_name", "item_code", "uom"], limit_page_length=0)}
	for x in versions:
		cau = dich_version(x.data, dong_theo)
		if cau:
			ra.append({"bom": x.docname, "luc": str(x.creation), "nguoi": ten.get(x.owner, x.owner), "email": x.owner, "cau": cau})
	for x in comments:
		noi = re.sub(r"<[^>]+>", "", x.content or "").strip()
		if noi:
			ra.append({"bom": x.reference_name, "luc": str(x.creation), "nguoi": ten.get(x.owner, x.owner), "email": x.owner, "cau": [noi]})
	return sorted(ra, key=lambda x: x["luc"], reverse=True)


@frappe.whitelist()
def lich_su(name):
	_kiem_xem()
	return _lich_su_cua(_chuoi_bom(name))


def _ban_da_xoa(data):
	# Frappe delete_doc.add_to_deleted_document lưu doc.as_json(), không phải Version.
	try:
		d = json.loads(data or "{}")
	except (TypeError, ValueError):
		return None
	if not isinstance(d, dict) or d.get("doctype") != "BOM":
		return None
	return {"bom": d.get("name"), "ma": d.get("item"), "ten": d.get("item_name"),
		"so_luong": d.get("quantity"), "dvt": d.get("uom"),
		"dong": [{"ma": x.get("item_code"), "ten": x.get("item_name"),
			"sl": x.get("qty"), "dvt": x.get("uom")} for x in d.get("items") or []]}


@frappe.whitelist()
def ban_da_xoa(name):
	"""Chỉ đọc bản lưu của BOM đã xoá, không nạp hay phục hồi BOM."""
	_kiem_xem()
	d = frappe.db.get_value("Deleted Document", {"name": name, "deleted_doctype": "BOM"},
		["data", "deleted_name"], as_dict=True)
	ra = _ban_da_xoa(d.data) if d else None
	if not ra:
		frappe.throw("Không còn bản lưu công thức này. Nhờ quản lý kiểm tra lịch sử.")
	return ra


@frappe.whitelist()
def nhat_ky(nguoi=None, mon=None, tu_ngay=None, den_ngay=None):
	"""Nhật ký tập trung, mặc định bảy ngày và trả lựa chọn cho bộ lọc."""
	_kiem_xem()
	tu_ngay = tu_ngay or str(add_days(nowdate(), -6))
	den_ngay = den_ngay or nowdate()
	loc = {"item": mon} if mon else {}
	boms = frappe.get_all("BOM", filters=loc,
		fields=["name", "item", "item_name"], limit_page_length=0)
	cac = [x.name for x in boms]
	ds = _lich_su_cua(cac, tu_ngay, den_ngay, nguoi) if cac else []
	mon_theo = {x.item: x.item_name or x.item for x in boms}
	loc_xoa = {"deleted_doctype": "BOM", "creation": ["between", [tu_ngay, "%s 23:59:59" % den_ngay]]}
	if nguoi:
		loc_xoa["owner"] = nguoi
	for x in frappe.get_all("Deleted Document", filters=loc_xoa,
			fields=["name", "deleted_name", "owner", "creation", "data"], limit_page_length=0):
		ban = _ban_da_xoa(x.data)
		if not ban or (mon and ban["ma"] != mon):
			continue
		mon_theo[ban["ma"]] = ban["ten"] or ban["ma"]
		ds.append({"bom": x.deleted_name, "da_xoa": x.name, "luc": str(x.creation),
			"nguoi": _ten_nguoi([x.owner])[x.owner], "email": x.owner,
			"cau": ["Đã xoá công thức. Bấm để xem bản lưu chỉ đọc."]})
	ds.sort(key=lambda x: x["luc"], reverse=True)
	return {"ds": ds[:500], "tong": len(ds), "tu_ngay": tu_ngay, "den_ngay": den_ngay,
		"nguoi": sorted({(x["email"], x["nguoi"]) for x in ds}, key=lambda x: x[1]),
		"mon": sorted(mon_theo.items(), key=lambda x: x[1])}


SIDEBAR_DESK = "Manufacturing"


def muc_sidebar():
	"""Lối vào nhật ký trên sidebar Desk, khai thuần để ca kiểm chốt."""
	return {"type": "Link", "label": "Nhật ký sửa công thức", "link_type": "URL",
		"url": "/nhat-ky-sua-cong-thuc", "child": 0}


def dung_sidebar():
	"""Dựng lối vào Desk lặp lại được, không thay các mục sẵn có."""
	try:
		if not frappe.db.exists("Workspace Sidebar", SIDEBAR_DESK):
			return 0
		doc = frappe.get_doc("Workspace Sidebar", SIDEBAR_DESK)
		m = muc_sidebar()
		if any(x.get("type") == m["type"] and x.get("label") == m["label"] for x in doc.get("items") or []):
			return 0
		doc.append("items", m)
		doc.flags.ignore_permissions = True
		doc.save()
		return 1
	except Exception:
		frappe.log_error(frappe.get_traceback(), "cong_thuc: dung sidebar")
		return 0


def _gan_huong_dan(ra):
	"""Moi the biet mon cua no da co huong dan che bien chua.

	Ba tinh trang: `chua` chua soan, `nhap` co ban nhap, `xong` dang dung.
	Them `lech` khi huong dan soan theo mot cong thuc khac ban mac dinh
	hien nay - do la luc bep dang lam theo giay cu.
	"""
	cac_ma = sorted({x["ma"] for x in ra})
	if not cac_ma:
		return
	co = {}
	for i in range(0, len(cac_ma), 300):
		for d in frappe.get_all(
				"Vagabond Huong Dan Che Bien",
				filters={"ma_mon": ["in", cac_ma[i:i + 300]]},
				fields=["name", "ma_mon", "trang_thai", "cong_thuc_da_doi"],
				limit_page_length=0):
			co[d.ma_mon] = d
	for x in ra:
		d = co.get(x["ma"])
		if not d:
			x["huong_dan"] = "chua"
			x["hd_name"] = ""
			x["hd_lech"] = 0
			continue
		x["huong_dan"] = "xong" if str(d.trang_thai) == "Đang dùng" else "nhap"
		x["hd_name"] = d.name
		x["hd_lech"] = 1 if d.cong_thuc_da_doi else 0


@frappe.whitelist()
def chi_tiet(name):
	"""Một công thức: đầu phiếu, dòng nguyên liệu, và chuỗi phiên bản."""
	_kiem_xem()
	b = frappe.get_doc("BOM", name)
	dong = [{"ma": d.item_code, "ten": d.item_name, "sl": d.qty,
		"dvt": d.uom, "note": d.get("custom_note") or ""}
		for d in (b.items or [])]
	# Chuoi phien ban: lan nguoc ban_truoc, va tim ban sau tro ve minh.
	chuoi, x = [], b.get("custom_ban_truoc")
	for _ in range(10):
		if not x:
			break
		chuoi.append(x)
		x = frappe.db.get_value("BOM", x, "custom_ban_truoc")
	ban_sau = frappe.get_all("BOM", filters={"custom_ban_truoc": name},
		pluck="name", limit_page_length=5)
	return {
		"bom": b.name, "ma": b.item,
		"ten": frappe.db.get_value("Item", b.item, "item_name") or b.item,
		"trang_thai": trang_thai_bom(b.docstatus, b.is_active, b.is_default),
		"so_luong": b.quantity, "dvt": b.uom,
		"chang": ten_chang_gom(b.get("custom_chang")),
		"dong": dong, "ban_truoc": chuoi, "ban_sau": ban_sau,
		"phien_ban": duoi_phien_ban(b.name),
		"lich_su": _lich_su_cua(_chuoi_bom(b.name))[:20],
	}


@frappe.whitelist()
def dieu_chinh(bom_cu):
	"""Tạo BẢN NHÁP mới sao chép từ một công thức đã ghi sổ."""
	_kiem_soan()
	cu = frappe.get_doc("BOM", bom_cu)
	if cint(cu.docstatus) != 1:
		frappe.throw(
			"Chỉ điều chỉnh được công thức đã ghi sổ. Bản nháp thì sửa "
			"thẳng, khỏi tạo phiên bản.")
	nhap = frappe.get_all("BOM", filters={"item": cu.item, "docstatus": 0},
		pluck="name", limit_page_length=1)
	if nhap:
		return {"bom_nhap": nhap[0], "da_co": 1,
			"ghi_chu": "Món này đang có sẵn bản nháp %s, sửa tiếp bản đó "
				"cho khỏi lạc nhau." % nhap[0]}
	moi = frappe.copy_doc(cu)
	moi.custom_ban_truoc = cu.name
	moi.is_default = 0
	moi.insert(ignore_permissions=True)
	return {"bom_nhap": moi.name, "da_co": 0,
		"ghi_chu": "Đã tạo bản nháp %s từ %s. Sửa dòng nguyên liệu rồi bấm "
			"Ghi sổ, bản cũ tự lui về làm bản lưu." % (moi.name, cu.name)}


@frappe.whitelist()
def tao_moi(ma_item, so_luong, dvt=None, dong=None):
	"""Tạo công thức nháp mới cho một món chưa có, hoặc thêm bản đầu tiên."""
	_kiem_soan()
	if not frappe.db.exists("Item", ma_item):
		frappe.throw("Không thấy mã %s trên hệ." % ma_item)
	nhap = frappe.get_all("BOM", filters={"item": ma_item, "docstatus": 0},
		pluck="name", limit_page_length=1)
	if nhap:
		frappe.throw("Món này đang có bản nháp %s chờ duyệt, sửa tiếp bản đó."
			% nhap[0])
	if isinstance(dong, str):
		import json as _json
		dong = _json.loads(dong or "[]")
	if not dong:
		frappe.throw("Công thức phải có ít nhất một dòng nguyên liệu.")
	doc = frappe.new_doc("BOM")
	doc.item = ma_item
	doc.company = frappe.db.get_single_value("Global Defaults", "default_company")
	doc.quantity = flt(so_luong) or 1
	doc.uom = dvt or frappe.db.get_value("Item", ma_item, "stock_uom")
	doc.currency = "VND"
	doc.rm_cost_as_per = "Valuation Rate"
	doc.with_operations = 0
	for d in dong:
		doc.append("items", {"item_code": d.get("ma"),
			"qty": flt(d.get("sl")), "uom": d.get("dvt") or None})
	doc.insert(ignore_permissions=True)
	return {"bom_nhap": doc.name,
		"ghi_chu": "Đã tạo bản nháp %s. Xem lại rồi bấm Ghi sổ." % doc.name}


@frappe.whitelist()
def sua_nhap(bom_nhap, so_luong=None, dong=None):
	"""Sửa dòng nguyên liệu của một bản nháp."""
	_kiem_soan()
	doc = frappe.get_doc("BOM", bom_nhap)
	if cint(doc.docstatus) != 0:
		frappe.throw("Bản %s đã ghi sổ, muốn đổi thì bấm Điều chỉnh để ra "
			"bản mới." % bom_nhap)
	if so_luong is not None and flt(so_luong) > 0:
		doc.quantity = flt(so_luong)
	if isinstance(dong, str):
		import json as _json
		dong = _json.loads(dong or "[]")
	if dong is not None:
		if not dong:
			frappe.throw("Công thức phải còn ít nhất một dòng nguyên liệu.")
		doc.set("items", [])
		for d in dong:
			doc.append("items", {"item_code": d.get("ma"),
				"qty": flt(d.get("sl")), "uom": d.get("dvt") or None})
	doc.save(ignore_permissions=True)
	return {"ok": 1, "bom_nhap": doc.name, "ghi_chu": "Đã lưu bản nháp."}


@frappe.whitelist()
def ghi_so(bom_nhap):
	"""Ghi sổ bản nháp thành bản đang dùng; bản trước lui về làm bản lưu."""
	_kiem_ghi_so()
	doc = frappe.get_doc("BOM", bom_nhap)
	if cint(doc.docstatus) != 0:
		frappe.throw("Bản %s không còn là nháp." % bom_nhap)
	cu = (doc.get("custom_ban_truoc") or "").strip()
	doc.submit()
	# Hai co is_active / is_default cua BOM cho sua sau ghi so, nen doi
	# thang bang db.set_value la duong chuan, khong lach luat gi.
	if cu and frappe.db.exists("BOM", cu):
		frappe.db.set_value("BOM", cu, {"is_default": 0, "is_active": 0})
	frappe.db.set_value("BOM", doc.name, {"is_default": 1, "is_active": 1})
	doc.add_comment("Comment", "Ghi sổ%s." % (", thay bản %s" % cu if cu else ""))
	if cu and frappe.db.exists("BOM", cu):
		frappe.get_doc("BOM", cu).add_comment("Comment", "Bản %s đã ghi sổ thay công thức này." % doc.name)
	frappe.db.commit()
	loi = "Đã ghi sổ %s thành bản đang dùng." % doc.name
	if cu:
		loi += " Bản cũ %s lui về làm bản lưu, vẫn tra lại được." % cu
	return {"ok": 1, "bom": doc.name, "ban_cu": cu, "ghi_chu": loi}


@frappe.whitelist()
def bo_nhap(bom_nhap):
	"""Bỏ một bản nháp tạo nhầm. Chỉ nháp mới bỏ được."""
	_kiem_soan()
	ds = cint(frappe.db.get_value("BOM", bom_nhap, "docstatus"))
	if ds != 0:
		frappe.throw("Bản %s đã ghi sổ, không bỏ được. Muốn thay thì Điều "
			"chỉnh ra bản mới." % bom_nhap)
	frappe.delete_doc("BOM", bom_nhap, ignore_permissions=True)
	return {"ok": 1, "ghi_chu": "Đã bỏ bản nháp %s." % bom_nhap}

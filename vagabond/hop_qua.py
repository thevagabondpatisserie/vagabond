"""Tuỳ biến ruột hộp quà ngay trên dòng báo giá.

Việc thật ngày 21/08/2026: khách đặt 25 hộp Moongarden nhưng không ăn được
sầu riêng, xin đổi sang hạt dẻ long nhãn và chịu phụ thu. Anh Việt chốt
"Được em, code thì chỉnh được".

CHỖ ĐỀ BÀI KHÔNG KHỚP DỮ LIỆU THẬT
----------------------------------
Đề bài nói "Product Bundle đang bị khoá cứng". Tra ra thì khác: cả hệ thống
đang có ĐÚNG 0 bản ghi Product Bundle, và `BASS00038 - HỘP MOONGARDEN, năm
2026` chỉ là một Item bán hàng bình thường, không Product Bundle, không BOM,
không Vagabond Combo. Nghĩa là hệ thống chưa hề biết trong hộp có bánh gì,
nên không phải bung không được mà là chưa có ruột để bung.

Vậy nên chỗ này làm hai tầng:

  Tầng MASTER, dùng chung mọi đơn: `Product Bundle` chuẩn của ERPNext, mỗi
  hộp một bản ghi, liệt kê bánh trong hộp. Đây là danh mục, KHÔNG bao giờ bị
  đơn hàng sửa vào.

  Tầng ĐƠN, riêng từng dòng báo giá: một bản CHÉP của ruột, cất dạng JSON ở
  ô `ruot_hop` của dòng. Sales đổi món, bớt món, thêm món, gõ phụ thu - tất
  cả nằm trong bản chép này. Mã hộp gốc trong danh mục không suy suyển.

VÌ SAO KHÔNG BUNG THÀNH NHIỀU DÒNG HÀNG
---------------------------------------
Đơn 25 hộp cho khách doanh nghiệp phải xuất hoá đơn đúng một dòng "Hộp
Moongarden x25" theo giá bán hộp. Bung thành từng cái bánh là đổi cả tờ hoá
đơn điện tử, mà hoá đơn đã gửi cơ quan thuế thì không sửa lại được (luật anh
Việt chốt 13/08/2026). Nên dòng hàng giữ nguyên MỘT dòng, phụ thu cộng vào
đơn giá của chính dòng đó, còn ruột đi kèm để bếp biết làm gì và kế toán
tính được giá thành.

Đổi lại được nếu sau này anh Việt muốn in ruột ra hoá đơn: dữ liệu ruột đã
nằm sẵn ở dạng danh sách món, chỉ khác cách vẽ ra giấy.
"""

import json

import frappe
from frappe.utils import cint, flt

QUYEN = ("System Manager", "Giám đốc", "AP Giám đốc", "Sales Manager",
	"Vagabond Sales", "Accounts Manager")

# Nhóm hàng nào được coi là hộp quà có ruột. Để rộng vừa đủ: nhóm mùa vụ và
# nhóm hộp quà. Món ngoài nhóm này vẫn khai ruột được nếu có Product Bundle,
# bảng này chỉ quyết định app có gợi ý nút Tuỳ biến hay không.
NHOM_HOP = ("Hộp bánh theo mùa", "Hộp quà", "Set quà tặng")

TRUONG_MOI = {"Bao Gia Dong": [
	{
		"fieldname": "ruot_hop", "label": "Ruột hộp (JSON)",
		"fieldtype": "Long Text", "insert_after": "ck_tien_dong",
		"description": "Danh sách bánh bên trong hộp của RIÊNG dòng này. "
			"Sales sửa trên app, mã hộp gốc trong danh mục không đổi.",
	},
	{
		"fieldname": "phu_thu_hop", "label": "Phụ thu tuỳ biến",
		"fieldtype": "Currency", "insert_after": "ruot_hop",
		"description": "Tiền cộng thêm cho một hộp do khách đổi vị. Đã nằm "
			"trong đơn giá của dòng, ô này chỉ để tra lại về sau.",
	},
]}


# ---------------------------------------------------------------- phép thuần


def doc_ruot(s):
	"""Đọc chuỗi JSON ruột hộp ra danh sách. Hỏng thì trả danh sách rỗng chứ
	không nổ: một ô dữ liệu gõ sai không được làm rớt cả tờ báo giá."""
	if not s:
		return []
	if isinstance(s, list):
		return list(s)
	try:
		v = json.loads(s)
	except Exception:
		return []
	return v if isinstance(v, list) else []


def chuan_ruot(ruot):
	"""Nắn danh sách ruột về đúng bốn khoá, bỏ dòng rác.

	Giữ nguyên thứ tự Sales xếp: thứ tự món trong hộp là thứ tự xếp bánh,
	bếp đọc theo đó.
	"""
	ra = []
	for d in (ruot or []):
		if not isinstance(d, dict):
			continue
		ma = (d.get("ma") or "").strip()
		ten = (d.get("ten") or "").strip()
		if not ma and not ten:
			continue
		sl = flt(d.get("sl"))
		if sl <= 0:
			sl = 1
		ra.append({
			"ma": ma,
			"ten": ten or ma,
			"sl": sl,
			"ghi_chu": (d.get("ghi_chu") or "").strip(),
		})
	return ra


def da_doi_ruot(goc, moi):
	"""Ruột của dòng có khác bản gốc trong danh mục không."""
	g = [(x["ma"], x["sl"]) for x in chuan_ruot(goc)]
	m = [(x["ma"], x["sl"]) for x in chuan_ruot(moi)]
	return sorted(g) != sorted(m)


def so_mon(ruot):
	"""Tổng số bánh trong hộp, để đối chiếu với số bánh chuẩn của hộp."""
	return sum(flt(x.get("sl")) for x in chuan_ruot(ruot))


def don_gia_sau_phu_thu(don_gia_goc, phu_thu):
	"""Đơn giá một hộp sau khi cộng phụ thu tuỳ biến.

	Phụ thu ÂM cũng nhận: khách bỏ bớt một bánh thì trừ tiền, và trừ tiền
	cũng là một kiểu tuỳ biến. Chỉ chặn cho giá xuống dưới 0.
	"""
	g = flt(don_gia_goc) + flt(phu_thu)
	return g if g > 0 else 0.0


def mo_ta_thay_doi(goc, moi):
	"""Một câu tiếng Việt tả đúng chỗ khác nhau, để in lên báo giá và cho
	bếp đọc. Trả chuỗi rỗng nếu không đổi gì."""
	g = {x["ma"]: x for x in chuan_ruot(goc)}
	m = {x["ma"]: x for x in chuan_ruot(moi)}
	bo = [g[k]["ten"] for k in g if k not in m]
	them = [m[k]["ten"] for k in m if k not in g]
	doi_sl = []
	for k in m:
		if k in g and flt(m[k]["sl"]) != flt(g[k]["sl"]):
			doi_sl.append("%s %s thành %s" % (m[k]["ten"],
				_so(g[k]["sl"]), _so(m[k]["sl"])))
	phan = []
	if bo and them:
		phan.append("đổi %s sang %s" % (", ".join(bo), ", ".join(them)))
	else:
		if bo:
			phan.append("bỏ %s" % ", ".join(bo))
		if them:
			phan.append("thêm %s" % ", ".join(them))
	if doi_sl:
		phan.append("đổi số lượng " + ", ".join(doi_sl))
	return "; ".join(phan)


def _so(v):
	v = flt(v)
	return str(int(v)) if v == int(v) else str(v)


# ------------------------------------------------------- phần chạm hệ thống


def _chan():
	if not set(frappe.get_roles()) & set(QUYEN):
		frappe.throw("Chỉ Sales, kế toán hoặc giám đốc mới tuỳ biến hộp được.")


@frappe.whitelist()
def ruot_goc(ma_mon):
	"""Ruột chuẩn của một hộp, đọc từ Product Bundle trong danh mục.

	Chưa khai Product Bundle thì trả danh sách rỗng kèm lời nhắc, KHÔNG đoán
	bừa món nào nằm trong hộp.
	"""
	_chan()
	ma_mon = (ma_mon or "").strip()
	if not ma_mon:
		return {"ma_mon": "", "ruot": [], "co_khai": 0}
	pb = frappe.db.get_value("Product Bundle", {"new_item_code": ma_mon}, "name")
	if not pb:
		return {
			"ma_mon": ma_mon, "ruot": [], "co_khai": 0,
			"nhac": "Hộp này chưa khai ruột trong danh mục. Vào Desk, mở "
				"Product Bundle, tạo một bản ghi cho %s rồi liệt kê bánh bên "
				"trong. Khai một lần, mọi báo giá về sau dùng chung." % ma_mon,
		}
	dong = frappe.get_all("Product Bundle Item", filters={"parent": pb},
		fields=["item_code", "description", "qty"], order_by="idx asc")
	ten = {}
	ma_ds = [d.item_code for d in dong if d.item_code]
	if ma_ds:
		for it in frappe.get_all("Item", filters={"name": ["in", ma_ds]},
				fields=["name", "item_name"]):
			ten[it.name] = it.item_name
	return {
		"ma_mon": ma_mon, "co_khai": 1, "bundle": pb,
		"ruot": chuan_ruot([{
			"ma": d.item_code,
			"ten": ten.get(d.item_code) or d.description or d.item_code,
			"sl": d.qty,
		} for d in dong]),
	}


@frappe.whitelist()
def mon_thay_the(tim=None, gioi_han=40):
	"""Danh sách bánh Sales có thể chọn để thay vào hộp.

	Chỉ trả món ĐANG BÁN và không phải chính hộp quà, để khỏi lồng hộp vào
	hộp.
	"""
	_chan()
	dk = {"disabled": 0, "is_sales_item": 1}
	tim = (tim or "").strip()
	loc = [["Item", k, "=", v] for k, v in dk.items()]
	loc.append(["Item", "item_group", "not in", list(NHOM_HOP)])
	if tim:
		loc.append(["Item", "item_name", "like", "%" + tim + "%"])
	ds = frappe.get_all("Item", filters=loc,
		fields=["name", "item_name", "item_group", "stock_uom"],
		limit=cint(gioi_han) or 40, order_by="item_name asc")
	return {"ds": [{"ma": x.name, "ten": x.item_name, "nhom": x.item_group,
		"dvt": x.stock_uom} for x in ds]}


@frappe.whitelist()
def xem_tuy_bien(ma_mon, ruot=None, don_gia_goc=0, phu_thu=0):
	"""Máy chốt số cho một lần tuỳ biến: ruột đã nắn, câu mô tả, đơn giá mới.

	Cửa này để app hỏi máy chủ thay vì tự tính trên điện thoại (QT-19).
	"""
	_chan()
	if isinstance(ruot, str):
		ruot = doc_ruot(ruot)
	goc = ruot_goc(ma_mon)
	moi = chuan_ruot(ruot if ruot is not None else goc.get("ruot"))
	return {
		"ma_mon": ma_mon,
		"ruot_goc": goc.get("ruot") or [],
		"ruot": moi,
		"co_khai_goc": goc.get("co_khai") or 0,
		"nhac": goc.get("nhac") or "",
		"da_doi": 1 if da_doi_ruot(goc.get("ruot"), moi) else 0,
		"mo_ta": mo_ta_thay_doi(goc.get("ruot"), moi),
		"so_mon": so_mon(moi),
		"so_mon_goc": so_mon(goc.get("ruot")),
		"don_gia_moi": don_gia_sau_phu_thu(don_gia_goc, phu_thu),
		"phu_thu": flt(phu_thu),
	}

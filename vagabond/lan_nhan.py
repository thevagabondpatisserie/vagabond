# -*- coding: utf-8 -*-
"""Nhận hàng theo phiếu yêu cầu điều chuyển: MỘT lần bấm là MỘT phiếu kho,
kể cả khi mạng rớt và người ta bấm lại.

Vì sao có tệp này
-----------------
Màn "Nhận hàng" trên app trước đây gọi thẳng `frappe.client.insert` rồi
`frappe.client.submit`. Mạng chập chờn đúng lúc máy chủ đã ghi sổ xong mà
phản hồi không về được, màn hình báo lỗi, bếp bấm lại, và máy chủ ghi thêm
một phiếu chuyển nữa. ERPNext chỉ chặn khi TỔNG đã chuyển vượt số trên phiếu
yêu cầu (update_completed_qty), nên nhận 30 trên phiếu xin 100 mà bấm lại là
thành 60. Codex P1 trên PR #222 vòng 3 (07/09/2026). Chốt ở màn hình
(`RCV_DANG_GUI`) chỉ chặn bấm kép trong cùng một lần gửi, không chặn được
lần gửi sau khi lần trước đã báo lỗi.

Cách chống trùng
----------------
Mỗi lần nhận mang một MÃ LẦN NHẬN do màn hình sinh ra lúc mở màn. Mã giữ
nguyên khi gửi hỏng (bấm lại là gửi lại ĐÚNG lần đó), và đổi sang mã mới khi
gửi xong hay khi người ta sửa số lượng (vì lúc đó là một lần nhận khác).

Máy chủ ghi mã đó vào ô `vgb_ma_lan_nhan` của Stock Entry, ô này có RÀNG
BUỘC DUY NHẤT ở cơ sở dữ liệu (khai trong TRUONG_MOI dưới đây). Hai yêu cầu
mang cùng mã tới cùng lúc thì MariaDB chỉ cho một cái chèn được; cái còn lại
ăn lỗi trùng khoá, được đón lại và trả về đúng phiếu cái kia đã tạo. Không
dựa vào "đọc trước rồi mới ghi", vì hai kết nối đọc cùng lúc đều thấy trống.

Giữ đúng cách chọn lô của v219: dòng gửi lên KHÔNG kèm lô, `lo_hang.gan_lo`
ở before_validate của Stock Entry chọn. Tệp này không chọn lô lại lần nữa.

Tên tệp là `lan_nhan` vì `nhan_hang.py` (nhận từng phần đơn mua) và
`nhan_dieu_chuyen.py` (bếp xác nhận đã nhận, không đụng sổ) đều đã có việc
khác. Đừng gộp: ba tệp là ba nghiệp vụ.

Phần THUẦN (kiểm được không cần Frappe): `doc_ma_lan`, `doc_dong_nhan`.
Phần chạm hệ: `nhan_theo_phieu`, `tra_lan_nhan` (chỉ đọc).
"""

import json
import re

import frappe
from frappe.utils import flt, nowdate, nowtime

# Mã lần nhận: chữ, số, gạch ngang, gạch dưới; đủ dài để hai màn hình không
# vô tình trùng nhau, đủ ngắn để nằm trong ô Data 140 ký tự.
MAU_MA_LAN = re.compile(r"^[A-Za-z0-9_-]{8,80}$")

TRUONG_MOI = {
	"Stock Entry": [
		{
			"fieldname": "vgb_ma_lan_nhan", "label": "Mã lần nhận trên app",
			"fieldtype": "Data", "insert_after": "remarks",
			"unique": 1, "read_only": 1, "no_copy": 1, "print_hide": 1,
			"description": (
				"Màn Nhận hàng trên app sinh mã này cho mỗi lần bấm xác nhận. "
				"Ràng buộc duy nhất: bấm lại sau khi mạng rớt không tạo thêm phiếu."
			),
		},
	]
}


# ------------------------------------------------------------ phần thuần


def doc_ma_lan(ma):
	"""Đọc mã lần nhận từ app. Sai dạng là ném, KHÔNG tự sinh mã thay: mã tự
	sinh ở máy chủ thì mỗi lần gửi lại là một mã mới, mất hết ý nghĩa chống
	trùng."""
	ma = ma.strip() if isinstance(ma, str) else ""
	if not MAU_MA_LAN.match(ma):
		frappe.throw(
			"Thiếu mã lần nhận hoặc mã sai dạng. Thoát màn Nhận hàng rồi vào lại; "
			"vẫn lỗi thì app đang chạy bản cũ, tải lại trang."
		)
	return ma


def doc_dong_nhan(dong):
	"""Đọc các dòng nhận từ app. Trả về danh sách dict sạch, theo đúng thứ tự.

	Mỗi dòng: item_code, qty (> 0), uom, conversion_factor (> 0),
	material_request, material_request_item. Không kèm lô: máy chủ chọn.
	Dòng gửi kèm batch_no hay serial_and_batch_bundle bị BỎ hai ô đó, vì
	màn hình không được chọn lô (v219).
	"""
	if isinstance(dong, str):
		dong = json.loads(dong or "[]")
	sach = []
	for d in dong or []:
		ma = (d.get("item_code") or d.get("ma") or "").strip()
		sl = flt(d.get("qty") if d.get("qty") is not None else d.get("sl"))
		if not ma or sl <= 0:
			continue
		he_so = flt(d.get("conversion_factor")) or 1
		if he_so <= 0:
			he_so = 1
		x = {"item_code": ma, "qty": sl, "conversion_factor": he_so}
		if d.get("uom"):
			x["uom"] = d.get("uom")
		if d.get("material_request"):
			x["material_request"] = d.get("material_request")
		if d.get("material_request_item"):
			x["material_request_item"] = d.get("material_request_item")
		sach.append(x)
	if not sach:
		frappe.throw("Chưa có dòng nào có số lượng lớn hơn 0 để nhập kho.")
	return sach


# ------------------------------------------------------------ chạm hệ


def _da_co(ma_lan, khoa=False):
	return frappe.db.get_value(
		"Stock Entry", {"vgb_ma_lan_nhan": ma_lan}, ["name", "docstatus"], as_dict=True,
		for_update=khoa,
	)


def _tra_phieu_cu(cu):
	"""Phiếu của lần nhận này đã có sẵn: trả về nó, không tạo thêm."""
	ds = int(cu.get("docstatus") or 0)
	if ds == 2:
		frappe.throw(
			"Lần nhận này đã có phiếu %s nhưng phiếu đó đã bị huỷ. "
			"Thoát màn Nhận hàng rồi vào lại để nhận lần mới." % cu.get("name")
		)
	if ds == 0:
		# Bản nháp cùng mã: lần trước chèn xong mà chưa ghi sổ được. Ghi sổ
		# tiếp chính nó thay vì tạo phiếu thứ hai.
		doc = frappe.get_doc("Stock Entry", cu.get("name"))
		doc.submit()
	return {"ok": 1, "name": cu.get("name"), "da_co": 1}


def _la_loi_trung_khoa(e):
	loai = tuple(
		x for x in (
			getattr(frappe, "UniqueValidationError", None),
			getattr(frappe, "DuplicateEntryError", None),
		) if x
	)
	return bool(loai) and isinstance(e, loai)


@frappe.whitelist()
def tra_lan_nhan(ma_lan_nhan=None):
	"""Lần nhận này đã thành phiếu chưa. CHỈ ĐỌC.

	Màn hình gọi khi mở lại một lần nhận đang chờ xác nhận (mất phản hồi sau
	khi gửi): có phiếu thì báo và không gửi lại, chưa có thì gửi lại đúng mã.
	Codex P1 vòng 4 trên PR #222.
	"""
	ma_lan = doc_ma_lan(ma_lan_nhan)
	cu = _da_co(ma_lan)
	if not cu:
		return {"co": 0}
	return {"co": 1, "name": cu.get("name"), "docstatus": int(cu.get("docstatus") or 0)}


@frappe.whitelist()
def nhan_theo_phieu(ma_lan_nhan=None, phieu=None, kho_xuat=None, kho_nhan=None,
		dong=None, ghi_chu=None, cong_ty=None):
	"""Tạo và ghi sổ MỘT phiếu chuyển kho cho một lần nhận. Gửi lại cùng mã
	lần nhận thì trả về phiếu đã có, không tạo thêm.

	Quyền: đúng như đường cũ (frappe.client.insert + submit), tức người gọi
	phải có quyền tạo và ghi sổ Stock Entry. Không ignore_permissions.
	"""
	ma_lan = doc_ma_lan(ma_lan_nhan)
	if not kho_xuat or not kho_nhan:
		frappe.throw("Phiếu chưa có kho xuất hoặc kho nhận, không nhập kho được.")
	if kho_xuat == kho_nhan:
		frappe.throw("Kho xuất và kho nhận không được trùng nhau.")
	sach = doc_dong_nhan(dong)

	cu = _da_co(ma_lan)
	if cu:
		return _tra_phieu_cu(cu)

	doc = frappe.new_doc("Stock Entry")
	doc.company = (
		cong_ty
		or frappe.defaults.get_user_default("Company")
		or frappe.db.get_value("Company", {}, "name")
	)
	doc.stock_entry_type = "Material Transfer"
	doc.purpose = "Material Transfer"
	doc.set_posting_time = 1
	doc.posting_date = nowdate()
	doc.posting_time = nowtime()
	doc.from_warehouse = kho_xuat
	doc.to_warehouse = kho_nhan
	doc.remarks = ghi_chu or (
		"Nhận hàng điều chuyển nội bộ trên app" + (" - phiếu %s" % phieu if phieu else "")
	)
	doc.vgb_ma_lan_nhan = ma_lan
	for x in sach:
		hang = dict(x)
		hang["s_warehouse"] = kho_xuat
		hang["t_warehouse"] = kho_nhan
		if phieu and not hang.get("material_request"):
			hang["material_request"] = phieu
		doc.append("items", hang)

	# Điểm lưu quanh lần chèn: trùng khoá thì lùi về đây rồi trả phiếu của
	# bên kia, KHÔNG rollback cả transaction (bộ kiểm tích hợp chạy trong
	# điểm lưu của nó, rollback trần sẽ phá luôn điểm lưu đó).
	diem = "vgb_lan_nhan_chen"
	frappe.db.savepoint(diem)
	try:
		doc.insert()
	except Exception as e:
		if not _la_loi_trung_khoa(e):
			raise
		frappe.db.rollback(save_point=diem)
		# Đọc KHOÁ (FOR UPDATE), không đọc thường: MariaDB REPEATABLE READ giữ
		# ảnh chụp từ câu SELECT đầu tiên của transaction, lúc đó phiếu của bên
		# kia chưa commit, đọc thường sẽ không thấy và lại ném lỗi trùng khoá
		# ra màn hình. Đọc khoá luôn thấy bản đã commit mới nhất. Chỉ dùng ở
		# nhánh này, không dùng ở lần dò đầu (dò FOR UPDATE khi chưa có dòng
		# sẽ lấy gap lock, hai bên cùng chèn thành deadlock).
		cu = _da_co(ma_lan, khoa=True)
		if not cu:
			raise
		return _tra_phieu_cu(cu)
	doc.submit()
	return {"ok": 1, "name": doc.name, "da_co": 0}

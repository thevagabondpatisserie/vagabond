# -*- coding: utf-8 -*-
"""Một đơn trả bằng NHIỀU phương thức (anh Việt 01/09/2026).

Vì sao có tệp này
-----------------
Bên Loan Anh vướng chuyện khách trả một đơn bằng hai đường: chuyển khoản
trước một phần, tới cửa hàng đưa nốt tiền mặt. Đơn 92857 ngày 31/08 là ví
dụ thật: Pancake ghi 2.000.000 tiền mặt và 225.000 quẹt thẻ, tổng
2.225.000. Ô `vgb_pt_thanh_toan` chỉ chứa được MỘT tên, nên bạn nhập phải
chọn một cái, và sổ ghi cả 2.225.000 vào tiền mặt. Két tiền cuối ca lệch
đúng 225.000 mà không ai truy ra được vì sổ nói tiền mặt.

`_doan_thanh_toan` bên ban_hang.py trước đây thấy hai kênh thì CỐ Ý bỏ
trống để sales tự chọn. Cách đó đúng khi máy chưa có chỗ nào ghi được hai
dòng; giờ có rồi thì máy điền được cả hai.

Ô CŨ VẪN GIỮ, KHÔNG BỎ
----------------------
`vgb_pt_thanh_toan` có 77 chỗ đọc trong 13 tệp: chốt ca, đối soát SePay,
công nợ, hoá đơn điện tử, cột danh sách bên Desk, báo cáo... Đổi nó thành
bảng con là phải sửa cả 77 chỗ trong một lần deploy, mà đây là tiền.

Nên luật ở đây là: bảng con là nơi ghi SỰ THẬT, còn ô cũ vẫn được giữ và
luôn mang phương thức CHÍNH - dòng có số tiền lớn nhất. Mọi chỗ đọc ô cũ
tiếp tục chạy y như hôm nay, không sửa một dòng nào. Chỗ nào cần con số
đúng theo từng phương thức thì đọc bảng con; đợt này mới sửa MÀN CHỐT CA,
vì đó là chỗ con số sai làm lệch két thật.

Danh sách chỗ CHƯA đọc bảng con, để phiên sau biết mà làm tiếp: đối soát
SePay, công nợ phải thu, báo cáo doanh thu theo phương thức, cột danh sách
hoá đơn bên Desk. Bốn chỗ đó vẫn nhìn phương thức chính.
"""

# ------------------------------------------------------------ phần thuần


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def gom_dong(dong):
	"""Chuẩn hoá và gom các dòng thanh toán. THUẦN.

	Bỏ dòng thiếu phương thức hoặc số tiền không dương. Hai dòng CÙNG một
	phương thức thì cộng lại thành một: thu ngân gõ hai lần "Tiền mặt" là
	chuyện thường, mà để hai dòng thì màn chốt ca đếm hai lần một tên và
	bảng số trông như có lỗi.

	Mã tham chiếu giữ cái ĐẦU TIÊN không rỗng. Ghép hai mã lại thành một
	chuỗi thì phép kiểm định dạng mã ở ban_hang.py không nhận ra nữa.
	"""
	ra, thu_tu = {}, []
	for d in dong or []:
		if not isinstance(d, dict):
			continue
		pt = (d.get("pt") or "").strip()
		so = _so(d.get("so_tien"))
		if not pt or so <= 0:
			continue
		if pt not in ra:
			ra[pt] = {"pt": pt, "so_tien": 0.0, "ma_tham_chieu": "",
				"do_may": 1 if d.get("do_may") else 0}
			thu_tu.append(pt)
		ra[pt]["so_tien"] = round(ra[pt]["so_tien"] + so, 2)
		ma = (d.get("ma_tham_chieu") or "").strip()
		if ma and not ra[pt]["ma_tham_chieu"]:
			ra[pt]["ma_tham_chieu"] = ma
		if not d.get("do_may"):
			# Nguoi go tay thi ca dong do khong con la cua may nua.
			ra[pt]["do_may"] = 0
	return [ra[p] for p in thu_tu]


def tong(dong):
	"""Tổng tiền của các dòng. THUẦN."""
	return round(sum(_so(d.get("so_tien")) for d in dong or []), 2)


def chinh_cua(dong):
	"""Phương thức CHÍNH: dòng có số tiền lớn nhất. THUẦN.

	Bằng nhau thì lấy dòng ĐỨNG TRƯỚC, không lấy theo thứ tự bảng chữ cái.
	Thứ tự dòng là thứ tự khách trả, nên dòng trước là lần trả đầu; chọn
	theo chữ cái thì cùng một đơn nhập lại có thể ra phương thức chính
	khác, mà ô đó đang là căn cứ cho chốt ca và hoá đơn điện tử.
	"""
	chon = None
	for d in dong or []:
		if chon is None or _so(d.get("so_tien")) > _so(chon.get("so_tien")):
			chon = d
	return (chon or {}).get("pt") or ""


def lech(dong, tong_don):
	"""Tổng các dòng lệch bao nhiêu so với tổng đơn. THUẦN.

	Dương là các dòng ghi THỪA, âm là ghi THIẾU. Trả 0.0 khi khớp.
	"""
	return round(tong(dong) - _so(tong_don), 2)


# Sai lech duoi muc nay coi nhu khop. Tien Viet khong co hao, nhung
# grand_total di qua phep tinh thue 8% nen hay ra so le kieu 2224999,9996.
ZERO = 1.0


def khop_tong(dong, tong_don):
	"""Các dòng có khớp tổng đơn không. THUẦN."""
	return abs(lech(dong, tong_don)) <= ZERO


def ma_thue_cua(dong, ma_theo_pt):
	"""Mã hình thức thanh toán gửi cơ quan thuế. THUẦN.

	`ma_theo_pt` là bảng {tên phương thức: mã thuế} lấy từ pt_thanh_toan.

	Một đơn vừa tiền mặt vừa chuyển khoản thì mã đúng là "TM/CK" - m-invoice
	đã có sẵn mã đó, xem MA_THUE bên pt_thanh_toan.py. Trước đây không bao
	giờ dùng tới vì một đơn chỉ mang được một phương thức.

	Chỉ có một mã duy nhất thì trả đúng mã đó. Trộn TM với CK thì ra TM/CK.
	Có mã lạ hay thiếu mã thì trả rỗng chứ KHÔNG đoán: gửi sai mã sang cơ
	quan thuế thì lỗi hiện ở bên đó, không hiện trên màn của mình.
	"""
	thay = []
	for d in dong or []:
		ma = (ma_theo_pt or {}).get((d.get("pt") or "").strip())
		ma = (ma or "").strip()
		if not ma:
			return ""
		if ma not in thay:
			thay.append(ma)
	if not thay:
		return ""
	if len(thay) == 1:
		return thay[0]
	if set(thay) <= {"TM", "CK", "TM/CK"}:
		return "TM/CK"
	return ""


def tach_theo_pt(dong, tong_don):
	"""Chia tổng đơn ra từng phương thức. THUẦN.

	Dùng cho màn chốt ca. Không có dòng nào thì trả rỗng, người gọi tự lùi
	về cách cũ là dồn cả tờ vào phương thức chính.

	Các dòng khớp tổng đơn thì lấy nguyên số của từng dòng. LỆCH thì vẫn
	chia theo TỶ LỆ của các dòng cho đủ tổng đơn, vì con số phải khớp với
	tờ hoá đơn chứ không khớp với cái bảng nhập tay; phần lệch đã có phép
	kiểm chặn từ lúc ghi sổ rồi.
	"""
	dong = dong or []
	if not dong:
		return {}
	t = tong(dong)
	tong_don = _so(tong_don)
	ra = {}
	if t <= 0:
		return {}
	if abs(t - tong_don) <= ZERO or tong_don <= 0:
		for d in dong:
			ra[d["pt"]] = round(ra.get(d["pt"], 0.0) + _so(d.get("so_tien")), 2)
		return ra
	con = tong_don
	for i, d in enumerate(dong):
		if i == len(dong) - 1:
			phan = con
		else:
			phan = round(_so(d.get("so_tien")) / t * tong_don, 2)
			con = round(con - phan, 2)
		ra[d["pt"]] = round(ra.get(d["pt"], 0.0) + phan, 2)
	return ra


# ------------------------------------------------------- phần cần Frappe

import json

import frappe
from frappe.utils import cint, flt

SI = "Sales Invoice"
BANG = "vgb_thanh_toan_nhieu"
DT_DONG = "Vagabond Dong Thanh Toan"

TRUONG_MOI = {SI: [
	{
		"fieldname": BANG, "label": "Các dòng thanh toán",
		"fieldtype": "Table", "options": DT_DONG,
		"insert_after": "vgb_pt_thanh_toan",
		"allow_on_submit": 1, "no_copy": 1,
		"description": "Khách trả một đơn bằng nhiều đường thì ghi mỗi đường "
			"một dòng. Ô Phương thức thanh toán ở trên tự mang dòng lớn nhất.",
	},
]}


def dong_cua(si):
	"""Đọc các dòng thanh toán của một hoá đơn. Trả list dict thuần."""
	if not si:
		return []
	try:
		ds = frappe.get_all(
			DT_DONG,
			filters={"parent": si, "parenttype": SI, "parentfield": BANG},
			fields=["name", "pt", "so_tien", "ma_tham_chieu", "do_may"],
			order_by="idx asc", limit_page_length=0,
		)
	except Exception:
		return []
	return [{"pt": d["pt"], "so_tien": flt(d["so_tien"]),
		"ma_tham_chieu": d.get("ma_tham_chieu") or "",
		"do_may": cint(d.get("do_may"))} for d in ds]


def bang_dong_cua(cac_si):
	"""Dòng thanh toán của NHIỀU hoá đơn, đọc một lượt.

	Màn chốt ca soi cả ca nên không thể hỏi từng tờ một. Trả về bảng
	{mã hoá đơn: [dòng]}; tờ nào không có dòng nào thì không có khoá.
	"""
	cac_si = sorted({s for s in (cac_si or []) if s})
	ra = {}
	if not cac_si:
		return ra
	for i in range(0, len(cac_si), 200):
		try:
			ds = frappe.get_all(
				DT_DONG,
				filters={"parent": ["in", cac_si[i:i + 200]],
					"parenttype": SI, "parentfield": BANG},
				fields=["parent", "pt", "so_tien", "ma_tham_chieu", "do_may"],
				order_by="parent asc, idx asc", limit_page_length=0,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "thanh_toan_nhieu: doc lo")
			continue
		for d in ds:
			ra.setdefault(d["parent"], []).append({
				"pt": d["pt"], "so_tien": flt(d["so_tien"]),
				"ma_tham_chieu": d.get("ma_tham_chieu") or "",
				"do_may": cint(d.get("do_may")),
			})
	return ra


def _doc_json(v):
	"""Man hinh gui len co the la chuoi JSON hoac list san."""
	if isinstance(v, str):
		try:
			v = json.loads(v)
		except Exception:
			return []
	if isinstance(v, dict):
		v = [v]
	return v if isinstance(v, list) else []


def ma_thue_theo_bang():
	"""Bảng {tên phương thức: mã thuế} lấy từ danh mục đang bật."""
	from vagabond import pt_thanh_toan

	ra = {}
	try:
		for p in pt_thanh_toan.ds():
			ten = (p.get("ten") or "").strip()
			if ten:
				ra[ten] = (p.get("ma_thue") or "").strip()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thanh_toan_nhieu: doc ma thue")
	return ra


def dat_pt_chinh(doc):
	"""Ô phương thức cũ luôn mang dòng LỚN NHẤT. Gọi từ hook validate.

	Không có dòng nào thì KHÔNG đụng vào ô cũ: đơn một phương thức vẫn đi
	nguyên đường cũ, và người gõ tay vẫn giữ nguyên lựa chọn của họ.
	"""
	try:
		dong = gom_dong([
			{"pt": d.get("pt"), "so_tien": d.get("so_tien"),
				"ma_tham_chieu": d.get("ma_tham_chieu"), "do_may": d.get("do_may")}
			for d in (doc.get(BANG) or [])
		])
	except Exception:
		return
	if not dong:
		return
	chinh = chinh_cua(dong)
	if chinh and (doc.get("vgb_pt_thanh_toan") or "").strip() != chinh:
		doc.vgb_pt_thanh_toan = chinh


def kiem_truoc_ghi_so(doc):
	"""Chặn ghi sổ khi các dòng không cộng đủ tổng đơn. Gọi từ before_submit.

	Vì sao chặn cứng: bảng này sinh ra để két tiền cuối ca khớp. Cho qua
	một tờ lệch thì đúng cái sai cũ quay lại, mà lần này còn khó thấy hơn
	vì nhìn vào tưởng đã tách rồi.
	"""
	dong = gom_dong([
		{"pt": d.get("pt"), "so_tien": d.get("so_tien")}
		for d in (doc.get(BANG) or [])
	])
	if not dong:
		return
	tong_don = flt(doc.get("grand_total"))
	if khop_tong(dong, tong_don):
		return
	l = lech(dong, tong_don)
	frappe.throw(
		"Các dòng thanh toán cộng lại là %s nhưng tổng đơn là %s, %s %s. "
		"Sửa lại cho khớp rồi ghi sổ."
		% (_vnd(tong(dong)), _vnd(tong_don),
			"thừa" if l > 0 else "thiếu", _vnd(abs(l)))
	)


def _vnd(so):
	return "{:,.0f}".format(flt(so)).replace(",", ".")


@frappe.whitelist()
def xem(si=None):
	"""Màn hình đọc các dòng thanh toán của một hoá đơn."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = (si or "").strip()
	if not si or not frappe.db.exists(SI, si):
		frappe.throw("Không tìm thấy hoá đơn %s." % si)
	d = frappe.db.get_value(
		SI, si, ["grand_total", "vgb_pt_thanh_toan", "docstatus"], as_dict=True)
	dong = dong_cua(si)
	return {
		"si": si, "tong_don": flt(d.grand_total),
		"pt_chinh": d.vgb_pt_thanh_toan or "",
		"da_ghi_so": 1 if cint(d.docstatus) == 1 else 0,
		"dong": dong, "tong_dong": tong(dong),
		"lech": lech(dong, d.grand_total) if dong else 0.0,
	}


@frappe.whitelist()
def luu(si=None, dong=None):
	"""Ghi lại các dòng thanh toán của một hoá đơn.

	Hoá đơn ĐÃ GHI SỔ thì không cho sửa ở đây. Đổi cách chia tiền của một
	tờ đã vào sổ là đổi số của ca đã chốt; việc đó đi đường huỷ và lập lại
	như mọi sửa đổi sau ghi sổ khác, không mở thêm một cửa lặng lẽ.
	"""
	from vagabond.ban_hang import _chuan_ma_tham_chieu, _kiem_quyen

	_kiem_quyen()
	si = (si or "").strip()
	if not si or not frappe.db.exists(SI, si):
		frappe.throw("Không tìm thấy hoá đơn %s." % si)
	doc = frappe.get_doc(SI, si)
	if cint(doc.docstatus) != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ nên không đổi cách chia tiền ở đây được. "
			"Cần sửa thì huỷ tờ rồi lập lại." % si)

	moi = gom_dong(_doc_json(dong))
	if len(moi) == 1:
		frappe.throw(
			"Chỉ có một phương thức thì không cần bảng này. Chọn thẳng ở ô "
			"Phương thức thanh toán, hoặc thêm dòng thứ hai vào.")
	for d in moi:
		if not frappe.db.exists("Mode of Payment", d["pt"]):
			frappe.throw("Phương thức %s không có trong danh mục." % d["pt"])
		# Ma tham chieu kiem theo DUNG luat cu cua tung phuong thuc, nhung
		# KHONG bat buoc: mot don tra hai duong thi duong tien mat khong co
		# ma nao ca, ma luat cu lai dang bat mot so phuong thuc phai co ma.
		d["ma_tham_chieu"] = _chuan_ma_tham_chieu(d["pt"], d.get("ma_tham_chieu"), False)

	tong_don = flt(doc.grand_total)
	if moi and not khop_tong(moi, tong_don):
		l = lech(moi, tong_don)
		frappe.throw(
			"Các dòng cộng lại là %s nhưng tổng đơn là %s, %s %s."
			% (_vnd(tong(moi)), _vnd(tong_don),
				"thừa" if l > 0 else "thiếu", _vnd(abs(l))))

	doc.set(BANG, [])
	for d in moi:
		doc.append(BANG, {
			"pt": d["pt"], "so_tien": d["so_tien"],
			"ma_tham_chieu": d["ma_tham_chieu"], "do_may": 0,
		})
	dat_pt_chinh(doc)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return xem(si)

# -*- coding: utf-8 -*-
"""Ghi sổ và xuất hoá đơn từ một hợp đồng đã ký.

VÌ SAO CÓ TỆP NÀY, ngày 28/08/2026
--------------------------------------------------------------------
Anh Việt: *"Nút 'ghi sổ và xuất hoá đơn'. Nội dung hàng hoá, số lượng sẽ
có 2 kiểu nhập: hoặc là map từ thông tin trong hợp đồng qua luôn hoặc là
điền thủ công."*

Trước đây muốn xuất hoá đơn cho một hợp đồng thì phải sang màn tạo đơn
tay, gõ lại từng dòng, rồi quay về hợp đồng bấm Gắn hoá đơn. Ba bước, ba
chỗ gõ lại, và chỗ nào cũng sai được.

HAI ĐIỀU TỆP NÀY GIỮ CHẶT
--------------------------------------------------------------------
1. GHI SỔ LÀ VIỆC CỦA KẾ TOÁN. Sales lập được tờ nháp và tờ đó nằm chờ,
   chỉ vai kế toán mới ghi sổ được. Đúng hàng rào chị Dung yêu cầu cho
   luồng mua hàng ngày 28/08/2026, và ở chiều bán ra thì càng đúng: một
   tờ hoá đơn ghi sổ là một khoản doanh thu và một tờ hoá đơn điện tử
   sắp gửi cơ quan thuế.

2. LỆCH VỚI GIÁ TRỊ HỢP ĐỒNG THÌ DỪNG LẠI. Hợp đồng đã ký là con số đã
   cam kết với khách. Xuất hoá đơn lệch với nó là chỗ hay sinh tranh cãi
   nhất khi đối chiếu cuối năm, nên máy phải hỏi lại chứ không lặng lẽ
   cho qua.
"""

# Lệch bao nhiêu đồng thì còn coi là làm tròn, quá thì phải hỏi lại. Một
# nghìn đồng: đủ rộng cho sai số làm tròn thuế của ERPNext, đủ hẹp để
# không nuốt một dòng hàng bị gõ thiếu.
NGUONG_LECH = 1000


def lech_qua_nguong(tong_hang, gia_tri_hd, nguong=NGUONG_LECH):
	"""Cộng tiền hàng có lệch với giá trị hợp đồng quá ngưỡng không. THUẦN."""
	try:
		return abs(float(tong_hang or 0) - float(gia_tri_hd or 0)) > float(nguong)
	except Exception:
		return False


def loi_lech(tong_hang, gia_tri_hd):
	"""Câu hỏi lại khi cộng tiền hàng lệch với hợp đồng. THUẦN."""
	def _t(v):
		try:
			return "{:,.0f}".format(float(v or 0)).replace(",", ".")
		except Exception:
			return "0"

	lech = float(tong_hang or 0) - float(gia_tri_hd or 0)
	huong = "cao hơn" if lech > 0 else "thấp hơn"
	return (
		"Cộng tiền hàng là %s đ, %s giá trị hợp đồng (%s đ) %s đ.\n\n"
		"Hợp đồng đã ký là con số đã cam kết với khách. Anh chị kiểm lại các dòng "
		"hàng, hoặc bấm tiếp nếu biết rõ vì sao lệch."
		% (_t(tong_hang), huong, _t(gia_tri_hd), _t(abs(lech)))
	)


def loi_chua_ghi_so_duoc():
	"""Câu chặn khi người bấm không có quyền ghi sổ. THUẦN."""
	return (
		"Chỉ kế toán mới ghi sổ hoá đơn bán hàng được. Anh chị bấm "
		'"Lập hoá đơn nháp" để dựng tờ hoá đơn, kế toán sẽ ghi sổ và xuất hoá đơn '
		"điện tử."
	)


def loi_khong_co_bao_gia(ma):
	"""Câu giải thích khi hợp đồng không có báo giá gốc để lấy hàng. THUẦN."""
	return (
		"Hợp đồng %s không có báo giá gốc nên không lấy hàng tự động được. "
		"Anh chị chuyển sang kiểu Gõ tay và nhập từng dòng hàng." % (ma or "")
	)


def cong_tien(dong):
	"""Cộng thành tiền của các dòng hàng. THUẦN.

	Tính lại từ số lượng và đơn giá chứ không tin ô thành tiền màn hình
	gửi lên: màn hình làm tròn để hiển thị, tin nó là cộng ra một con số
	khác con số ERPNext sẽ ghi.
	"""
	tong = 0.0
	for d in dong or []:
		d = d or {}
		try:
			sl = float(d.get("so_luong") or 0)
			gia = float(d.get("don_gia") or 0)
			ck = float(d.get("chiet_khau") or 0)
		except Exception:
			continue
		if sl <= 0:
			continue
		tong += sl * gia * (1.0 - ck / 100.0)
	return round(tong, 2)


def dong_hop_le(dong):
	"""Lọc các dòng hàng dùng được, và kể ra dòng nào bị bỏ vì sao. THUẦN.

	Trả về (danh sách dòng dùng được, danh sách câu nhắc).
	"""
	ok, nhac = [], []
	for i, d in enumerate(dong or [], 1):
		d = d or {}
		ten = str(d.get("ten_mon") or d.get("ma_mon") or "").strip()
		try:
			sl = float(d.get("so_luong") or 0)
		except Exception:
			sl = 0
		if not ten:
			nhac.append("Dòng %d chưa có tên món nên máy bỏ qua." % i)
			continue
		if sl <= 0:
			nhac.append("Dòng %d (%s) có số lượng bằng 0 nên máy bỏ qua." % (i, ten))
			continue
		ok.append(d)
	return ok, nhac


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, flt, nowdate

DT_HD = "Hop Dong Ban Hang"

# Trang thai hop dong duoc phep xuat hoa don. Giong het danh sach ben
# `thu_hop_dong`, va co y giong: mot khi chua chot con so thi khong thu
# tien duoc ma cung khong xuat hoa don duoc.
TT_HD_XUAT_DUOC = ("Dang thuc hien", "Hoan tat", "Da thanh ly")


def _quyen():
	from vagabond.hop_dong import _quyen as q

	q()


def _ghi_so_duoc():
	from vagabond.doi_chieu_mua import VAI_GHI_SO

	return bool(VAI_GHI_SO & set(frappe.get_roles()))


def _hop_dong(ten):
	if not ten or not frappe.db.exists(DT_HD, ten):
		frappe.throw("Không tìm thấy hợp đồng %s." % (ten or "(trống)"))
	return frappe.get_doc(DT_HD, ten)


@frappe.whitelist()
def dong_tu_hop_dong(hop_dong=None):
	"""Đọc các dòng hàng từ báo giá gốc của hợp đồng.

	Giữ nguyên mã món, đơn vị, số lượng, đơn giá, chiết khấu và thuế suất
	CỦA TỪNG DÒNG. Không gộp, không tính lại: báo giá là thứ khách đã đọc
	và đã đồng ý, hoá đơn phải soi lại được vào đó.
	"""
	_quyen()
	hd = _hop_dong(hop_dong)
	bg = hd.get("bao_gia") or ""
	if not bg or not frappe.db.exists("Bao Gia Ban Hang", bg):
		return {
			"co": 0,
			"vi_sao": loi_khong_co_bao_gia(hd.get("so_hop_dong") or hd.name),
			"dong": [],
			"gia_tri_hd": flt(hd.gia_tri),
			"ghi_so_duoc": 1 if _ghi_so_duoc() else 0,
		}
	q = frappe.get_doc("Bao Gia Ban Hang", bg)
	dong = []
	for r in q.get("dong") or []:
		ma = r.get("ma_mon") or r.get("ma_tv") or ""
		dong.append({
			"ma_mon": ma,
			"ten_mon": r.get("ten_mon") or ma,
			"dvt": r.get("dvt") or "",
			"so_luong": flt(r.get("so_luong")),
			"don_gia": flt(r.get("don_gia")),
			"chiet_khau": flt(r.get("chiet_khau")),
			"thue_pt": flt(r.get("thue_pt")) or flt(q.get("thue_pt")),
			"co_ma": 1 if (ma and frappe.db.exists("Item", ma)) else 0,
		})
	tong = cong_tien(dong)
	return {
		"co": 1,
		"bao_gia": bg,
		"dong": dong,
		"tong_hang": tong,
		"gia_tri_hd": flt(hd.gia_tri),
		"lech": 1 if lech_qua_nguong(tong, hd.gia_tri) else 0,
		"cau_lech": loi_lech(tong, hd.gia_tri) if lech_qua_nguong(tong, hd.gia_tri) else "",
		"ten_khach": hd.get("ten_khach") or hd.get("khach_hang") or "",
		"khach_hang": hd.get("khach_hang") or "",
		"email": hd.get("email") or "",
		"ma_so_thue": hd.get("ma_so_thue") or "",
		"ghi_so_duoc": 1 if _ghi_so_duoc() else 0,
		"trang_thai": hd.trang_thai,
		"xuat_duoc": 1 if hd.trang_thai in TT_HD_XUAT_DUOC else 0,
	}


@frappe.whitelist()
def ghi_so(hop_dong=None, dong=None, ghi_so_luon=1, xuat_hddt=1, xac_nhan_lech=0, xhd_ten=None):
	"""Lập hoá đơn bán hàng cho hợp đồng, ghi sổ, rồi đẩy hoá đơn điện tử.

	Bốn nhịp, và mỗi nhịp hỏng thì dừng ở đó chứ không đi tiếp:
	  1. lập tờ nháp, gắn số hợp đồng
	  2. ghi sổ, nếu người bấm có quyền và có yêu cầu
	  3. đẩy sang m-invoice ở trạng thái chờ ký
	  4. ghi vết vào hợp đồng
	"""
	_quyen()
	hd = _hop_dong(hop_dong)
	if hd.trang_thai not in TT_HD_XUAT_DUOC:
		frappe.throw(
			"Hợp đồng đang ở trạng thái chưa chốt nên chưa xuất hoá đơn được. "
			"Chuyển sang Đang thực hiện rồi bấm lại.",
			title="Chưa xuất hoá đơn được",
		)

	if isinstance(dong, str):
		try:
			dong = frappe.parse_json(dong)
		except Exception:
			dong = []
	dong, nhac = dong_hop_le(dong or [])
	if not dong:
		frappe.throw("Chưa có dòng hàng nào dùng được. Anh chị kiểm lại danh sách hàng.")

	tong = cong_tien(dong)
	if lech_qua_nguong(tong, hd.gia_tri) and not cint(xac_nhan_lech):
		frappe.throw(loi_lech(tong, hd.gia_tri), title="Lệch với giá trị hợp đồng")

	muon_ghi_so = cint(ghi_so_luon)
	if muon_ghi_so and not _ghi_so_duoc():
		frappe.throw(loi_chua_ghi_so_duoc(), title="Chưa đủ quyền ghi sổ")

	si = frappe.new_doc("Sales Invoice")
	si.customer = _khach(hd)
	si.posting_date = nowdate()
	si.set_posting_time = 1
	si.due_date = nowdate()
	si.custom_hop_dong = hd.name
	si.custom_nguon = "Hop dong"
	if si.meta.has_field("vgb_xhd_ten"):
		si.vgb_xhd_ten = (xhd_ten or hd.get("ten_khach") or "").strip() or None
	for d in dong:
		si.append("items", _dong_si(d))
	_dat_thue(si, dong)
	si.flags.ignore_permissions = True
	si.insert(ignore_permissions=True)

	ket = {"hoa_don": si.name, "nhac": nhac, "ghi_so": 0, "hddt": ""}
	if muon_ghi_so:
		si.submit()
		ket["ghi_so"] = 1
		if cint(xuat_hddt):
			try:
				from vagabond.ban_hang import _tu_xuat_hddt

				ok, ghi = _tu_xuat_hddt(si.name)
				ket["hddt"] = "Đã đẩy hoá đơn điện tử, đang chờ ký." if ok else (ghi or "")
			except Exception:
				frappe.log_error(frappe.get_traceback(), "hop_dong_hoa_don: xuat HDDT loi")
				ket["hddt"] = "Chưa đẩy được hoá đơn điện tử, kế toán xuất tay giúp."
	frappe.db.commit()

	try:
		hd.add_comment("Comment", "Lập hoá đơn %s từ hợp đồng%s." % (
			si.name, ", đã ghi sổ" if ket["ghi_so"] else ", còn nháp chờ kế toán"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_hoa_don: ghi vet")
	return ket


def _khach(hd):
	"""Khách hàng của hoá đơn. Ưu tiên mã đã gắn trên hợp đồng."""
	ma = (hd.get("khach_hang") or "").strip()
	if ma and frappe.db.exists("Customer", ma):
		return ma
	ten = (hd.get("ten_khach") or "").strip()
	if ten:
		co = frappe.db.get_value("Customer", {"customer_name": ten}, "name")
		if co:
			return co
	frappe.throw(
		"Hợp đồng chưa gắn khách hàng nào bên Next nên chưa lập hoá đơn được. "
		"Anh chị mở hợp đồng và chọn khách hàng, hoặc nhờ chị Dung tạo hồ sơ khách."
	)


def _dong_si(d):
	"""Một dòng hàng của hoá đơn.

	Món không có trong danh mục thì KHÔNG tự đẻ mã mới: đưa vào dòng dịch
	vụ dùng chung, giữ nguyên tên người gõ. Đẻ mã tự động là cách nhanh
	nhất để danh mục 1.428 mã thành 1.600 mã rác.
	"""
	from vagabond.ban_hang import MA_PHI_GIAO

	ma = str(d.get("ma_mon") or "").strip()
	ten = str(d.get("ten_mon") or ma).strip()
	hang = {
		"qty": flt(d.get("so_luong")),
		"rate": flt(d.get("don_gia")),
		"description": ten,
	}
	if d.get("chiet_khau"):
		hang["discount_percentage"] = flt(d.get("chiet_khau"))
	if ma and frappe.db.exists("Item", ma):
		hang["item_code"] = ma
	else:
		hang["item_code"] = MA_PHI_GIAO if _la_phi_giao(ten) else _item_dich_vu()
		hang["item_name"] = ten[:140]
	if d.get("dvt"):
		hang["uom"] = d.get("dvt")
	return hang


def _la_phi_giao(ten):
	t = str(ten or "").lower()
	return "vận chuyển" in t or "giao hàng" in t or "phí giao" in t


def _item_dich_vu():
	"""Mã dịch vụ dùng chung cho dòng gõ tay không khớp danh mục."""
	from vagabond.ban_hang import _item_phi_giao

	return _item_phi_giao()


def _dat_thue(si, dong):
	"""Dòng thuế của hoá đơn, theo thuế suất chung của các dòng hàng.

	Các dòng cùng thuế suất thì đặt một dòng thuế. Lệch thuế suất giữa các
	dòng thì để ERPNext tự lo qua Item Tax Template, không tự dựng nhiều
	dòng thuế ở đây - dựng tay là chỗ dễ ra sai số thuế nhất.
	"""
	suat = {flt(d.get("thue_pt")) for d in dong if flt(d.get("thue_pt")) > 0}
	if len(suat) != 1:
		return
	ts = list(suat)[0]
	tk = frappe.db.get_value(
		"Account", {"name": ["like", "33311%"], "company": si.company}, "name"
	) or frappe.db.get_value(
		"Account", {"account_name": ["like", "%GTGT%đầu ra%"], "company": si.company}, "name"
	)
	if not tk:
		return
	si.append("taxes", {
		"charge_type": "On Net Total",
		"account_head": tk,
		"rate": ts,
		"description": "Thuế GTGT %g%%" % ts,
	})

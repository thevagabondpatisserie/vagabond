# -*- coding: utf-8 -*-
"""Tiền chuyển khoản về đủ thì máy TỰ CHỐT bill tạm tính (v678).

ANH VIỆT 20/11/2026
-------------------
*"hiện tại nếu như khách muốn thanh toán tại quầy thông qua phương thức O2O
thì thu ngân vẫn đang phải đối soát tay. Có thể làm phần này cho đối soát
thành tự động luôn được không?"* rồi chốt: *"Anh chốt phương án là hệ thống
sẽ tự chốt luôn."*

Bill tạm tính (bàn gọi món qua QR, hay bill quầy đã in tạm tính) mang mã bill
TCVxxxxx. Mã QR chuyển khoản, nút mở app ngân hàng trên trang khách và tờ tạm
tính đều điền mã đó vào nội dung. SePay báo một dòng tiền vào có mã đó, tổng
tiền của mã đủ bằng tổng bill, thì máy làm đúng việc thu ngân vẫn làm bằng
nút Chốt: ghi phương thức chuyển khoản, mã tham chiếu là mã bill, bỏ dấu tạm
tính. Ghi sổ vẫn đi đường cũ (nhịp ghi sổ, cửa _chuan_bi_ghi_so kiểm tiền lại
lần nữa), nên bước này KHÔNG ghi sổ, không xuất hoá đơn.

Phương thức theo NƠI TIỀN VỀ (pt_ck.ck_cua_tk): về tài khoản Shinhan là
"Chuyển khoản - Shinhan", về MB là "Chuyển khoản". Bill không bao giờ mang
phương thức lệch với ngân hàng thật.

KHÔNG tự chốt khi (dừng, để thu ngân xử lý như cũ):
  - bill không còn tạm tính, đã huỷ, đã ghi sổ;
  - bill đã chia nhiều dòng thanh toán (thu ngân đang tự chia);
  - tiền chưa đủ, hoặc dòng sao kê đã thuộc chứng từ khác;
  - tiền về hai ngân hàng khác nhau cho một bill (không đoán phương thức);
  - ưu đãi khách chọn đổi số giảm lúc tính lại (uu_dai_ban.truoc_chot dừng
    chốt để báo khách số mới).

Hai cửa gọi vào, cùng một hàm thu_chot:
  1. sepay._webhook sau khi ghi dòng sao kê (khi_co_giao_dich, xếp hàng đợi).
  2. trang khách hỏi trạng thái chuyển khoản (ck_ban.trang_thai), lưới an toàn
     khi hàng đợi chậm.
Nạp bù sao kê bằng tay (nhap_sao_ke) KHÔNG tự chốt: dòng cũ nạp lại không được
lặng lẽ chốt bill tạm tính của ngày cũ; thu ngân, kế toán chốt bằng nút như cũ.
"""

import frappe
from frappe.utils import cint, flt, now_datetime

from vagabond import ma_bill, pt_ck

SI = "Sales Invoice"
BT = "Bank Transaction"
SAI_SO = 1.0


# ------------------------------------------------------------------ THUẦN


def ma_trong_mo_ta(mo_ta):
	"""Các mã bill trong nội dung một dòng sao kê, bỏ trùng, giữ thứ tự. THUẦN."""
	ra = []
	for m in ma_bill.RE_MA.findall(str(mo_ta or "").upper()):
		if m not in ra:
			ra.append(m)
	return ra


def ly_do_khong_chot(b, nhan, so_dong_tach, pts, co_chu):
	"""Vì sao KHÔNG tự chốt một bill; rỗng là chốt được. THUẦN.

	b             dict bill: docstatus, vgb_tam_tinh, vgb_huy, grand_total
	nhan          tổng tiền SePay đã nhận cho mã bill
	so_dong_tach  số dòng thanh toán chia nhiều đường của bill
	pts           tập phương thức chuyển khoản suy ra từ nơi tiền về
	co_chu        dòng sao kê đã thuộc chứng từ khác chưa
	"""
	if cint(b.get("docstatus")) != 0 or cint(b.get("vgb_huy")):
		return "khong_mo"
	if not cint(b.get("vgb_tam_tinh")):
		return "da_chot"
	if so_dong_tach:
		return "chia_dong"
	tong = flt(b.get("grand_total"))
	if tong <= 0:
		return "khong_tien"
	if flt(nhan) < tong - SAI_SO:
		return "chua_du"
	if co_chu:
		return "gd_co_chu"
	if len(pts or ()) != 1 or "" in pts:
		return "nhieu_tk"
	return ""


def ghi_chu_chot(nhan, ds_gd, luc):
	"""Dòng ghi chú đối soát khi máy tự chốt. THUẦN. Không tên người."""
	return "Hệ thống tự chốt lúc %s: ngân hàng nhận đủ %s đ (giao dịch %s)." % (
		luc, "{:,.0f}".format(flt(nhan)).replace(",", "."), ", ".join(ds_gd or []) or "không rõ")


# ------------------------------------------------------------ phần chạm hệ


def khi_co_giao_dich(ma_bt):
	"""sepay._webhook gọi ngay sau khi ghi dòng sao kê. Không bao
	giờ ném lỗi ra ngoài: dòng tiền đã ghi xong, hỏng phản hồi là SePay gửi lại
	mãi. Chỉ xếp hàng đợi (sau commit), không chốt trong yêu cầu webhook."""
	try:
		g = frappe.db.get_value(BT, ma_bt, ["deposit", "description", "reference_number"], as_dict=True)
		if not g or flt(g.get("deposit")) <= 0:
			return []
		ds = ma_trong_mo_ta("%s %s" % (g.get("description") or "", g.get("reference_number") or ""))
		for ma in ds:
			frappe.enqueue("vagabond.tu_chot_ck.chot_theo_ma", queue="short", timeout=120,
				enqueue_after_commit=True, job_id="tu_chot_ck:%s" % ma, deduplicate=True, ma=ma)
		return ds
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tu_chot_ck: xếp hàng tự chốt lỗi")
		return []


def bill_mo_theo_ma(ma):
	"""Tên bill tạm tính còn mở mang mã bill `ma`, hoặc rỗng."""
	ma = str(ma or "").strip().upper()
	if not ma_bill.hop_le(ma):
		return ""
	return frappe.db.get_value(SI, {"custom_pancake_display_id": ma, "docstatus": 0,
		"vgb_tam_tinh": 1, "vgb_huy": 0}, "name") or ""


def chot_theo_ma(ma):
	"""Việc trong hàng đợi: tìm bill tạm tính mang mã này rồi thử chốt."""
	ten = bill_mo_theo_ma(ma)
	if not ten:
		return {"ok": 0, "ly_do": "khong_co_bill"}
	try:
		return thu_chot(ten)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "tu_chot_ck: tự chốt bill %s lỗi" % ten)
		return {"ok": 0, "ly_do": "loi"}


def _ba_cua_gd(ds_gd):
	if not ds_gd:
		return []
	return [r[0] for r in frappe.db.sql(
		"select bank_account from `tabBank Transaction` where name in %(ds)s", {"ds": tuple(ds_gd)})]


def thu_chot(ten):
	"""Khoá bill, đọc lại MỌI thứ sau khoá, đủ điều kiện thì chốt. Trả
	{"ok": 1, "pt": ...} khi đã chốt, {"ok": 0, "ly_do": ...} khi không."""
	from vagabond import ban_hang, doi_soat_sepay, pt_thanh_toan, uu_dai_ban
	from vagabond import thanh_toan_nhieu as ttn
	from vagabond.tra_truoc_khach import chon_pt_ca_don

	# Khoá trước, đọc sau (sổ mẫu lỗi loại 1): hai cửa (webhook, trang khách)
	# cùng tới thì cửa sau chờ, đọc lại thấy bill đã chốt và dừng.
	si = frappe.get_doc(SI, ten, for_update=True)
	ma = str(si.get("custom_pancake_display_id") or "").strip().upper()
	if not ma_bill.hop_le(ma):
		return {"ok": 0, "ly_do": "khong_ma"}
	g = ban_hang._sepay_bill(ma) if ma else {}
	ds_gd = list(g.get("gd") or [])
	chu = doi_soat_sepay.chu_cua_giao_dich(ds_gd, bo_qua_hoa_don=si.name) if ds_gd else {}
	ba_sh = pt_thanh_toan.ba_shinhan()
	# Codex #597 vòng 1 (cùng loại, quét thêm): giao dịch thiếu tài khoản thì
	# không biết tiền về đâu, giữ "" để ly_do_khong_chot không tự chốt.
	pts = {pt_ck.ck_cua_tk(b, ba_sh) for b in _ba_cua_gd(ds_gd)}
	b = {k: si.get(k) for k in ("docstatus", "vgb_tam_tinh", "vgb_huy", "grand_total")}
	ly = ly_do_khong_chot(b, g.get("nhan"), len(ttn.dong_cua(si.name)), pts, bool(chu))
	if ly:
		return {"ok": 0, "ly_do": ly, "nhan": flt(g.get("nhan"))}
	pt = pts.pop()
	if pt not in ban_hang._pt_cho_nguon(si.get("custom_nguon")):
		return {"ok": 0, "ly_do": "pt_sai_nguon"}
	with uu_dai_ban._luu_bang_quyen_he_thong():
		try:
			kq_ud = uu_dai_ban.truoc_chot(si) if cint(si.get("vgb_tam_tinh")) else None
		except uu_dai_ban.UuDaiDoi:
			# truoc_chot đã lưu số giảm mới và commit; khách thấy tổng mới.
			return {"ok": 0, "ly_do": "ud_doi"}
		if flt(g.get("nhan")) < flt(si.grand_total) - SAI_SO:
			return {"ok": 0, "ly_do": "chua_du", "nhan": flt(g.get("nhan"))}
		chon_pt_ca_don(si, pt)
		si.vgb_ma_tham_chieu = ma
		si.vgb_tam_tinh = 0
		dong = ghi_chu_chot(g.get("nhan"), ds_gd, str(now_datetime())[11:16])
		co = (si.get("vgb_ghi_chu_doi_soat") or "").strip()
		si.vgb_ghi_chu_doi_soat = (co + " | " + dong) if co else dong
		si.flags.ignore_permissions = True
		si.save(ignore_permissions=True)
		uu_dai_ban.sau_chot(si, kq_ud)
		ban_hang._ghi_vet(si.name, "Tự chốt bill %s bằng %s: %s" % (ma, pt, dong), "hệ thống tự chốt khi tiền về")
		_bao_quay(si, pt)
	frappe.db.commit()
	return {"ok": 1, "pt": pt, "name": si.name, "ma": ma}


def _bao_quay(si, pt):
	"""Tin Zalo nhóm quầy: bàn nào đã chuyển khoản, bill đã tự chốt. Không số
	tiền (luật v613, kenh_zalo.bo_dong_tien)."""
	try:
		from vagabond import diem_ban, kenh_zalo
		from vagabond.lien_ket_app import goc_app

		d = diem_ban.theo_ma(si.get("vgb_quay")) or {}
		ban = str(si.get("vgb_so_ban") or "").strip()
		noi = d.get("ten_ngan") or d.get("ten") or si.get("vgb_quay") or ""
		tieu_de = ("Bàn %s đã chuyển khoản, bill tự chốt" % ban) if ban else "Bill đã chuyển khoản, tự chốt"
		dong = ["Bill %s%s, %s." % (si.get("custom_pancake_display_id") or si.name,
			(" tại " + noi) if noi else "", pt),
			"Ngân hàng đã nhận đủ, quầy không cần thu nữa."]
		kenh_zalo.bao("thong_bao", "ban_hang", tieu_de, dong, link=goc_app() + "/ban-tai-quay",
			khoa="tu-chot-ck:%s" % si.name, nguon=si.name, ma_tin="bh_ban_da_chuyen_khoan")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tu_chot_ck: báo quầy lỗi")

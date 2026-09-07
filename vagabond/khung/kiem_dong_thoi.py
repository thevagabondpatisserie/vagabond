# -*- coding: utf-8 -*-
"""Kiểm HAI KẾT NỐI CÙNG LÚC trên site THỬ. Có commit thật. KHÔNG chạy trên production.

Vì sao tách khỏi kiem_that/
---------------------------
Bộ `kiem_that` chạy trong một điểm lưu của MỘT kết nối và cấm commit, nên nó
không dựng được cảnh hai request đua nhau: hai kết nối chỉ nhìn thấy nhau
qua dữ liệu đã commit. Codex (PR #222 và #224, 07/09/2026) đòi đúng cảnh đó:

  1. Hai kết nối gửi CÙNG mã lần nhận qua `lan_nhan.nhan_theo_phieu`. Phải ra
     đúng MỘT Stock Entry, cả hai nhận cùng tên phiếu, sổ kho trừ một lần, MR
     nhảy một lần.
  2. Một kết nối đếm tay (`kiem_banh.luu_o`) và một kết nối chốt ngày
     (`kiem_banh.chot_ngay`) cùng lúc trên cùng dòng ngày mai. Số đếm không
     được mất trong im lặng: bên thua phải nhận lỗi rõ (TimestampMismatchError)
     hoặc số đếm vẫn còn nguyên với nguồn "Da kiem dem".

Cách chạy (từ thư mục sites của bench, bằng python của bench):

    ../env/bin/python ../apps/vagabond/vagabond/khung/kiem_dong_thoi.py <site> lan_nhan
    ../env/bin/python ../apps/vagabond/vagabond/khung/kiem_dong_thoi.py <site> kiem_banh [so_vong]

Tệp TỰ TỪ CHỐI chạy nếu tên site không chứa "kiem" hoặc "test", trừ khi đặt
VGB_SITE_THU=1. Dữ liệu tạo ra được dọn ở cuối (huỷ và xoá phiếu), nhưng đây
vẫn là site thử, không phải site thật.

Mỗi kết nối là một TIẾN TRÌNH riêng (multiprocessing), có frappe.init và
frappe.connect riêng, chờ nhau ở một Barrier rồi gọi cùng lúc, mỗi bên tự
commit. Tiến trình cha đọc lại bằng kết nối thứ ba.
"""

import json
import multiprocessing as mp
import os
import sys
import time
import traceback

# ------------------------------------------------------------------ nền


def _mo(site):
	import frappe

	frappe.init(site=site)
	frappe.connect()
	frappe.set_user("Administrator")
	return frappe


def _cho_phep(site):
	if os.environ.get("VGB_SITE_THU") == "1":
		return True
	t = (site or "").lower()
	return "kiem" in t or "test" in t


def _con(site, ten, hang_rao, kq, ham, *a):
	"""Thân một tiến trình con: mở kết nối, chờ hàng rào, gọi, commit, báo về."""
	try:
		frappe = _mo(site)
		hang_rao.wait(timeout=30)
		t0 = time.time()
		try:
			ra = ham(frappe, *a)
			frappe.db.commit()
			kq.put({"ten": ten, "ok": 1, "ra": ra, "ms": int((time.time() - t0) * 1000)})
		except Exception as e:
			frappe.db.rollback()
			kq.put({"ten": ten, "ok": 0, "loi": "%s: %s" % (type(e).__name__, str(e)[:300]),
				"ms": int((time.time() - t0) * 1000)})
	except Exception:
		kq.put({"ten": ten, "ok": 0, "loi": traceback.format_exc()[-800:]})


def _chay_song_song(site, viec):
	"""viec: [(ten, ham, args...)]. Trả về kết quả theo tên."""
	# "spawn" chứ KHÔNG "fork": con fork thừa kế kết nối MySQL của cha, khi con
	# mở kết nối riêng thì kết nối thừa kế bị thu dọn và gửi COM_QUIT trên cùng
	# socket, cha đọc lại sẽ gặp (2006, 'Server has gone away').
	ctx = mp.get_context("spawn")
	hang_rao = ctx.Barrier(len(viec))
	kq = ctx.Queue()
	ps = []
	for v in viec:
		p = ctx.Process(target=_con, args=(site, v[0], hang_rao, kq, v[1]) + tuple(v[2:]))
		p.start()
		ps.append(p)
	ra = {}
	for _ in viec:
		r = kq.get(timeout=120)
		ra[r["ten"]] = r
	for p in ps:
		p.join(timeout=10)
	return ra


# ------------------------------------------------------ 1. lan_nhan cùng mã


def _goi_nhan(frappe, ma_lan, mr, tu_kho, den_kho, ma, so, cty):
	from vagabond import lan_nhan

	# Gửi đúng như màn hình gửi: có uom và material_request_item. Thiếu
	# material_request_item thì ERPNext validate_with_material_request tìm
	# không ra dòng MR và đổ AttributeError 'NoneType' ... 'item_code'.
	dong_mr = frappe.db.get_value("Material Request Item", {"parent": mr, "item_code": ma}, "name")
	return lan_nhan.nhan_theo_phieu(
		ma_lan_nhan=ma_lan, phieu=mr, kho_xuat=tu_kho, kho_nhan=den_kho, cong_ty=cty,
		dong=[{
			"item_code": ma, "qty": so, "uom": frappe.db.get_value("Item", ma, "stock_uom"),
			"conversion_factor": 1, "material_request": mr, "material_request_item": dong_mr,
		}],
	)


def kiem_lan_nhan(site):
	"""Hai kết nối, cùng mã lần nhận, cùng lúc."""
	frappe = _mo(site)
	from frappe.utils import add_days, nowdate
	from vagabond.khung.kiem_that import nen, thu_nhan_nvl as t

	cty = nen.cong_ty()
	tu_kho = nen.mot_kho(cty)
	den_kho = t._kho_nhan(cty)
	t._bat_serial_batch_neu_chua()
	ma = t._mon_theo_lo("KTDT-NVL-DONG-THOI")
	lo = t._lo(ma, "KTDT-LO-A", add_days(nowdate(), 30))
	nhap = t._nhap(ma, tu_kho, [(lo, 200)], cty)
	mr = t._yeu_cau(ma, tu_kho, den_kho, 100, cty)
	frappe.db.commit()
	ma_lan = "KTDT-LAN-%d" % int(time.time())
	so_se_truoc = frappe.db.count("Stock Entry", {"vgb_ma_lan_nhan": ma_lan})
	so_sle_truoc = frappe.db.count("Stock Ledger Entry", {"is_cancelled": 0})

	ra = _chay_song_song(site, [
		("A", _goi_nhan, ma_lan, mr.name, tu_kho, den_kho, ma, 30, cty),
		("B", _goi_nhan, ma_lan, mr.name, tu_kho, den_kho, ma, 30, cty),
	])

	frappe.db.commit()  # mở snapshot mới để đọc số liệu đã commit của hai con
	se = frappe.get_all("Stock Entry", filters={"vgb_ma_lan_nhan": ma_lan}, fields=["name", "docstatus"])
	sle = frappe.db.count("Stock Ledger Entry", {"is_cancelled": 0}) - so_sle_truoc
	mr_doc = frappe.get_doc("Material Request", mr.name)
	ket = {
		"ma_lan": ma_lan,
		"A": ra.get("A"), "B": ra.get("B"),
		"so_se_cung_ma": len(se) - so_se_truoc,
		"se": se,
		"sle_them": sle,
		"mr_ordered": float(mr_doc.items[0].ordered_qty or 0),
		"ton_kho_xuat": t._ton_kho(ma, tu_kho),
	}
	ten = set()
	for k in ("A", "B"):
		if ra[k].get("ok"):
			ten.add(ra[k]["ra"]["name"])
	ket["dat"] = bool(
		ket["so_se_cung_ma"] == 1
		and all(ra[k].get("ok") for k in ("A", "B"))
		and len(ten) == 1
		and ket["sle_them"] == 2
		and ket["mr_ordered"] == 30.0
		and ket["ton_kho_xuat"] == 170.0
	)
	print(json.dumps(ket, ensure_ascii=False, indent=1, default=str))

	# Dọn: HUỶ những gì vừa tạo trên site thử. Không xoá: hook on_trash
	# chung_tu.chan_xoa chặn xoá mọi chứng từ (kể cả force=1), xoá sẽ ném lỗi
	# và cuốn cả phần huỷ vào rollback. Phiếu huỷ vẫn giữ mã lần nhận, nên
	# xoá mã đi để không chiếm chỗ trên khoá duy nhất và không để rác KTDT-LAN.
	try:
		for x in se:
			d = frappe.get_doc("Stock Entry", x["name"])
			if d.docstatus == 1:
				d.cancel()
			frappe.db.set_value("Stock Entry", d.name, "vgb_ma_lan_nhan", None, update_modified=False)
		mr_doc.reload()
		if mr_doc.docstatus == 1:
			mr_doc.cancel()
		nhap.reload()
		nhap.cancel()
		frappe.db.commit()
		print("don dep xong (da huy, khong xoa)")
	except Exception as e:
		frappe.db.rollback()
		print("DON DEP CHUA HET: %s" % e)
	return ket["dat"]


if __name__ == "__main__":
	if len(sys.argv) < 3:
		print(__doc__)
		sys.exit(2)
	site, viec = sys.argv[1], sys.argv[2]
	if not _cho_phep(site):
		print("TU CHOI: site %r khong giong site thu. Dat VGB_SITE_THU=1 neu chac chan." % site)
		sys.exit(3)
	if viec == "lan_nhan":
		ok = kiem_lan_nhan(site)
	else:
		print("viec phai la lan_nhan")
		sys.exit(2)
	sys.exit(0 if ok else 1)

# -*- coding: utf-8 -*-
"""Đột biến cho v602 (chuỗi cuối ngày đi từng đơn), đọc theo AGENTS điều 17.

Mỗi đột biến làm hỏng lại đúng một chỗ, khẳng định mẫu khớp ĐÚNG MỘT lần,
chạy bộ ca liên quan, rồi trả tệp về như cũ. In thật số bắt được.

Chạy:  python3 vagabond/khung/kiem_thu/dot_bien_chuoi_602.py
"""

import io
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BH = "vagabond/ban_hang.py"
HB = "vagabond/hddt_bu.py"
KZ = "vagabond/kenh_zalo.py"
CA = [sys.executable, "-c", (
	"import sys; sys.path.insert(0, %r)\n"
	"from vagabond.khung.kiem_thu import thu_cach_ly_243\n"
	"from vagabond.khung.kiem_thu import nen; nen.gia_lap()\n"
	"from vagabond.khung.kiem_thu import thu_chuoi_tung_don_602, thu_ghi_so_266, thu_hddt_bu, thu_hang_tang\n"
	"sys.exit(1 if nen.chay_het(im=True) else 0)" % GOC)]

DOT_BIEN = [
	("chuỗi không xếp đơn nào", BH,
		'	xong = _xep_ghi_so(ds, ngay, cho_xuat=cho_xuat, nguon="vet" if (da_du_chuoi and not chay_tay) else "cuoi-ngay")',
		"	xong = 0"),
	("chuỗi không đặt cờ ngày", BH,
		'		frappe.db.set_single_value("Vagabond Settings", "tu_ghi_so_lan_cuoi", ngay)\n		frappe.db.commit()\n\n	# Nhip VET',
		'		pass\n\n	# Nhip VET'),
	# Codex #488 vòng 2: phát hành phải đợi các lượt ghi sổ riêng xong.
	("chuỗi phát hành thẳng, không đợi lượt riêng", BH,
		"		cho_ghi_so_roi_phat_hanh(str(ngay), ds, cho_xuat=cho_xuat)\n		return\n",
		"		phat_hanh_cuoi_ngay(str(ngay), xong, 0)\n		return\n"),
	("xuất rải hoãn báo số đã xếp như cũ", BH,
		'		_giao_luot_cho(ngay, chon, cho_xuat, "xuat-rai",\n			"vgb-cho-xuat-rai-%s" % now_datetime().strftime("%Y%m%d%H%M"))',
		'		_bao_hoan_phat_hanh(ngay, len(chon), [], "xuat-rai") if not cho_xuat else _giao_luot_cho(ngay, chon, cho_xuat, "xuat-rai", "x")'),
	("lượt chờ báo hoãn mất nhãn nơi gọi", BH,
		"		_bao_hoan_phat_hanh(ngay, da_ghi, con, noi_goi)",
		'		_bao_hoan_phat_hanh(ngay, da_ghi, con, "cuoi-ngay")'),
	("giao lượt chờ lên hàng đợi mặc định 300 giây", BH,
		'			"vagabond.ban_hang.cho_ghi_so_roi_phat_hanh",\n			queue="long",',
		'			"vagabond.ban_hang.cho_ghi_so_roi_phat_hanh",\n			queue="default",'),
	# Codex #488 vòng 3.
	("xuất rải không hoãn thì không giao lượt chờ (mất bước ký)", BH,
		'		_giao_luot_cho(ngay, chon, cho_xuat, "xuat-rai",',
		'		if not cho_xuat: _giao_luot_cho(ngay, chon, cho_xuat, "xuat-rai",'),
	("lượt chờ xuất rải chạy phát hành cuối ngày thay vì ký sau rải", BH,
		'	else:\n		phat_hanh_sau_rai(str(ngay), [t for t in ds if cint(tt.get(t)) == 1], con)',
		'	else:\n		phat_hanh_cuoi_ngay(str(ngay), da_ghi, cint(so_loi) + len(con))'),
	("phát hành sau rải không ký", BH,
		"			if bat_ky and _con_trong_ngay(ngay):\n				ky = _ky_theo_lo(ngay, trong_ngay=ngay)\n				loi += ky.get(\"loi\") or []\n		finally:\n			_mo_khoa_dong_bo(khoa2)",
		"			pass\n		finally:\n			_mo_khoa_dong_bo(khoa2)"),
	("phát hành sau rải chỉ ký khi kịch bản báo tờ mới (như vòng cũ)", BH,
		"			if bat_ky and _con_trong_ngay(ngay):\n				ky = _ky_theo_lo(ngay, trong_ngay=ngay)",
		"			if bat_ky and tao and _con_trong_ngay(ngay):\n				ky = _ky_theo_lo(ngay, trong_ngay=ngay)"),
	("chọn đơn xếp cả đơn tạm tính", HB,
		'		if rai_bo_qua(ma) or ma == "tam_tinh":', "		if rai_bo_qua(ma):"),
	("lý do xếp bỏ mất tạm tính của đơn Sales", BH,
		'	return ma if ma in ("tang_cho_duyet", "tang_tu_choi", "tam_tinh") else ""',
		'	return ma if ma in ("tang_cho_duyet", "tang_tu_choi") else ""'),
	("đọc đơn Sales không lọc tạm tính", BH,
		'"vgb_quay": ["in", ["", None]], "vgb_tam_tinh": 0, "vgb_huy": 0}, fields=truong, order_by="creation asc",',
		'"vgb_quay": ["in", ["", None]], "vgb_huy": 0}, fields=truong, order_by="creation asc",'),
	("kéo đơn không bỏ tạm tính", BH,
		'or cint(si.get("vgb_tam_tinh")) or si.get("custom_hddt_so"):', 'or si.get("custom_hddt_so"):'),
	# Codex #488 vòng 4.
	("trần chờ trả 0 từ 23:45 như cũ", HB,
		"	han = max(MOC_CUOI_CHO - giay, min(GIAY_CHO_TRE, MOC_NUA_DEM - giay))",
		"	han = MOC_CUOI_CHO - giay"),
	("trần chờ vượt quá 23:58", HB,
		"	han = max(MOC_CUOI_CHO - giay, min(GIAY_CHO_TRE, MOC_NUA_DEM - giay))",
		"	han = max(MOC_CUOI_CHO - giay, GIAY_CHO_TRE)"),
	("không giao lượt chờ tiếp cho đơn còn chạy", BH,
		"	if tiep:\n		_giao_tiep(ngay, tiep)", "	pass"),
	("giao tiếp cả đơn hàng đợi không trả lời", BH,
		"	tiep = hddt_bu.con_cho(ds, tt, chay.get, chi_chac=True)",
		"	tiep = hddt_bu.con_cho(ds, tt, chay.get)"),
	("giao tiếp cả khi hết giờ trong ngày", BH,
		"	if _giay_cho(ngay) <= 0:\n		frappe.log_error(",
		"	if False:\n		frappe.log_error("),
	("lượt chờ tiếp chạy phát hành cuối ngày (ghi đè nhật ký)", BH,
		'	if noi_goi == "cuoi-ngay":\n		phat_hanh_cuoi_ngay(', '	if noi_goi != "xuat-rai":\n		phat_hanh_cuoi_ngay('),
	# Codex #488 vòng 5.
	("lượt chờ đọc sổ trước rồi mới hỏi hàng đợi", BH,
		"		tt = _trang_thai_lo(ds)\n		if not hddt_bu.con_cho(ds, tt, chay.get)",
		"		tt = _trang_thai_lo(ds)\n		chay = {t: _job_dang_chay(t) for t in ds}\n		if not hddt_bu.con_cho(ds, tt, chay.get)"),
	("giờ chờ không xét ngày của lô (quay vòng qua nửa đêm)", BH,
		'		cung_ngay=str(ngay)[:10] == bay_gio.strftime("%Y-%m-%d"))', "		cung_ngay=True)"),
	("trần chờ bỏ qua cờ khác ngày", HB,
		"	if not cung_ngay:\n		# Lô của ngày đã qua: giờ trong ngày đã quay về 00:xx, đừng mở lại cửa.\n		return 0\n", ""),
	# Codex #488 vòng 6.
	("lượt riêng giữ quyền phát hành cũ qua nửa đêm", BH,
		"		cho_xuat = hddt_bu.con_phat_hanh(cho_xuat, ngay, nowdate())\n", ""),
	("lượt chờ phát hành lô hôm trước sau nửa đêm", BH,
		"	cho_xuat = hddt_bu.con_phat_hanh(cho_xuat, ngay, nowdate())\n	if not cho_xuat:", "	if not cho_xuat:"),
	("quyền phát hành không xét ngày", HB,
		'	return bool(cho_xuat) and str(ngay or "")[:10] == str(hom_nay or "")[:10]', "	return bool(cho_xuat)"),
	("báo động không xét giờ chuỗi", BH,
		'	if not hddt_bu.den_luc_bao_dong(now_datetime().strftime("%H:%M"), gio):\n		return\n', ""),
	("mốc báo động cố định 23:20, 23:45", HB,
		"		t = min(goc + tre, 23 * 60 + 55)", "		t = 23 * 60 + tre"),
	# Codex #488 vòng 7.
	("phát hành theo lô không kiểm ngày trước mỗi lô", BH,
		'		if trong_ngay and not _con_trong_ngay(trong_ngay):\n			ds.append({"tim_thay": 0,', '		if False:\n			ds.append({"tim_thay": 0,'),
	("ký theo lô không kiểm ngày trước mỗi lô", BH,
		'		if trong_ngay and not _con_trong_ngay(trong_ngay):\n			ds.append({"can_ky": 0,', '		if False:\n			ds.append({"can_ky": 0,'),
	("phát hành cuối ngày không truyền ngày của lô", BH,
		"			ph = _phat_hanh_theo_lo(ngay, trong_ngay=ngay)", "			ph = _phat_hanh_theo_lo(ngay)"),
	("phát hành cuối ngày làm tờ chờ xuất cả khi qua nửa đêm", BH,
		"			if _con_trong_ngay(ngay):\n				ph = _gop_cho_xuat(", "			if True:\n				ph = _gop_cho_xuat("),
	("phát hành sau rải không dừng khi qua nửa đêm", BH,
		"				if not _con_trong_ngay(ngay):\n					loi.append(QUA_NUA_DEM % ngay)\n					break\n", ""),
	("phát hành sau rải ký cả khi qua nửa đêm", BH,
		"			if bat_ky and _con_trong_ngay(ngay):", "			if bat_ky:"),
	("báo động chỉ chạy trong giờ 23", "vagabond/hooks.py",
		'setdefault("*/5 * * * *", []).append("vagabond.ban_hang.bao_dong_ghi_so_toi")',
		'setdefault("*/5 23 * * *", []).append("vagabond.ban_hang.bao_dong_ghi_so_toi")'),
	("lượt chờ không chờ gì", BH,
		"		if not hddt_bu.con_cho(ds, tt, chay.get) or time.monotonic() >= het:",
		"		if True:"),
	("lượt chờ đọc trong một giao dịch (ảnh chụp cũ)", BH,
		"		frappe.db.commit()\n		tt = _trang_thai_lo(ds)",
		"		tt = _trang_thai_lo(ds)"),
	("lượt chờ báo số đã xếp thay vì số đã ghi sổ", BH,
		"	phat_hanh_cuoi_ngay(str(ngay), da_ghi, cint(so_loi) + len(con))",
		"	phat_hanh_cuoi_ngay(str(ngay), len(ds), cint(so_loi) + len(con))"),
	("còn chờ cả đơn có lượt đã xong", HB,
		"		if chay is False or (chi_chac and chay is not True):\n			continue\n",
		"		if chi_chac and chay is not True:\n			continue\n"),
	("trần chờ không chừa giờ trước nửa đêm", HB,
		"	return max(0, min(GIAY_CHO_LO, han))", "	return GIAY_CHO_LO"),
	("đếm kết quả theo số đã xếp", HB,
		"	da = sum(1 for t in ds or [] if int((trang_thai or {}).get(t, -1)) == 1)",
		"	da = len(ds or [])"),
	("lượt riêng không nhả khoá khi kẹt", BH,
		"		return _ghi_so_mot_don(si, sepay, cho_xuat=cho_xuat)\n	finally:\n		_mo_khoa_dong_bo(khoa)",
		"		return _ghi_so_mot_don(si, sepay, cho_xuat=cho_xuat)\n	finally:\n		pass"),
	("lượt riêng không đặt trần chờ khoá dòng", BH,
		'		frappe.db.sql("SET SESSION innodb_lock_wait_timeout = %s" % int(hddt_bu.GIAY_CHO_KHOA_DONG))',
		"		pass"),
	("lượt riêng không kiểm đơn còn nên ghi", BH,
		"		if not hddt_bu.con_duoc_ghi_so(si, ngay):\n			return 0, 0, \"\"",
		"		pass"),
	("xếp với trần một giờ như cũ", BH,
		"				timeout=hddt_bu.GIAY_MOI_DON,", "				timeout=3600,"),
	("xếp không chống trùng", BH,
		"				job_id=hddt_bu.job_ghi_so(ten),\n				deduplicate=True,",
		"				job_id=hddt_bu.job_ghi_so(ten),\n				deduplicate=False,"),
	("hỏng hàng đợi thì bỏ đơn", BH,
		"			ghi_so_mot_don_nen(ten, str(ngay), cho_xuat=cho_xuat, nguon=nguon)", "			pass"),
	("chọn đơn không bỏ đơn cần người xử", HB,
		'		if rai_bo_qua(ma) or ma == "tam_tinh":\n			continue\n', '		if ma == "tam_tinh":\n			continue\n'),
	("lượt tới muộn vẫn ghi đơn đã kéo sang ngày khác", HB,
		'	return str(si.get("posting_date") or "")[:10] == str(ngay or "")[:10]', "	return True"),
	("xuất rải bỏ đơn Sales đã giao", BH,
		"		ds += _sales_da_giao_du_gio(ngay, truong)", "		pass"),
	("xuất rải lấy đơn giao SAU mốc", BH,
		'"giao_luc": ["<=", moc], "ngay_giao": ngay,', '"giao_luc": [">=", moc], "ngay_giao": ngay,'),
	("kéo đơn đổi ngày thẳng, mất ngày bán gốc", BH,
		'				_doi_ngay_ban_nhap(si, moi, "kéo hoá đơn treo hàng loạt", "hàng loạt")',
		"				si.posting_date = moi"),
	("kéo đơn không nhận bill quầy gọi đích danh", BH,
		"		if thieu:\n			cho += _bill_quay_nhap_cu(thieu, so_ngay)", "		pass"),
	("báo động gửi chủ đề Bán hàng", BH,
		'kenh_zalo.bao_hoac_ghi_loi("canh_bao", "hoa_don", tin[0], tin[1],',
		'kenh_zalo.bao_hoac_ghi_loi("canh_bao", "ban_hang", tin[0], tin[1],'),
	("tin báo động im cả khi còn đơn", HB,
		"	if not tong:\n		return None", "	return None"),
	("bỏ chủ đề Hoá đơn ở máy chủ", KZ,
		'"ban_hang", "hoa_don", "don_web"', '"ban_hang", "don_web"'),
]


def main():
	loc = sys.argv[1] if len(sys.argv) > 1 else ""
	ds = [x for x in DOT_BIEN if loc in x[0]]
	bat = 0
	for ten, tep, cu, moi in ds:
		duong = os.path.join(GOC, tep)
		with io.open(duong, encoding="utf-8") as f:
			goc = f.read()
		so = goc.count(cu)
		if so != 1:
			print("  MAU SAI  %s: khop %d lan, mong 1" % (ten, so))
			continue
		try:
			with io.open(duong, "w", encoding="utf-8") as f:
				f.write(goc.replace(cu, moi))
			rc = subprocess.run(CA, cwd=GOC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300).returncode
		finally:
			with io.open(duong, "w", encoding="utf-8") as f:
				f.write(goc)
		if rc:
			bat += 1
			print("  BAT      %s" % ten)
		else:
			print("  LOT      %s" % ten)
	print("\n%d/%d đột biến bị bắt." % (bat, len(ds)))
	return 0 if bat == len(ds) else 1


if __name__ == "__main__":
	sys.exit(main())

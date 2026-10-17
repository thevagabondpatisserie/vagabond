# -*- coding: utf-8 -*-
"""Đột biến cho màn Giá vốn tạm tính (#482), đọc theo AGENTS điều 17.

Mỗi đột biến cố tình làm hỏng lại đúng một chỗ, khẳng định mẫu khớp ĐÚNG MỘT
lần trước khi tin kết quả, chạy bộ ca liên quan, rồi trả tệp về như cũ.
In thật số bắt được, không làm tròn.

Chạy:  python3 vagabond/khung/kiem_thu/dot_bien_gia_von_tam.py
"""

import io
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PY = "vagabond/gia_von_tam.py"
JS = "vagabond/public/js/bep/53-gia-von-tam.js"
TC = "vagabond/public/js/bep/02-trang-chu.js"
SD = "vagabond/public/js/bep/48-ban-soan-do.js"
CT = "vagabond/vagabond/doctype/vagabond_gia_thu/vagabond_gia_thu.py"

CA_PY = [sys.executable, "-c", (
	"import sys; sys.path.insert(0, %r)\n"
	"from vagabond.khung.kiem_thu import nen; nen.gia_lap()\n"
	"from vagabond.khung.kiem_thu import thu_gia_von_tam\n"
	"sys.exit(1 if nen.chay_het(im=True) else 0)" % GOC)]
CA_JS = ["node", "vagabond/khung/kiem_thu/hanh_vi/gia_von_tam_482.js"]
CA_SD = ["node", "vagabond/khung/kiem_thu/hanh_vi/ban_soan_do_533.js"]
CA_SD_PY = [sys.executable, "-c", (
	"import sys; sys.path.insert(0, %r)\n"
	"from vagabond.khung.kiem_thu import nen; nen.gia_lap()\n"
	"from vagabond.khung.kiem_thu import thu_ban_soan_do_533\n"
	"sys.exit(1 if nen.chay_het(im=True) else 0)" % GOC)]

DOT_BIEN = [
	("bỏ đi xuống công thức con khi bom_no rỗng", PY,
		"	return mac_dinh or None\n", "	return None\n", CA_PY),
	("đổi stock_qty sang qty khi đọc dòng BOM", PY,
		'"sl": flt(d.stock_qty) or flt(d.qty),', '"sl": flt(d.qty),', CA_PY),
	("bỏ chặn vòng lặp", PY,
		"		if bom in dang:\n			return", "		if False:\n			return", CA_PY),
	("làm tròn xuống thay vì lên", PY,
		"int(math.ceil(round(", "int(math.floor(round(", CA_PY),
	("bỏ lọc món thiếu giá khi chốt", PY,
		'		ly_do = TRANG_THAI_BO_QUA.get(d.get("trang_thai"))\n', "		ly_do = None\n", CA_PY),
	("bỏ cổng quyền Chốt ở máy chủ", PY,
		'	_kiem(QUYEN_CHOT, "chốt giá vốn tạm tính")\n', "", CA_PY),
	("Codex #483 v1: bỏ lọc dòng hết hạn hoặc tương lai", PY,
		"		if (tu and tu > hn) or (den and den < hn):\n			continue\n", "", CA_PY),
	("Codex #483 v1: bỏ lọc dòng giá riêng khách, nhà cung cấp, lô", PY,
		'		if p.get("customer") or p.get("supplier") or p.get("batch_no"):\n			continue\n', "", CA_PY),
	("Codex #483 v1: lấy valid_from cũ nhất thay vì mới nhất", PY,
		"	hop.sort(reverse=True)\n", "	hop.sort()\n", CA_PY),
	("Codex #483 v2: không đổi đơn vị mua về đơn vị kho", PY,
			"			gia, hang = gia / hs, 1\n", "			hang = 1\n", CA_PY),
	("Codex #483 v2: thẻ không có chip trạng thái", JS,
		"'<div class=\"gvt-chips\">' + gvtChipTrangThai(d) + gvtChipHeSo(d) + chot", "'<div class=\"gvt-chips\">' + gvtChipHeSo(d) + chot", CA_JS),
	("Codex #483 v3: nhiều công thức không mặc định thì lấy đại bản đầu", PY,
		'		elif len(ds) == 1:\n			ra[ma] = ds[0].get("name")\n', '		else:\n			ra[ma] = ds[0].get("name")\n', CA_PY),
	("Codex #483 v3: ô trang chủ hiện cho mọi vai kế toán", TC,
		"(coQuyenGvt() ? card('🧮'", "(true ? card('🧮'", CA_PY),
	("Codex #483 v3: bỏ chip lọc Công thức vòng", JS,
		"['vuot_gia_ban', 'vong', 'thieu_gia', 'duoi_muc_tieu']", "['vuot_gia_ban', 'thieu_gia', 'duoi_muc_tieu']", CA_JS),
	("Codex #483 v3: không hiện khung món nhiều công thức", JS,
		"  if (nct.so) {", "  if (false) {", CA_JS),
	("v600: chia cho hệ số thay vì nhân", PY,
		"flt(gia_von) * _so(he_so) / 1000.0", "flt(gia_von) / _so(he_so) / 1000.0", CA_PY),
	("v600: so hệ số đã làm tròn thay vì tỷ số thật", PY,
		"flt(gia_ban) / flt(gia_von) < _so(he_so_muc_tieu)", "he_so_hien(gia_von, gia_ban) < _so(he_so_muc_tieu)", CA_PY),
	("v600: hệ số 1 được nhận là mục tiêu", PY,
		"return h is not None and HE_SO_MIN < h <= HE_SO_MAX", "return h is not None and HE_SO_MIN <= h <= HE_SO_MAX", CA_PY),
	("v600: phiếu thử, giá tay không thắng giá mã", PY,
		'		if flt(d.get("don_gia_tay")) > 0:\n', "		if False:\n", CA_PY),
	("v600: phiếu thử không chia số ra của mẻ", PY,
		"	gv = round(tong / so_ra)\n", "	gv = round(tong)\n", CA_PY),
	("v600: bỏ cổng quyền lập phiếu thử", PY,
		'	_kiem(QUYEN_CHOT, "lập phiếu tính giá thử")\n', "", CA_PY),
	("v600: tính thử gửi cả dòng chưa có số lượng", JS,
		"    if (sl == null || sl <= 0) return;\n", "", CA_JS),
	("v600: sửa phiếu không đánh dấu chưa lưu", JS,
		"  S.chuaLuu = 'Phiếu tính giá thử đang sửa dở", "  if (0) S.chuaLuu = 'Phiếu tính giá thử đang sửa dở", CA_JS),
	("v600: đổi tab tính lại cả tab bán", JS,
		"  return GVT.kq ? gvtVe() : scrGiaVonTam();", "  return scrGiaVonTam();", CA_JS),
	("hiện nút Chốt cho người không có quyền", JS,
		"kq.sua_duoc ? { footer:", "true ? { footer:", CA_JS),
	("Chốt không hỏi xác nhận", JS,
		"  if (!await confirmSheet('Chốt giá vốn tạm',", "  if (false && await confirmSheet('Chốt giá vốn tạm',", CA_JS),
	("gọi chi_tiet ngay lúc mở màn", JS,
		"  gvtVe();\n}", "  gvtVe();\n  api('vagabond.gia_von_tam.chi_tiet', { ma: 'x' });\n}", CA_JS),
	# ---- Codex #486 vòng 1 ----
	("Codex #486 P1: phiếu thử không bọc bản nháp", SD,
		"gvtManPhieu = sdBoc('gia_thu', 'gvtManPhieu', gvtManPhieu);\n", "", CA_SD),
	("Codex #486 P1: bản nháp phiếu thử không đọc trạng thái", SD,
		"  ten: 'Phiếu tính giá thử', lay: function () { return GVT.p; },", "  ten: 'Phiếu tính giá thử', lay: function () { return null; },", CA_SD),
	("Codex #486 P1: màn phiếu thử khai bằng biểu thức, không được nâng lên trước 48", JS,
		"function gvtManPhieu() {", "var gvtManPhieu = function () {", CA_SD_PY),
	("Codex #486 P1: bỏ phiếu thành xoá cứng", PY,
		"		d.da_bo = 1\n", "		frappe.delete_doc(DT_THU, name, ignore_permissions=True)\n", CA_PY),
	("Codex #486 P1: danh sách hiện cả phiếu đã bỏ", PY,
		'	loc = [["da_bo", "=", 0]]\n', '	loc = []\n', CA_PY),
	("Codex #486 P1 + v2: sửa được phiếu đã bỏ (app và Desk)", PY,
		'	if truoc and int(truoc.get("da_bo") or 0):\n', "	if False:\n", CA_PY),
	("Codex #486 P1: bỏ phiếu không hỏi xác nhận", JS,
		"  if (!await confirmSheet('Bỏ phiếu',", "  if (false && await confirmSheet('Bỏ phiếu',", CA_JS),
	("Codex #486 P2: Desk lưu không tính lại", CT,
		"		kiem_khi_luu(self)\n", "		pass\n", CA_PY),
	("Codex #486 P2: tính lại mà không ghi giá vốn vào phiếu", PY,
		'	d.gia_von = kq["gia_von"]\n', "", CA_PY),
	("Codex #486 P2: kết quả tính thử cũ về sau đè số mới", JS,
		"  if (lan !== GVT.lan || p !== GVT.p) return;\n  GVT.loiTinh = null;", "  GVT.loiTinh = null;", CA_JS),
	("Codex #486 P2: kết quả tìm phiếu cũ về sau đè kết quả mới", JS,
		"  if (lan !== GVT.lanDs) return;\n  if (noiTiep)", "  if (noiTiep)", CA_JS),
	("Codex #486 P2: máy chủ không báo còn trang sau", PY,
		'		"con_nua": bd + len(cat) < len(hop),', '		"con_nua": False,', CA_PY),
	("Codex #486: tìm nguyên liệu không loại nhóm bánh bán", PY,
		'{"disabled": 0, "item_group": ["not in", list(NHOM_BAN)]}, "Item"', '{"disabled": 0}, "Item"', CA_PY),
	# ---- Codex #486 vòng 2 ----
	("Codex #486 v2+v3: mã nhiều công thức chưa chọn mặc định lấy giá kho (mọi tầng)", PY,
		"		if ma in mo_ho:\n			return 0.0, NGUON_NHIEU_CT", "		if False:\n			return 0.0, NGUON_NHIEU_CT", CA_PY),
	# ---- Codex #486 vòng 3 ----
	("Codex #486 v3: cộng dồn không coi mã nhiều công thức là thiếu", PY,
		"				if nguon in NGUON_LA_THIEU:\n					thieu.add", "				if nguon == NGUON_THIEU:\n					thieu.add", CA_PY),
	("Codex #486 v3: sheet chi tiết không báo thiếu cho mã nhiều công thức", PY,
		"			thieu = 1 if nguon in NGUON_LA_THIEU else 0", "			thieu = 1 if nguon == NGUON_THIEU else 0", CA_PY),
	("Codex #486 v3: mẻ ra 0 vẫn gửi tính thử", JS,
		"  if (soRa == null || soRa <= 0) return gvtBaoLoiTinh(", "  if (false) return gvtBaoLoiTinh(", CA_JS),
	("Codex #486 v3: mẻ ra trống tự thay 1", JS,
		"ten_mon: p.ten_mon || 'Món thử', nhom: p.nhom, so_ra: gvtSoVn(p.so_ra),", "ten_mon: p.ten_mon || 'Món thử', nhom: p.nhom, so_ra: gvtSoVn(p.so_ra) || 1,", CA_JS),
	("Codex #486 v3: máy chủ từ chối tính thử thì im lặng giữ số cũ", JS,
		"    return gvtBaoLoiTinh((e && e.message) ||", "    return; gvtBaoLoiTinh((e && e.message) ||", CA_JS),
	("Codex #486 v3: Lưu khi mẻ ra trống vẫn gửi", JS,
		"  if (soRa == null || soRa <= 0) return baoTin(", "  if (false) return baoTin(", CA_JS),
	("Codex #486 v2: bỏ phiếu tính lại ảnh chụp giá", PY,
		'		return "giu"\n', '		return "tinh"\n', CA_PY),
	("Codex #486 v2: bỏ phiếu kèm sửa nội dung lọt qua", PY,
		'		if truoc.get("noi_dung") != nay.get("noi_dung"):\n', "		if False:\n", CA_PY),
	("Codex #486 v2: lưu luôn tính lại, bỏ qua quyết định", PY,
		'	if viec == "tinh":\n		return tinh_lai_doc(d)', '	if True:\n		return tinh_lai_doc(d)', CA_PY),
	# ---- Codex #486 vòng 4 ----
	("Codex #486 v4: Desk xoá được phiếu thử", CT,
		'\t\tfrappe.throw("Không xoá phiếu tính giá thử.', '\t\treturn\n\t\tfrappe.throw("Không xoá phiếu tính giá thử.', CA_PY),
	("Codex #486 v4: tính xong không vẽ ô giá tay cho dòng thiếu", JS,
		"  if (ds && lech) {", "  if (false) {", CA_JS),
	("Codex #486 v4: dòng mã thiếu giá không cần ô giá tay", JS,
		"!d.item_code || !!(r && r.thieu) ||", "!d.item_code || false ||", CA_JS),
	# ---- Giao diện chip 17/10/2026 ----
	("Chip: chip hệ số không đổi màu theo trạng thái", JS,
		"[d.trang_thai] ||\n    ['#0b7c93', '#ecfeff'];", "['x'] ||\n    ['#0b7c93', '#ecfeff'];", CA_JS),
	("Chip: thẻ thiếu giá vẫn hiện ô đề xuất xanh", JS,
		"  if (!tinhDuoc) oDx = gvtO('Đề xuất', 'Chưa tính', '', 1);\n  else if (d.gia_de_xuat)", "  if (false) oDx = 0;\n  else if (d.gia_de_xuat)", CA_JS),
	("Chip: đầu nhóm không nói chưa đặt mục tiêu", JS,
		"      : '<span class=\"gvt-c\">Chưa đặt mục tiêu</span>') + '</div>';", "      : '') + '</div>';", CA_JS),
	# ---- Codex #486 vòng 6 ----
	("Codex #486 v6: chip hệ số hiện khi giá vốn còn thiếu", JS,
		"  if (d.he_so == null || !gvtTinhDuoc(d)) return '';", "  if (d.he_so == null) return '';", CA_JS),
	("Codex #486 v6: thẻ phiếu thử thiếu giá vẫn tính được", JS,
		"  return d.trang_thai !== 'thieu_gia' && d.trang_thai !== 'vong'", "  return d.trang_thai !== 'vong'", CA_JS),
	("Codex #486 v6: thẻ phiếu thử không có ô ảnh món", JS,
		"    '<div class=\"gvt-dau\">' + anhMon('') + '<div class=\"gvt-th\">' +", "    '<div class=\"gvt-dau\"><div class=\"gvt-th\">' +", CA_JS),
	("Codex #486 P2: máy chủ bỏ qua vị trí bắt đầu", PY,
		"	cat = hop[bd:bd + trang]", "	cat = hop[0:trang]", CA_PY),
	# ---- Codex #486 vòng 7 ----
	("Codex #486 v7: máy chủ bỏ qua lọc nhóm", PY,
		"		return not nhom or (p.get(\"nhom\") or CHUA_NHOM) == nhom", "		return True", CA_PY),
	("Codex #486 v7: đếm nhóm không theo trạng thái đang chọn", PY,
		"		if khop_tt(p):\n			k = p.get(\"nhom\")", "		if True:\n			k = p.get(\"nhom\")", CA_PY),
	("Codex #486 v7: máy chủ bỏ qua khoảng ngày lập", PY,
		"	if moc:\n		loc.append", "	if False:\n		loc.append", CA_PY),
	("Codex #486 v7: bấm chip trạng thái không gửi lên máy chủ", JS,
		"trang_thai: GVT.thuTt, nhom: GVT.thuNhom", "trang_thai: '', nhom: GVT.thuNhom", CA_JS),
	("Codex #486 v7: Xem thêm bỏ mất bộ lọc", JS,
		"      trang_thai: t.trang_thai || '', nhom: t.nhom || '', khoang: t.khoang || '' }", "      trang_thai: '', nhom: '', khoang: '' }", CA_JS),
	("Codex #486 v7: sheet nhóm bán gõ không lọc", JS,
		"  o.oninput = function () { ve(o.value); };", "  o.oninput = function () { };", CA_JS),
	("Codex #486 v7: không hiện hàng chip lọc phiếu thử", JS,
		"  var chip = (t.tong || dangLoc) ? gvtChipThu(t) : '';", "  var chip = '';", CA_JS),
	("Codex #486 P2: màn không có nút Xem thêm", JS,
		"    (t.con_nua ? '<button class=\"btn gh\" data-gvtthemds", "    (false ? '<button class=\"btn gh\" data-gvtthemds", CA_JS),
]


def main():
	bat = 0
	for ten, tep, cu, moi, lenh in DOT_BIEN:
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
			rc = subprocess.run(lenh, cwd=GOC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300).returncode
		finally:
			with io.open(duong, "w", encoding="utf-8") as f:
				f.write(goc)
		if rc:
			bat += 1
			print("  BAT      %s" % ten)
		else:
			print("  LOT      %s" % ten)
	print("\n%d/%d đột biến bị bắt." % (bat, len(DOT_BIEN)))
	return 0 if bat == len(DOT_BIEN) else 1


if __name__ == "__main__":
	sys.exit(main())

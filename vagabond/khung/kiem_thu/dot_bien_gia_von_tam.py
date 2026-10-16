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

CA_PY = [sys.executable, "-c", (
	"import sys; sys.path.insert(0, %r)\n"
	"from vagabond.khung.kiem_thu import nen; nen.gia_lap()\n"
	"from vagabond.khung.kiem_thu import thu_gia_von_tam\n"
	"sys.exit(1 if nen.chay_het(im=True) else 0)" % GOC)]
CA_JS = ["node", "vagabond/khung/kiem_thu/hanh_vi/gia_von_tam_482.js"]

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
		"h(d.ten) + '</div>' + gvtChipTrangThai(d) + '</div>' +", "h(d.ten) + '</div>' + '</div>' +", CA_JS),
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

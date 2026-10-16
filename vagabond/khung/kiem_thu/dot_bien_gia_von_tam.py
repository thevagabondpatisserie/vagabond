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
		"'</div>' + gvtChipTrangThai(d) + '</div>' +", "'</div>' + '</div>' +", CA_JS),
	("hiện nút Chốt cho người không có quyền", JS,
		"kq.sua_duoc ? { footer:", "true ? { footer:", CA_JS),
	("Chốt không hỏi xác nhận", JS,
		"  if (!await confirmSheet(", "  if (false && await confirmSheet(", CA_JS),
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

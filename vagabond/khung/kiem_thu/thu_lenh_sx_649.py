# -*- coding: utf-8 -*-
"""v649 màn Lệnh sản xuất (anh Việt 11/11/2026, hai ảnh 15:15 và 15:25).

1. Thẻ lệnh: số lượng, trạng thái xuống một dòng dưới tên, không còn cột phải
   chữ to (hành vi chạy thật ở hanh_vi/the_lenh_649.js).
2. Câu chặn kiểm kê: nói đúng số phiếu kiểm kê đang khoá (KK-26-00085 khoá sáu
   mã Hannari ở Pastry - Nguyên liệu), app hiện đủ câu, xuống dòng đúng chỗ.
"""
import json
import subprocess
from pathlib import Path

from vagabond import kho_sap
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).parents[3]


@ca("v649 thẻ lệnh sản xuất chạy thật trong node: ba cột, số lượng một dòng dưới tên")
def _():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/the_lenh_649.js")],
		capture_output=True, text=True, timeout=120)
	dung("chạy được: " + (r.stdout[-1500:] + r.stderr[-600:]), r.returncode == 0)
	dung("đủ 4 ca", "4 dat, 0 hong" in r.stdout)


@ca("v649 câu chặn kiểm kê nói số phiếu đang khoá (KK-26-00085 ngày 11/11/2026)")
def _():
	khoa = kho_sap.khoa_dang_kiem([
		{"phieu": "KK-26-00085", "kho": "Pastry - Nguyên liệu - TV", "trang_thai": "Chờ duyệt", "ma": ["NBTP00033", "NBTP00036"]},
		{"phieu": "KK-26-00082", "kho": "Pastry - Nguyên liệu - TV", "trang_thai": "Đã ghi sổ", "ma": ["NBTP00033"]},
	])
	la("khoá ghi đúng số phiếu", khoa[("Pastry - Nguyên liệu - TV", "NBTP00033")], "KK-26-00085")
	vuong = kho_sap.dong_bi_khoa([{"ma": "NBTP00033", "kho": ["Pastry - Nguyên liệu - TV"]}], khoa)
	la("dòng vướng mang số phiếu", vuong[0]["phieu"], "KK-26-00085")
	c = kho_sap.cau_bi_khoa(vuong, {"NBTP00033": "BTP Cấp 1 Bánh Ổ Hannari size 12cm"})
	dung("số phiếu đứng đầu câu", c.startswith("Phiếu kiểm kê KK-26-00085"))
	dung("tên món, tên kho", "BTP Cấp 1 Bánh Ổ Hannari size 12cm tại Pastry - Nguyên liệu - TV" in c)
	dung("nói phải làm gì", "ghi sổ chênh lệch" in c)
	# Tập cũ (không số phiếu) vẫn chạy: câu không bịa số phiếu.
	c2 = kho_sap.cau_bi_khoa(kho_sap.dong_bi_khoa([{"ma": "A", "kho": ["K"]}], {("K", "A")}), {})
	dung("không có số phiếu thì câu chung", c2.startswith("Đang có phiếu kiểm kê mở"))


@ca("v649 app đọc lỗi máy chủ: <br> thành xuống dòng, câu chặn kiểm kê không bị cắt mất số phiếu và việc cần làm")
def _():
	c = kho_sap.cau_bi_khoa([{"ma": "NBTP00033", "kho": "Pastry - Nguyên liệu - TV", "phieu": "KK-26-00085"}],
		{"NBTP00033": "BTP Cấp 1 Bánh Ổ Hannari size 12cm"})
	src = (GOC / "vagabond/public/js/bep/03-kho-chung-tu.js").read_text(encoding="utf-8")
	dau = src.index("function errMsg(e)")
	ham = src[dau:src.index("\n}\n", dau) + 2]
	js = ham + "\nprocess.stdout.write(JSON.stringify(errMsg({message: %s})));" % json.dumps(c)
	r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
	ra = json.loads(r.stdout or '""')
	dung("không còn thẻ html", "<" not in ra)
	dung("xuống dòng thật giữa tên kho và câu hướng dẫn", "Pastry - Nguyên liệu - TV\nNgười duyệt" in ra)
	dung("không dính chữ 'TVĐếm' như ảnh 15:25", "TVĐếm" not in ra and "TVNgười" not in ra)
	dung("đủ câu, không bị cắt", ra.endswith("rồi bấm lại."))


@ca("v649 Codex #552 vòng 2: số còn phải làm của lệnh trừ cả hao hụt (nút Hoàn tất, Kế hoạch, dùng lệnh đang mở) chạy thật trong node")
def _():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/con_lai_lenh_649.js")],
		capture_output=True, text=True, timeout=120)
	dung("chạy được: " + (r.stdout[-1500:] + r.stderr[-600:]), r.returncode == 0)
	dung("đủ 3 ca", "3 dat, 0 hong" in r.stdout)


@ca("v649 một nguồn cho số còn lại của lệnh: trong bep/ chỉ mfgConLai tự lấy qty trừ produced_qty")
def _():
	import re
	cho = []
	for p in sorted((GOC / "vagabond/public/js/bep").glob("*.js")):
		for i, dong in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
			if re.search(r"\.qty\s*\|\|\s*0\)\s*-\s*\([^)]*\.produced_qty", dong):
				cho.append("%s:%d" % (p.name, i))
	la("chỉ một chỗ (trong mfgConLai)", len(cho), 1)
	src = (GOC / "vagabond/public/js/bep/05-san-xuat.js").read_text(encoding="utf-8")
	dau = src.index("function mfgConLai(")
	dung("chỗ đó nằm trong mfgConLai và trừ cả hao", "process_loss_qty" in src[dau:src.index("\n}\n", dau)])

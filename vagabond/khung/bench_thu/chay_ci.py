"""Chạy trên bench GitHub dùng một lần, hai lượt cùng bộ nhớ Python.

Không dùng `bench execute`: cửa đó có nhánh eval thử lại khi hàm ném lỗi.
Runner này ghi bằng chứng rồi thoát đỏ ngay khi khung mất an toàn.
"""

import json
import os
import socket
import subprocess
import sys
import traceback
from pathlib import Path
from unittest.mock import patch

import frappe


def chay():
	if os.environ.get("GITHUB_ACTIONS") != "true":
		raise RuntimeError("Chỉ chạy trên GitHub Actions, không dùng với site thật.")
	tep = Path(os.environ["VGB_ARTIFACTS"])
	tep.mkdir(parents=True, exist_ok=True)
	frappe.init(site="bench-ci.localhost", sites_path=".")
	frappe.connect()
	ket = []
	try:
		if not frappe.conf.get("vagabond_bench_thu"):
			raise RuntimeError("Thiếu khoá bench thử.")
		frappe.set_user("Administrator")
		from vagabond.khung.kiem_that.cua import chay as chay_cua
		from vagabond.khung.kiem_that import nen

		# Không có worker/scheduler chạy. Chặn kết nối ra ngoài kể cả hook quên
		# đọc cờ thử; MariaDB/Redis nằm ở loopback và vẫn chạy thật.
		ket_noi = socket.socket.connect

		def chi_noi_bo(sock, dia_chi):
			if isinstance(dia_chi, tuple) and dia_chi[0] not in ("127.0.0.1", "::1", "localhost"):
				raise RuntimeError("Bench cấm kết nối ra ngoài: %s" % dia_chi[0])
			return ket_noi(sock, dia_chi)

		co_243 = [ten for ten, _ in nen.CA if ten.startswith("#243 ")]
		if len(co_243) != 11:
			raise RuntimeError("Phải đăng ký đủ 11 ca #243, nhận %s" % len(co_243))
		with patch.object(socket.socket, "connect", chi_noi_bo):
			for luot in (1, 2):
				kq = chay_cua(im=0)
				ket.append(kq)
				(tep / ("luot-%s.json" % luot)).write_text(
					json.dumps(kq, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
				print("Lượt %s: %s" % (luot, json.dumps(kq, ensure_ascii=False, default=str)), flush=True)
				if not kq.get("sach") or kq.get("mat_diem_luu") or kq.get("chung_tu_con_sot") or kq.get("so_luong_lech"):
					raise RuntimeError("Mất an toàn hoàn nguyên, không chạy lượt sau.")
				if kq.get("chua_chay") or kq.get("da_chay") != len(nen.CA):
					raise RuntimeError("Bộ kiểm chưa chạy đủ ca.")
		# Không bỏ qua lỗi cũ. Hai lượt được ghi đủ để phân biệt lỗi nền và
		# lỗi trạng thái còn sót; bất kỳ ca đỏ nào vẫn làm job đỏ.
		dat_bo = not any(kq.get("hong") for kq in ket)
		print("%s: hai lượt đầy đủ, không còn chứng từ thử." % ("PASS" if dat_bo else "FAIL"))
		# Hai cửa phát hành dùng SI riêng; chỉ HTTP cuối được giả lập.
		from vagabond.khung.bench_thu.kiem_minvoice_243 import chay as chay_minvoice
		try:
			with patch.object(socket.socket, "connect", chi_noi_bo):
				kq = chay_minvoice()
		except Exception:
			kq = {"dat": False, "loi": traceback.format_exc()}
		(tep / "minvoice-243.json").write_text(
			json.dumps(kq, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
		print("M-Invoice: " + json.dumps(kq, ensure_ascii=False, default=str), flush=True)
		return dat_bo and bool(kq.get("dat"))
	except Exception:
		(tep / "loi.txt").write_text(traceback.format_exc(), encoding="utf-8")
		raise
	finally:
		frappe.db.rollback()
		frappe.destroy()


if __name__ == "__main__":
	dat = chay()
	# Kịch bản này cố ý commit và mở nhiều kết nối. Chỉ chạy sau khi bộ
	# điểm lưu đã kết thúc sạch, trên site dùng một lần của GitHub.
	kho = subprocess.run([sys.executable, "-m", "vagabond.khung.bench_thu.kho_tang_243"], check=False)
	if not dat or kho.returncode:
		raise RuntimeError("Có cửa tích hợp đỏ. Đọc JSON từng lượt, M-Invoice và kho; không phát hành.")

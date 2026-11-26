# -*- coding: utf-8 -*-
"""v694 (giám đốc chốt 26/11/2026): màn Nhập kho và Nhận hàng theo đơn hỏi lại khi
còn dòng chưa đánh dấu Đã đếm mà số lượng lớn hơn 0; mặc định quay lại kiểm. Chạy
nguyên hai màn trong DOM giả bằng node (hanh_vi/nhap_kho_chua_dem_694.js)."""

import subprocess
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[3]


@ca("v694 nhập kho: dòng chưa đánh dấu Đã đếm có số lượng thì hỏi lại, mặc định quay lại kiểm (chạy thật hai màn)")
def _hai_man():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/nhap_kho_chua_dem_694.js"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	dung("đủ ca", "PASS 694" in r.stdout)

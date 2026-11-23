# -*- coding: utf-8 -*-
"""PR B (vòng 2 kiểm giao diện 22/11/2026): Trang chủ hiện ngay, màn cũ không vẽ đè.

Codex đo trên site thật: bấm Trang chủ từ năm màn phải chờ 2,3 tới 3,6 giây mới thấy
lưới, vì trang chủ đợi lần lượt khoảng 20 lượt đếm số. Và một lần đang ở Đối soát COD
thì màn Vận đơn quay lại đè lên.

Hành vi chạy THẬT trong node ở hanh_vi/trang_chu_nhanh_pr_b.js (khung app và trang chủ
thật, máy chủ giả giữ số tới khi ca cho trả). Phép đo thời gian trong trình duyệt nằm ở
cong_cu/ui_b/do_dieu_huong.cjs (cần Playwright, không chạy trong CI).

Toàn phép thuần, không Frappe, không requests.
"""

import os
import subprocess

from vagabond.khung.kiem_thu.nen import ca, la

GOC = os.path.dirname(os.path.abspath(__file__))


@ca("PR B chạy thật trong node: lưới trang chủ hiện trước số đếm, đếm song song, giữ số trong hạn, không vẽ đè màn mới")
def _hanh_vi():
	r = subprocess.run(["node", os.path.join(GOC, "hanh_vi", "trang_chu_nhanh_pr_b.js")],
		capture_output=True, text=True, timeout=120)
	la("trang_chu_nhanh_pr_b.js chạy xanh", (r.returncode, (r.stdout or "")[-600:] if r.returncode else ""), (0, ""))


@ca("PR B công cụ đo điều hướng đúng cú pháp")
def _cong_cu():
	tep = os.path.join(GOC, "..", "..", "..", "cong_cu", "ui_b", "do_dieu_huong.cjs")
	r = subprocess.run(["node", "--check", os.path.abspath(tep)], capture_output=True, text=True, timeout=60)
	la("node --check do_dieu_huong.cjs", (r.returncode, r.stderr), (0, ""))


@ca("v689 Codex kiểm v685 UI16: 25 màn async Bán hàng, Giao hàng không vẽ đè hay ghi đè màn đang đứng khi lời đáp về muộn (node, thân hàm thật)")
def _man_cu_ve_muon():
	r = subprocess.run(["node", os.path.join(GOC, "hanh_vi", "man_cu_ve_muon_ui16.js")],
		capture_output=True, text=True, timeout=180)
	la("man_cu_ve_muon_ui16.js chạy xanh", (r.returncode, (r.stdout or "")[-800:] if r.returncode else ""), (0, ""))

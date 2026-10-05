# -*- coding: utf-8 -*-
"""v558: mo khoa / dong khoa mot to tren app va Desk.

Anh Viet chot 03/10/2026 (bang duyet so tay, viec so 6): them nut mo khoa
tren ca app va Desk. Truoc v558 may chu da co mo_khoa_mot_to nhung khong nut
nao goi toi, so tay phai ghi "chua ro nguoi dung bam o dau".

Phep THUAN trang_thai_khoa quyet dinh nut nao hien. Ca giao dien chay that o
hanh_vi/mo_khoa_558.cjs.
"""

import datetime
import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import chung_tu  # noqa: E402

D = datetime.date


@ca("v558: trang thai khoa cua mot to quyet dinh nut Mo khoa hay Dong khoa")
def _trang_thai():
	tt = chung_tu.trang_thai_khoa
	la("to trong ky khoa", tt(D(2026, 9, 1), D(2026, 9, 30), 0), "khoa")
	la("to dung ngay khoa", tt(D(2026, 9, 30), D(2026, 9, 30), 0), "khoa")
	la("to sau ngay khoa", tt(D(2026, 10, 1), D(2026, 9, 30), 0), "tu_do")
	la("khong khoa gi", tt(D(2026, 9, 1), None, 0), "tu_do")
	la("to khong co ngay", tt(None, D(2026, 9, 30), 0), "tu_do")
	# To da mo thi phai thay nut Dong khoa du ke toan da doi moc khoa sau do.
	la("to da mo trong ky khoa", tt(D(2026, 9, 1), D(2026, 9, 30), 1), "mo")
	la("to da mo nhung moc khoa da lui", tt(D(2026, 9, 1), None, 1), "mo")


@ca("v558: Desk goi dung cua khoa_cua_to va mo/dong khoa tren moi loai chung tu bi khoa")
def _desk():
	goc = os.path.dirname(os.path.abspath(chung_tu.__file__))
	js = io.open(os.path.join(goc, "public", "js", "vgb_khoa_xoa.js"), encoding="utf-8").read()
	# Do chuoi chi chot loi vao, hanh vi nut chay o may chu va ca app.
	dung("nut gan vao refresh chung", "vgb.nut_khoa_so(frm);" in js)
	for m in ("khoa_cua_to", "mo_khoa_mot_to", "dong_khoa_mot_to"):
		dung("Desk goi %s" % m, "vagabond.chung_tu.%s" % m in js)


@ca("#414 Codex: so tay khong noi 'noi phieu o dau cung giu gia'; nut Noi phieu nhap kho tren Desk phai bi can")
def _noi_phieu_desk():
	# Hook dong_bo_luc_luu chi dung lai gia cho to dung tu hoa don dien tu
	# (custom_minvoice_id). Hoa don nhap tay bam nut Desk thi gia bi de that.
	goc = os.path.dirname(os.path.abspath(chung_tu.__file__))
	md = io.open(os.path.join(goc, "so_tay", "kho.md"), encoding="utf-8").read()
	dung("khong con cau noi o dau cung giu gia", "Nối phiếu ở đâu thì máy cũng giữ" not in md)
	dung("co dong can nut Desk", "Không bấm [[desk:Nối phiếu nhập kho]]" in md)

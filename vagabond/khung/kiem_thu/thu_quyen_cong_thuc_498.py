# -*- coding: utf-8 -*-
"""#498: ba cửa của màn Danh mục công thức, và hai lớp phải khớp nhau.

Anh Việt 16/09/2026: mở cho bếp trưởng, bếp phó và quầy bar xem, sửa, thêm
mới công thức; riêng nút Ghi sổ vẫn để bếp trưởng chốt.

Ca kiểm ở đây GỌI THẬT từng cửa với từng bộ vai chứ không dò chuỗi trong mã
nguồn (điều 16 AGENTS.md). Phép dò chuỗi chỉ dùng đúng một lần, cho việc
không chạy được ở tầng Python: đối chiếu danh sách vai bên JS với bên máy
chủ, vì lệch một vai là hiện nút ra rồi máy chủ từ chối.
"""
import io
import os
import re
from unittest.mock import patch

from vagabond import cong_thuc as ct
from vagabond.vai_cua_hang import BANG_VAI, VAI_BAR, VAI_QLCT
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS = os.path.join(GOC, "public", "js", "bep", "26-cong-thuc.js")


def _voi(vai):
	"""Giả lập đúng một thứ: người đang đăng nhập giữ bộ vai nào."""
	return patch.object(ct.frappe, "get_roles", lambda *a: list(vai), create=True)


@ca("#498: bếp phó và quầy bar SOẠN được, nhưng KHÔNG ghi sổ được")
def _soan_khong_ghi_so():
	for vai in (["Bếp phó"], [VAI_BAR], ["Bếp phó", "Manufacturing User"]):
		with _voi(vai):
			ct._kiem_xem()
			ct._kiem_soan()
			nem("ghi sổ với vai %s" % vai, ct._kiem_ghi_so, Exception)


@ca("#498: bếp trưởng, giám đốc và quản lý công thức vẫn ghi sổ được")
def _ghi_so_duoc():
	for vai in (["Manufacturing Manager"], ["System Manager"], ["Giám đốc"],
			["AP Giám đốc"], [VAI_QLCT]):
		with _voi(vai):
			ct._kiem_xem()
			ct._kiem_soan()
			ct._kiem_ghi_so()


@ca("#498: người ngoài không mở được màn, và Manufacturing User chỉ xem")
def _nguoi_ngoai():
	for vai in (["Stock User"], ["Sales User"], ["Bộ phận đặt hàng"], []):
		with _voi(vai):
			nem("xem với vai %s" % vai, ct._kiem_xem, Exception)
			nem("soạn với vai %s" % vai, ct._kiem_soan, Exception)
	# Manufacturing User la vai xem, KHONG phai vai soan. Giu nguyen nhu
	# truoc ban nay: 15 tai khoan dang giu no, mo cua soan cho ca 15 la
	# vuot qua dieu anh Viet chot.
	with _voi(["Manufacturing User"]):
		ct._kiem_xem()
		nem("Manufacturing User không soạn", ct._kiem_soan, Exception)


@ca("#498: cửa soạn bao trọn cửa ghi sổ, cửa xem bao trọn cửa soạn")
def _bao_nhau():
	dung("ghi sổ nằm trong soạn", ct._vai_ghi_so() <= ct._vai_soan())
	dung("soạn nằm trong xem", ct._vai_soan() <= ct._vai_xem())
	dung("bếp phó chưa lọt vào ghi sổ", "Bếp phó" not in ct._vai_ghi_so())
	dung("quầy bar chưa lọt vào ghi sổ", VAI_BAR not in ct._vai_ghi_so())


@ca("#498: vai Quầy Bar do mã nguồn dựng, không bấm tay trên Desk")
def _vai_do_ma_nguon():
	ds = [m for m in BANG_VAI if m["vai"] == VAI_BAR]
	la("có đúng một dòng trong BANG_VAI", len(ds), 1)
	la("vai bộ phận đơn lẻ, không gắn hồ sơ", ds[0]["ho_so"], "")
	la("không kéo thêm vai có sẵn nào", tuple(ds[0]["them_san"]), ())


@ca("#498: danh sách vai bên JS khớp từng vai với máy chủ")
def _hai_lop_khop():
	src = io.open(JS, encoding="utf-8").read()

	def vai_trong(ten):
		# Cat dung than ham roi nhat moi hasRole('...') trong do.
		neo = "function %s() {" % ten
		dung("tìm thấy %s trong JS" % ten, neo in src)
		than = src.split(neo, 1)[1].split("\n}", 1)[0]
		return set(re.findall(r"hasRole\('([^']+)'\)", than))

	# `ctSoanDuoc` va `ctXemDuoc` goi long nhau nen phai cong don len.
	gs = vai_trong("ctGhiSoDuoc")
	soan = gs | vai_trong("ctSoanDuoc")
	xem = soan | vai_trong("ctXemDuoc")
	la("JS ghi sổ khớp máy chủ", gs, ct._vai_ghi_so())
	la("JS soạn khớp máy chủ", soan, ct._vai_soan())
	la("JS xem khớp máy chủ", xem, ct._vai_xem())


@ca("#498: từng cửa gọi ĐÚNG phép kiểm, không phải chỉ có phép kiểm nằm đó")
def _noi_dung_cua():
	"""Điều 16: có hàm kiểm trong tệp không chứng minh cửa nào gọi nó.

	Gắn máy đếm vào ba phép kiểm rồi GỌI THẬT từng cửa. Cửa nào chưa nối
	hoặc nối nhầm phép kiểm là lộ ngay ở đây. Lỗi phát sinh SAU phép kiểm
	(không có cơ sở dữ liệu) thì bỏ qua, vì cái cần đo là ai được gọi.
	"""
	mong = {
		"danh_sach": "xem", "chi_tiet": "xem",
		"tao_moi": "soan", "sua_nhap": "soan",
		"dieu_chinh": "soan", "bo_nhap": "soan",
		"ghi_so": "ghi_so",
	}
	doi_so = {
		"danh_sach": (), "chi_tiet": ("BOM-X",), "tao_moi": ("MON", 1),
		"sua_nhap": ("BOM-X",), "dieu_chinh": ("BOM-X",),
		"bo_nhap": ("BOM-X",), "ghi_so": ("BOM-X",),
	}
	for ten, cua in mong.items():
		dem = []
		with patch.object(ct, "_kiem_xem", lambda: dem.append("xem")), \
				patch.object(ct, "_kiem_soan", lambda: dem.append("soan")), \
				patch.object(ct, "_kiem_ghi_so", lambda: dem.append("ghi_so")):
			try:
				getattr(ct, ten)(*doi_so[ten])
			except Exception:
				pass
		la("cửa %s gọi đúng một phép kiểm" % ten, len(dem), 1)
		la("cửa %s gọi phép kiểm nào" % ten, dem[0], cua)


@ca("#498: ghi_so từ chối bếp phó và quầy bar ngay trước khi đụng dữ liệu")
def _ghi_so_chan_that():
	for vai in (["Bếp phó"], [VAI_BAR], ["Bếp phó", "Manufacturing User"]):
		with _voi(vai):
			nem("ghi_so với vai %s" % vai, lambda: ct.ghi_so("BOM-X"), Exception)

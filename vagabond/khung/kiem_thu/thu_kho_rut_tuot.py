# -*- coding: utf-8 -*-
"""Ba việc bên Bếp ngày 28/08/2026.

MỘT: ba ô kho trên lệnh sản xuất phải tự điền theo món, đừng bắt Khải chọn
lại mỗi lần.

HAI: 23 trên 23 mã Bánh khuôn (C2) đang mang cờ "Làm tươi, không giữ tồn
kho". Sai: theo tài liệu 21/08 thì chỉ chặng BTP thành phần mới làm tươi,
C1 và C2 phải giữ tồn vì bánh khuôn nướng hôm nay để mai ráp.

BA: tắt hai kho logic BTP sơ cấp và BTP sẵn sàng ở cả hai bếp, mọi lệnh rút
nguyên liệu từ kho Nguyên liệu và cũng nhập trả về đó, trừ thành phẩm.

Đo trên site cùng ngày, và đây là căn cứ của việc ba:

* Bốn kho trung gian có 23 bản ghi tồn mà tồn đều 0, KHÔNG bút toán kho nào
  từng đi qua.
* Sáu lệnh sản xuất từng trỏ vào chúng thì cả sáu đã bị huỷ - đó chính là
  các lệnh Khải thử rồi gặp "thiếu nguyên liệu".
* Hàng thật nằm ở kho Nguyên liệu: Pastry 132 mã có tồn, Baker 84 mã.
"""

import io
import os

from vagabond import kho_san_xuat as k
from vagabond import phantom as ph
from vagabond.khung.kiem_thu.nen import ca, dung, la

HAU_TO = " - TV"


def _py(ten):
	goc = os.path.dirname(os.path.abspath(k.__file__))
	return io.open(os.path.join(goc, ten), encoding="utf-8").read()


# ------------------------------------------------- ba kho của một lệnh


@ca("bán thành phẩm: cả ba kho đều là kho Nguyên liệu của bếp")
def _():
	for chang in (k.BTP_SO_CAP, k.BTP_SAN_SANG):
		nguon, dd, dich = k.kho_cua_lenh(chang, "pastry", HAU_TO)
		la("nguồn %s" % chang, nguon, "Pastry - Nguyên liệu - TV")
		la("dở dang %s" % chang, dd, "Pastry - Nguyên liệu - TV")
		la("đích %s" % chang, dich, "Pastry - Nguyên liệu - TV")


@ca("thành phẩm: lấy ở kho Nguyên liệu, nhập về kho Thành phẩm")
def _():
	nguon, dd, dich = k.kho_cua_lenh(k.THANH_PHAM, "baker", HAU_TO)
	la("nguồn", nguon, "Baker - Nguyên liệu - TV")
	la("dở dang", dd, "Baker - Nguyên liệu - TV")
	la("đích", dich, "Baker - Thành phẩm - TV")


@ca("kho dở dang đi CHUNG với kho nguyên liệu, không tách riêng")
def _():
	# Bếp không có khu vực dở dang riêng. Tách ra chỉ đẻ thêm hai bút toán
	# chuyển kho cho mỗi mẻ mà không ai đọc.
	for chang in (k.BTP_SO_CAP, k.BTP_SAN_SANG, k.THANH_PHAM):
		nguon, dd, _d = k.kho_cua_lenh(chang, "pastry", HAU_TO)
		la("chặng %s" % chang, dd, nguon)


@ca("thiếu dữ kiện thì trả ba giá trị rỗng, không đoán bừa")
def _():
	la("không biết chặng", k.kho_cua_lenh(None, "pastry", HAU_TO), (None, None, None))
	la("không biết bếp", k.kho_cua_lenh(k.THANH_PHAM, None, HAU_TO), (None, None, None))
	la("bếp lạ", k.kho_cua_lenh(k.THANH_PHAM, "bar", HAU_TO), (None, None, None))
	la("chặng nguyên liệu không phải món làm ra",
		k.kho_cua_lenh(k.NGUYEN_LIEU, "pastry", HAU_TO), (None, None, None))


# --------------------------------------------------- luật rút tuột


@ca("mọi chặng đều chỉ rút nguyên liệu từ kho Nguyên liệu")
def _():
	for chang in (k.BTP_SO_CAP, k.BTP_SAN_SANG, k.THANH_PHAM):
		la("chặng %s" % chang, k.LUAT_NGUON[chang], [k.NGUYEN_LIEU])


@ca("hai kho trung gian không còn nằm trong luật nguồn của chặng nào")
def _():
	for chang, uu_tien in k.LUAT_NGUON.items():
		for bo in k.CHANG_TAT:
			la("chặng %s không được lấy từ %s" % (chang, bo), bo in uu_tien, False)


@ca("chọn kho nguồn: nguyên liệu thô lấy ở kho Nguyên liệu")
def _():
	la("làm thành phẩm, dòng là nguyên liệu",
		k.chon_kho_nguon(k.THANH_PHAM, k.NGUYEN_LIEU, "pastry"),
		"Pastry - Nguyên liệu - TV")


@ca("dòng nguyên liệu là bán thành phẩm thì luật KHÔNG phủ, giữ nguyên kho người chọn")
def _():
	# Trả None nghĩa là không đổi. Bán thành phẩm nay cũng nằm ở kho Nguyên
	# liệu, nhưng đó là việc của ô kho trên lệnh chứ không phải chỗ này -
	# tự ý đổi thì mất đường cho người tạo lệnh chỉ tay vào kho khác.
	la("btp sơ cấp làm nguyên liệu",
		k.chon_kho_nguon(k.THANH_PHAM, k.BTP_SO_CAP, "pastry"), None)


@ca("bảng kho đích: chỉ thành phẩm mới rời kho Nguyên liệu")
def _():
	la("sơ cấp", k.LUAT_KHO_DICH[k.BTP_SO_CAP], k.NGUYEN_LIEU)
	la("sẵn sàng", k.LUAT_KHO_DICH[k.BTP_SAN_SANG], k.NGUYEN_LIEU)
	la("thành phẩm", k.LUAT_KHO_DICH[k.THANH_PHAM], k.THANH_PHAM)


@ca("luật cũ bốn chặng còn nguyên trong ghi chú để bật lại được")
def _():
	m = _py("kho_san_xuat.py")
	dung("phải giữ bản cũ trong ghi chú",
		"BTP_SAN_SANG: [BTP_SO_CAP, NGUYEN_LIEU]" in m)


# ------------------------------------------------ cờ Làm tươi đúng chặng


@ca("chỉ chặng BTP thành phần được mang cờ Làm tươi")
def _():
	dung("BTP thành phần", ph.chang_duoc_lam_tuoi(ph.CHANG_BTP))
	la("Ruột bánh C1", ph.chang_duoc_lam_tuoi(ph.CHANG_C1), False)
	la("Bánh khuôn C2", ph.chang_duoc_lam_tuoi(ph.CHANG_C2), False)
	la("Thành phẩm", ph.chang_duoc_lam_tuoi(ph.CHANG_TP), False)
	la("chặng rỗng", ph.chang_duoc_lam_tuoi(""), False)
	la("chặng None", ph.chang_duoc_lam_tuoi(None), False)


@ca("hàng rào cờ Làm tươi có nói rõ phải làm gì, không chỉ nói không")
def _():
	m = _py("phantom.py")
	doan = m.split("def chan_lam_tuoi_sai_chang")[1].split("\n@frappe")[0]
	dung("phải chỉ cách sửa", "Cách sửa" in doan)
	dung("phải nói tên chặng của món", "%s" in doan)
	# Món chưa có công thức thì chưa biết chặng, chặn là cản người khai món mới.
	dung("chưa có công thức thì không chặn", "if not chang" in doan)


@ca("hàm soát cờ Làm tươi chạy thử là mặc định")
def _():
	m = _py("phantom.py")
	doan = m.split("def soat_lam_tuoi")[1].split("\n@frappe")[0]
	dung("mặc định phải là chạy thử", "chay_that=0" in m.split("def soat_lam_tuoi")[0][-80:]
		or "def soat_lam_tuoi(chay_that=0)" in m)
	dung("chỉ ghi khi được lệnh", "if chay_that:" in doan)


# ------------------------------------------- tắt kho, và các hàng rào


@ca("hàm tắt kho tự kiểm bốn điều trước khi ghi, không tin lần đo cũ")
def _():
	m = _py("kho_san_xuat.py")
	doan = m.split("def tat_kho_trung_gian")[1].split("\ndef ")[0]
	for t in ("Bin", "Stock Ledger Entry", "Work Order", "Item Default"):
		dung("phải tự kiểm %s" % t, t in doan)
	dung("còn vướng là dừng, không tắt kho nào cả", "dung_vi" in doan)


@ca("tắt kho chứ KHÔNG xoá")
def _():
	m = _py("kho_san_xuat.py")
	doan = m.split("def tat_kho_trung_gian")[1].split("\ndef ")[0]
	dung("phải đặt cờ disabled", '"disabled", 1' in doan)
	la("không được xoá kho", "delete_doc" in doan, False)


@ca("hàm tắt kho chạy thử là mặc định")
def _():
	m = _py("kho_san_xuat.py")
	dung("mặc định chạy thử", "def tat_kho_trung_gian(chay_that=0)" in m)


@ca("gán kho lên lệnh CHỈ điền ô đang trống, không đè lên chữ người thật")
def _():
	m = _py("kho_san_xuat.py")
	doan = m.split("def gan_kho_lenh")[1].split("\ndef ")[0]
	dung("phải kiểm ô đang trống", "not (doc.get(o) or" in doan)
	dung("phải kiểm kho có thật", 'frappe.db.exists("Warehouse"' in doan)
	# Điền kho là tiện ích. Hỏng thì để người tạo lệnh tự chọn như trước.
	la("không được ném lỗi", "frappe.throw" in doan, False)
	dung("phải ghi Error Log khi hỏng", "log_error" in doan)


@ca("hook gán kho đặt ở before_validate, không phải validate")
def _():
	m = _py("hooks.py")
	# ERPNext dùng ba ô kho để dựng bảng nguyên liệu NGAY TRONG validate.
	# Điền muộn hơn là bảng đó đã dựng xong bằng kho cũ.
	# Doc nguoc len tu cho khai hook, tim ten su kien gan nhat phia truoc.
	truoc = m.split("vagabond.kho_san_xuat.gan_kho_lenh")[0]
	su_kien = [d.strip() for d in truoc.splitlines() if '":' in d and "vagabond." not in d]
	dung("su kien gan nhat phia truoc phai la before_validate",
		su_kien[-1].startswith('"before_validate":'))


@ca("hai hook mới đều đã nối vào hooks.py")
def _():
	m = _py("hooks.py")
	dung("gán ba kho cho lệnh", "vagabond.kho_san_xuat.gan_kho_lenh" in m)
	dung("hàng rào cờ làm tươi", "vagabond.phantom.chan_lam_tuoi_sai_chang" in m)
	la("khoá Item chỉ được khai một lần", m.count('\t"Item": {'), 1)

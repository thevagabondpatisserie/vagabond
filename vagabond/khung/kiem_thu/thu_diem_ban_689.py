# -*- coding: utf-8 -*-
"""v689: điểm bán mới hoặc đang tắt phải chọn được ở mọi nghiệp vụ sau bán (anh Việt 23/11/2026).

Sự cố: chị Dung (Kế toán) báo màn Biên nhận nộp tiền mặt không có điểm "Hội chợ",
trong khi Báo cáo BC03 có 11 đơn Hội chợ (1.135.000 đ) chưa nộp tiền. Điểm Hội chợ
có trong danh mục điểm bán nhưng đang TẮT sau sự kiện, mà màn biên nhận chỉ đọc
"điểm đang bật". Hai màn khác (Hoá đơn bán ra, Khuyến mãi) còn gõ tay ba điểm
ngay trong mã, nên thêm điểm thứ tư là không có chip.

Luật anh Việt chốt: có thêm điểm bán thì mọi nghiệp vụ liên quan phải chọn được
điểm đó. Cụ thể:
- `diem_ban.ds(chi_bat=True)` CHỈ dùng cho màn đang bán, nhận đơn. Danh sách chỗ
  được gọi nằm trong CHI_DANG_BAN dưới đây, mỗi chỗ một lý do. Chỗ mới phải ghi
  lý do vào đây, không thì ca đỏ.
- Màn trình duyệt không gõ tay danh sách mã điểm bán.

Phần hành vi của màn (chip, tên điểm) chạy ở hanh_vi/diem_ban_moi_nghiep_vu_689.js.
"""

import ast
import subprocess
import sys
import unittest.mock as um
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la
from vagabond.khung.kiem_thu.thu_su_co_290 import nap

gia_lap()

GOC = Path(__file__).resolve().parents[3]
APP = GOC / "vagabond"

# (tệp, hàm) -> lý do được chỉ đọc điểm ĐANG BẬT.
CHI_DANG_BAN = {
	("ban_hang.py", "_nguon_don"): "màn tính tiền: nguồn đơn của các quầy đang bán",
	("ban_hang.py", "_quay"): "màn tính tiền: thẻ chọn quầy đang bán",
	("ban_hang.py", "cau_hinh_ban_hang"): "cấu hình màn tính tiền, máy in, mẫu in của quầy đang bán",
	("ban_hang.py", "_diem_cua_bill"): "bill không mang mã quầy: suy điểm online đang nhận đơn theo nguồn",
	("diem_ban.py", "quay_dang_bat"): "đúng tên hàm: quầy đang bật",
	("diem_ban.py", "diem_cua_nguon"): "nhập đơn tay: nguồn đơn thuộc điểm đang nhận đơn",
	("diem_ban.py", "diem_co_gia_rieng"): "giá riêng áp lúc bán ở quầy đang bán",
	("pt_thanh_toan.py", "_kiem_nguon"): "kiểm phương thức thanh toán của nguồn đơn đang bán",
	("tai_chinh.py", "_cac_nguon"): "két tiền mặt của điểm đang bật; điểm đã tắt nộp hết tiền qua Biên nhận",
	("tai_khoan.py", "danh_sach"): "chỉ phần cảnh báo điểm đang bán chưa khai tài khoản; danh sách khai dùng mọi điểm",
	("tra_truoc_khach.py", "_ds_quay"): "thu tiền trả trước tại quầy đang bán",
	("pickup.py", "ds"): "điểm khách nhận bánh trên web",
	("banh_si.py", "_ds_diem"): "nơi khách sỉ nhận bánh",
	("thiet_ke_rieng.py", "_ds_diem"): "nơi khách nhận bánh thiết kế riêng",
	("tuyen_dung.py", "_noi_lam_mau"): "nơi làm việc đang tuyển",
	("thu_khung.py", "_cac_quay"): "chân thư: địa chỉ các quầy đang mở",
	("kiem_kho.py", "_diem_co_quay"): "tồn có thể bán của quầy đang bán, đẩy sang Pancake",
	("goi_mon_ban.py", "_diem"): "gọi món tại bàn ở quầy đang bán",
	("goi_mon_ban.py", "diem_in_qr"): "in mã QR gọi món cho quầy đang bán",
	("may_in.py", "kho_theo_vai_tro"): "máy in của quầy đang bán",
	("may_in.py", "tuyen_qz"): "máy in của quầy đang bán",
}


def _cho_goi_chi_bat():
	"""(tệp, hàm bao ngoài) của mọi lời gọi `...ds(chi_bat=True)` trong mã app."""
	ra = set()
	for p in sorted(APP.glob("*.py")):
		cay = ast.parse(p.read_text(encoding="utf-8"))
		for ham in ast.walk(cay):
			if not isinstance(ham, (ast.FunctionDef, ast.AsyncFunctionDef)):
				continue
			for n in ast.walk(ham):
				if not isinstance(n, ast.Call):
					continue
				ten = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
				if ten != "ds":
					continue
				if any(k.arg == "chi_bat" and isinstance(k.value, ast.Constant) and k.value.value is True
						for k in n.keywords):
					ra.add((p.name, ham.name))
	return ra


@ca("v689: chỉ màn đang BÁN mới đọc điểm đang bật; mọi chỗ gọi chi_bat=True có lý do trong CHI_DANG_BAN")
def _chi_dang_ban():
	co = _cho_goi_chi_bat()
	moi = sorted(co - set(CHI_DANG_BAN))
	la("chỗ gọi chi_bat=True chưa có lý do (nghiệp vụ sau bán phải dùng mọi điểm)", moi, [])
	thua = sorted(set(CHI_DANG_BAN) - co)
	la("lý do thừa cho chỗ đã đổi (xoá khỏi CHI_DANG_BAN)", thua, [])
	for k in [("nop_quy.py", "doanh_thu_diem"), ("tru_kho_bu.py", "ds_chua_tru_kho"), ("can_tru_san.py", "diem_ban"),
			("khuyen_mai.py", "_quay_ds"), ("bien_tap_menu.py", "_diem_co_quay"), ("tai_khoan.py", "bang_theo_nguon")]:
		dung("%s %s dùng mọi điểm" % k, k not in co)


def _diem_gia():
	"""diem_ban.ds giả: ba điểm đang bật và điểm hội chợ đang tắt."""
	tat_ca = [
		{"ma": "SALES", "ten": "Sales Online", "ten_ngan": "Sales Online", "quay": "", "bat": 1},
		{"ma": "TCV", "ten": "The Vagabond District 1", "ten_ngan": "District 1", "quay": "TCV", "bat": 1},
		{"ma": "NVHTN", "ten": "Nhà Văn Hóa Thanh Niên", "ten_ngan": "NVHTN", "quay": "NVHTN", "bat": 1},
		{"ma": "SUKIEN", "ten": "Bán hàng sự kiện - hội chợ", "ten_ngan": "Hội chợ", "quay": "SUKIEN", "bat": 0},
	]
	return lambda chi_bat=False: [d for d in tat_ca if d["bat"]] if chi_bat else list(tat_ca)


@ca("v689: Biên nhận nộp tiền liệt kê cả điểm đang tắt (Hội chợ), đúng sự cố chị Dung báo 23/11")
def _bien_nhan():
	from vagabond import diem_ban

	g = {"frappe": sys.modules["frappe"], "_kiem_quyen": lambda: None}
	f = nap("nop_quy.py", "doanh_thu_diem", g)
	with um.patch.object(diem_ban, "ds", _diem_gia()):
		ra = f()
	la("điểm trên màn biên nhận", [d["ma"] for d in ra["diem"]], ["SALES", "TCV", "NVHTN", "SUKIEN"])
	la("tên ngắn của điểm tắt", ra["diem"][3]["ten_ngan"], "Hội chợ")


@ca("v689: chip điểm của Hoá đơn bán ra: mã quầy, điểm không quầy là SALES, có điểm đang tắt, không trùng")
def _chip_hd():
	f = nap("ke_toan.py", "chip_diem_hd", {})
	la("chip", f(_diem_gia()()), [{"ma": "SALES", "ten": "Sales Online"}, {"ma": "TCV", "ten": "District 1"},
		{"ma": "NVHTN", "ten": "NVHTN"}, {"ma": "SUKIEN", "ten": "Hội chợ"}])
	la("hai điểm không quầy gộp một chip SALES", f([{"ma": "A", "ten": "A", "quay": ""}, {"ma": "B", "ten": "B", "quay": ""}]),
		[{"ma": "SALES", "ten": "A"}])


@ca("v689: màn trình duyệt không gõ tay danh sách mã điểm bán")
def _js_khong_go_tay():
	import re

	mau = re.compile(r"""(\[\s*'(?:SALES|TCV|NVHTN)'\s*,|ma:\s*'(?:SALES|TCV|NVHTN)'|\b(?:SALES|TCV|NVHTN)\s*:\s*'[^']+')""")
	bep = APP / "public" / "js" / "bep"
	thay = []
	for p in sorted(bep.glob("*.js")):
		for i, d in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
			if mau.search(d):
				thay.append("%s:%d" % (p.name, i))
	la("chỗ gõ tay mã điểm bán", thay, [])


@ca("v689: hành vi màn (chip Hoá đơn bán ra, tên điểm trong Khuyến mãi) chạy bằng node")
def _node():
	r = subprocess.run(["node", str(Path(__file__).parent / "hanh_vi" / "diem_ban_moi_nghiep_vu_689.js")],
		capture_output=True, text=True, timeout=120)
	dung("node: " + (r.stdout + r.stderr)[-600:], r.returncode == 0)


@ca("v689: cửa máy chủ của màn Hoá đơn bán ra vẫn mở; hàm phụ chip_diem_hd không thành cửa (bench 23/11: 403)")
def _cua_mo():
	cay = ast.parse((APP / "ke_toan.py").read_text(encoding="utf-8"))
	mo = {n.name for n in cay.body if isinstance(n, ast.FunctionDef) and any(
		"whitelist" in ast.unparse(d) for d in n.decorator_list)}
	la("ds_hoa_don_ban mở, chip_diem_hd không", ("ds_hoa_don_ban" in mo, "chip_diem_hd" in mo), (True, False))

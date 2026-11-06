"""v642 (chị Dung 06/11/2026): "Hoàn ứng có hóa đơn cũng có thêm nút kết nối
với sao kê MB NHV giống hoàn ứng không hóa đơn thì rõ ràng hơn".

Màn hoàn ứng CÓ hoá đơn nối được giao dịch sao kê vào từng hoá đơn đã tick.
Giao dịch là chứng từ tiền đã chi; số tiền vẫn theo hoá đơn. Máy chủ chỉ nhận
giao dịch CHI RA từ tài khoản của chính người được hoàn ứng, và chỉ ở luồng
hoàn ứng có hoá đơn. Chặn trùng giao dịch giữa các hồ sơ do cửa lưu hồ sơ lo
(như mọi luồng). Hành vi màn hình: hanh_vi/chay.js, ca "v642 hoan ung CO hoa don".
"""
import json
from unittest.mock import patch

import frappe

from vagabond import ho_so_tt as hs
from vagabond import hoan_ung_noi_bo as hn
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

GD = {
	"FT2": {"name": "BT-2", "reference_number": "FT2", "bank_account": "MB-NHV", "withdrawal": 500000, "docstatus": 1},
	"FTV": {"name": "BT-3", "reference_number": "FTV", "bank_account": "MB-NHV", "withdrawal": 0, "docstatus": 1},
	"FTK": {"name": "BT-4", "reference_number": "FTK", "bank_account": "ACB-KHAC", "withdrawal": 500000, "docstatus": 1},
	"FTH": {"name": "BT-5", "reference_number": "FTH", "bank_account": "MB-NHV", "withdrawal": 500000, "docstatus": 2},
}


@ca("v642 hoàn ứng có HĐ (phép thuần): giao dịch phải có trên sao kê, là khoản chi ra, đi từ tài khoản của người được hoàn ứng")
def _thuan():
	tk = {"MB-NHV"}
	la("chi ra đúng tài khoản", hn.loi_gd_hoan_ung(GD["FT2"], tk, "FT2"), "")
	dung("không có trên sao kê", "Không tìm thấy" in hn.loi_gd_hoan_ung(None, tk, "FTX"))
	dung("bản ghi đã huỷ coi như không có", "Không tìm thấy" in hn.loi_gd_hoan_ung(GD["FTH"], tk, "FTH"))
	dung("tiền vào", "tiền vào" in hn.loi_gd_hoan_ung(GD["FTV"], tk, "FTV"))
	dung("tài khoản người khác", "không đi ra từ tài khoản" in hn.loi_gd_hoan_ung(GD["FTK"], tk, "FTK"))


@ca("v642 hoàn ứng có HĐ: máy chủ đọc danh sách tài khoản của ĐÚNG người được hoàn ứng rồi kiểm từng giao dịch; sai thì chặn, không có giao dịch thì không đọc gì")
def _kiem():
	hoi = []

	def tk(nguoi=None):
		hoi.append(nguoi)
		return {"tk": [{"ma": "MB-NHV", "nguoi": "NCC-9"}], "doan": 0}
	with patch.object(hs, "ds_tk_hoan_ung", side_effect=tk), patch.object(hn, "giao_dich", side_effect=lambda m: GD.get(m)):
		hs._kiem_gd_hoan_ung([{"ma_giao_dich": "FT2"}, {"ma_giao_dich": ""}], " NCC-9 ")
		la("hỏi tài khoản của người được hoàn ứng", hoi, ["NCC-9"])
		nem("giao dịch tài khoản khác bị chặn", lambda: hs._kiem_gd_hoan_ung([{"ma_giao_dich": "FTK"}], "NCC-9"), frappe.ValidationError)
		nem("tiền vào bị chặn", lambda: hs._kiem_gd_hoan_ung([{"ma_giao_dich": "FTV"}], "NCC-9"), frappe.ValidationError)
		hoi.clear()
		hs._kiem_gd_hoan_ung([{"hoa_don": "HD-1"}], "NCC-9")
		la("không nối giao dịch nào thì không đọc tài khoản", hoi, [])


class _Dung(Exception):
	pass


@ca("v642 hoàn ứng có HĐ: cửa lập hồ sơ mang mã giao dịch của từng hoá đơn vào dòng và gọi kiểm giao dịch với người được hoàn ứng; luồng trả thẳng nhà cung cấp gửi mã giao dịch thì bị chặn")
def _tao():
	hd = frappe._dict(name="HD-1", supplier="NCC-1", supplier_name="NCC A", posting_date="2026-11-01", bill_date="2026-11-01",
		bill_no="0001234", due_date="2026-11-30", grand_total=500000, outstanding_amount=500000, docstatus=1)
	bat = {}

	def kiem_gd(dong, nguoi):
		bat["dong"], bat["nguoi"] = dong, nguoi
		raise _Dung()
	gui = json.dumps([{"hoa_don": "HD-1", "so_tien": 500000, "ma_giao_dich": " FT2 "}])
	with patch.object(hs, "_kiem"), patch.object(frappe.db, "get_value", return_value=hd), \
			patch.object(frappe, "parse_json", json.loads, create=True), \
			patch.object(hs, "_chan_hoa_don_trung"), patch.object(hs, "_soi_phieu_noi_bo"), \
			patch.object(hs, "_kiem_gd_hoan_ung", side_effect=kiem_gd):
		try:
			hs.tao(hoa_don=gui, loai=hs.LOAI_HU_HD, nguoi_ung="NCC-9", tk_hoan="MB-NHV")
			raise AssertionError("phải tới bước kiểm giao dịch")
		except _Dung:
			pass
		la("dòng mang mã giao dịch đã gọt", [d["ma_giao_dich"] for d in bat["dong"]], ["FT2"])
		la("kiểm theo người được hoàn ứng", bat["nguoi"], "NCC-9")
		bat.clear()
		nem("luồng nhà cung cấp gửi mã giao dịch: chặn", lambda: hs.tao(hoa_don=gui, loai=hs.LOAI_NCC, ncc="NCC-1"), frappe.ValidationError)
		la("bị chặn trước bước kiểm giao dịch", bat, {})
		khong = json.dumps([{"hoa_don": "HD-1", "so_tien": 500000}])
		try:
			hs.tao(hoa_don=khong, loai=hs.LOAI_HU_HD, nguoi_ung="NCC-9", tk_hoan="MB-NHV")
		except _Dung:
			pass
		la("không nối thì dòng mang mã rỗng", [d["ma_giao_dich"] for d in bat["dong"]], [""])


@ca("v642 hoàn ứng có HĐ (node, mã màn thật): nút Nối sao kê, gợi ý đúng số tiền, chặn nối hai lần, gửi mã giao dịch")
def _man():
	import re
	import subprocess
	from pathlib import Path
	goc = Path(__file__).resolve().parents[3]
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/chay.js"], cwd=goc, capture_output=True, text=True, timeout=120)
	la(r.stdout[-2000:] + r.stderr[-1000:], r.returncode, 0)
	dung("có ca v642", "v642 hoan ung CO hoa don" in (Path(goc) / "vagabond/khung/kiem_thu/hanh_vi/chay.js").read_text())
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca", m and int(m.group(1)) >= 67)


@ca("v642 Codex #545 vòng 1: người được hoàn ứng chưa gắn tài khoản quỹ tạm ứng (danh sách tài khoản là bản đoán) thì KHÔNG nối sao kê được; giao dịch phải đi từ tài khoản của chính người đó")
def _doan_khong_nhan():
	gd = {"FTK": {"name": "BT-9", "reference_number": "FTK", "bank_account": "ACB-KHAC", "withdrawal": 500000, "docstatus": 1}}
	doan = {"tk": [{"ma": "ACB-KHAC", "nguoi": "NCC-1"}], "doan": 1}
	with patch.object(hs, "ds_tk_hoan_ung", return_value=doan), patch.object(hn, "giao_dich", side_effect=lambda m: gd.get(m)):
		nem("danh sách đoán: chặn nối sao kê", lambda: hs._kiem_gd_hoan_ung([{"ma_giao_dich": "FTK"}], "NCC-9"), frappe.ValidationError)
	# Chưa có tài khoản nào thuộc quỹ 141: danh sách đoán là MỌI tài khoản công ty có sổ cái, có thể
	# có cả tài khoản đứng tên người này nhưng không phải tài khoản ứng tiền. Vẫn chặn.
	gd["FTC"] = {"name": "BT-8", "reference_number": "FTC", "bank_account": "CTY-1121", "withdrawal": 500000, "docstatus": 1}
	cty = {"tk": [{"ma": "CTY-1121", "nguoi": "NCC-9"}], "doan": 1}
	with patch.object(hs, "ds_tk_hoan_ung", return_value=cty), patch.object(hn, "giao_dich", side_effect=lambda m: gd.get(m)):
		nem("danh sách đoán có tài khoản đứng tên người này: vẫn chặn", lambda: hs._kiem_gd_hoan_ung([{"ma_giao_dich": "FTC"}], "NCC-9"), frappe.ValidationError)
	rieng = {"tk": [{"ma": "MB-NHV", "nguoi": "NCC-9"}, {"ma": "ACB-KHAC", "nguoi": "NCC-1"}], "doan": 0}
	with patch.object(hs, "ds_tk_hoan_ung", return_value=rieng), patch.object(hn, "giao_dich", side_effect=lambda m: gd.get(m)):
		nem("tài khoản của người khác lọt danh sách: vẫn chặn", lambda: hs._kiem_gd_hoan_ung([{"ma_giao_dich": "FTK"}], "NCC-9"), frappe.ValidationError)

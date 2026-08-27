# -*- coding: utf-8 -*-
"""Kiem thu: hoa don dien tu thanh chung tu, va cho sot (v313).

Bai anh Viet giao 26/08/2026 sau khi ben Uyen bao ngay 4/8 Ngon Co Dien
xuat 3 hoa don ma he chi lay ve 2.

Quet ra 125 to bi nuot, 157.604.325 d, chia hai nhom:
    22 to dau vao   126.427.733 d   lech thue tung dong
   103 to dau ra     31.176.592 d   ma hang khong co trong danh muc

Bo ca kiem nay chot BON quyet dinh, ca bon deu la loai doc lai se thay
"ky ky" va co nguoi sua nguoc lai:

  1. Xoa mau thue mat hang khoi dong chung tu sinh ra. Con so thue cua
     hoa don dien tu la con so da gui co quan thue, no thang.
  2. Hong thi KHONG duoc dong dau da_tao_chung_tu = 1.
  3. Hang doi xep theo so lan thu tang dan, de to hong khong chiem cho.
  4. Hoa don DAU RA khong tu dung, chi liet ke (Dieu 11).
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.minvoice_chung_tu import (
	LOAI_RA, NGUONG_KHOP, TT_KHOI_DUNG, can_theo_truoc_thue, dong_tu_hoa_don,
	gom_theo_ly_do, khoi_dung_duoc, rut_gon_loi,
)

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def chi_phan_ma(nguon):
	"""Bo chu thich va docstring khoi mot tep Python. THUAN."""
	import tokenize

	ra = []
	dau_khoi = {tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
		tokenize.DEDENT, tokenize.ENCODING}
	truoc = tokenize.NEWLINE
	for tk in tokenize.generate_tokens(io.StringIO(nguon).readline):
		if tk.type == tokenize.COMMENT:
			continue
		if tk.type == tokenize.STRING and truoc in dau_khoi:
			truoc = tokenize.STRING
			continue
		if tk.type not in (tokenize.NL, tokenize.INDENT, tokenize.DEDENT):
			truoc = tk.type
		ra.append(tk.string)
	return "\n".join(ra)


MA = _doc("minvoice_chung_tu.py")
MA_CODE = chi_phan_ma(MA)
MA_TOKEN = "\n" + MA_CODE + "\n"
MA_CUA = _doc("khung", "kiem_thu", "thu_cua_ngo.py")
MA_TRUONG = _doc("truong_tu_them.py")
MA_KEO = _doc("minvoice_dong_bo.py")


def co_cum(*token):
	return ("\n" + "\n".join(token) + "\n") in MA_TOKEN


# --------------------------------------------------------- dong hang


@ca("hoa don dien tu: dong co du don gia thi giu nguyen so luong")
def _():
	x = dong_tu_hoa_don({"mhhdvu": "NVLT00001", "ten": "Bột mì",
		"dvtinh": "Kg", "sluong": 3, "dgia": 25000, "thtien": 75000})
	la("mã hàng", x["ma"], "NVLT00001")
	la("số lượng", x["sl"], 3)
	la("đơn giá", x["gia"], 25000)
	la("thành tiền", x["tien"], 75000)


@ca("hoa don dien tu: dong THIEU don gia thi ha so luong ve 1")
def _():
	# Hoa don tien dien, tien nuoc, phi dich vu deu chi co thanh tien.
	# Ban cu giu nguyen so luong roi van lay thanh tien lam don gia, nen
	# thanh tien bi nhan len bang so luong lan: hoa don dien 53 trieu
	# tung thanh 814 ty.
	x = dong_tu_hoa_don({"ten": "Tiền điện tháng 8", "sluong": 5330,
		"dgia": None, "thtien": 53_000_000})
	la("số lượng về 1", x["sl"], 1)
	la("đơn giá là thành tiền", x["gia"], 53_000_000)
	la("tổng đúng bằng thành tiền", x["tien"], 53_000_000)


@ca("hoa don dien tu: dong don gia bang KHONG ma co thanh tien")
def _():
	# Ca that 27/08/2026, hoa don tiep khach Avanti C26TAV/5019: dong
	# "Phi phuc vu" ghi sluong 0, dgia 0, thtien 1.283.500. Ban cu chi bat
	# truong hop dgia la None nen dong do vao chung tu voi don gia 0, roi
	# ERPNext tu dien lai theo Bang gia nhap cua mat hang (4.500.000), lam
	# to hoa don phinh them dung 4,5 trieu.
	x = dong_tu_hoa_don({"ten": "Phí phục vụ", "sluong": 0, "dgia": 0,
		"thtien": 1_283_500})
	la("số lượng về 1", x["sl"], 1)
	la("đơn giá là thành tiền", x["gia"], 1_283_500)
	la("tổng đúng bằng thành tiền", x["tien"], 1_283_500)


@ca("hoa don dien tu: dong 0 dong that su thi van la 0, khong bia ra gia")
def _():
	# Hang tang kem, khuyen mai 0 dong. Khong duoc tu nhien co gia.
	x = dong_tu_hoa_don({"ten": "Hàng tặng kèm", "sluong": 2, "dgia": 0,
		"thtien": 0})
	la("đơn giá vẫn 0", x["gia"], 0)
	la("thành tiền vẫn 0", x["tien"], 0)


@ca("dong chung tu: ghim gia bang dung don gia tren hoa don")
def _():
	# Khong ghim thi ERPNext lay Bang gia nhap dien vao dong don gia 0.
	doan = MA.split("def _dong_pi")[1].split("\ndef ")[0]
	dung('có ghim price_list_rate', '"price_list_rate": x["gia"]' in doan)
	dung('có dập chiết khấu về 0', '"discount_percentage": 0' in doan)


@ca("hoa don dien tu: dong rong khong lam no")
def _():
	x = dong_tu_hoa_don(None)
	la("số lượng mặc định 1", x["sl"], 1)
	la("đơn giá 0", x["gia"], 0)
	la("mã rỗng", x["ma"], "")


# ------------------------------------------------------- nan tong tien


@ca("nan tong: dong hang THUA thi ghi vao o giam gia")
def _():
	# Chiet khau va giam thue theo nghi quyet deu roi vao day.
	la("thừa 200k", can_theo_truoc_thue(1_200_000, 1_000_000), ("giam", 200_000))


@ca("nan tong: dong hang THIEU thi them mot dong phi")
def _():
	# Ve may bay va phi dich vu khong nam trong dong hang khi len XML.
	la("thiếu 50k", can_theo_truoc_thue(950_000, 1_000_000), ("phi", 50_000))


@ca("nan tong: lech duoi mot dong thi coi nhu khop, khong nan")
def _():
	la("lệch 0", can_theo_truoc_thue(1_000_000, 1_000_000), ("khop", 0))
	la("lệch nửa đồng lên", can_theo_truoc_thue(1_000_000.5, 1_000_000), ("khop", 0))
	la("lệch nửa đồng xuống", can_theo_truoc_thue(999_999.5, 1_000_000), ("khop", 0))
	la("ngưỡng đúng bằng một đồng", NGUONG_KHOP, 1.0)


# ------------------------------------------------------ trang thai to


@ca("to bi thay the hoac da huy thi khoi dung chung tu")
def _():
	for tt in TT_KHOI_DUNG:
		dung("%s khỏi dựng" % tt, khoi_dung_duoc(tt))
	for tt in ("Gốc", "Thay thế", "Điều chỉnh", "", None):
		dung("%r vẫn phải dựng" % (tt,), not khoi_dung_duoc(tt))


# ------------------------------------------------------------ cau loi


@ca("cau loi: cat the HTML de o ly do doc duoc")
def _():
	# Cau that cua ERPNext co the br o giua, de nguyen thi nguoi doc thay
	# chu "<br>" giua cau trong bang.
	s = rut_gon_loi("Item Wise Tax Details do not match<br>Row 1 (Difference: 288000.0)")
	dung("không còn thẻ br", "<br>" not in s)
	dung("giữ được cả hai vế", "Item Wise Tax" in s and "288000" in s)


@ca("cau loi: rong thi van co cau de doc, khong de trong")
def _():
	for x in ("", None, "   "):
		dung("lỗi %r vẫn ra câu" % (x,), len(rut_gon_loi(x)) > 10)


@ca("gom theo ly do: dem so to va cong tien tuyet doi")
def _():
	ra = gom_theo_ly_do([
		{"ly_do": "lệch thuế", "tong_tien": 100, "loai": "Đầu vào"},
		{"ly_do": "lệch thuế", "tong_tien": -50, "loai": "Đầu vào"},
		{"ly_do": "thiếu mã", "tong_tien": 500, "loai": "Đầu ra"},
	])
	la("hai nhóm", len(ra), 2)
	la("nhóm to tiền đứng trước", ra[0]["ly_do"], "thiếu mã")
	# Cong tri tuyet doi: hoa don am cong voi hoa don duong thi triet tieu
	# nhau, nhin ra so nho gia tao.
	la("lệch thuế cộng tuyệt đối", ra[1]["tien"], 150)
	la("đếm đúng số tờ", ra[1]["so_to"], 2)


# --------------------------------------------- chot cac quyet dinh trong ma


@ca("chung tu: CO xoa mau thue mat hang khoi tung dong")
def _():
	# Day la phep sua chinh. Con so thue cua hoa don dien tu la con so da
	# gui co quan thue; mau thue tren danh muc Mon chi la du doan.
	dung("có xoá mẫu thuế mặt hàng", co_cum("item_tax_template", "=", '""'))
	# CHUOI RONG chu KHONG phai None. Ban v315 dat None va hong nguyen si:
	# `accounts_controller.set_missing_item_details` chi chep gia tri tu danh
	# muc Mon vao o nao dang la None, ma `item_tax_template` khong nam trong
	# `force_item_fields`. Dat None la ERPNext dien lai mau thue ngay trong
	# luc validate, dat chuoi rong thi no de yen.
	dung("KHÔNG đặt None, vì None là dấu hiệu cho ERPNext điền lại",
		not co_cum("item_tax_template", "=", "None"))
	dung("có xoá luôn thuế suất từng dòng",
		"item_tax_rate" in MA_CODE)
	dung("gọi trước khi ghi vào hệ",
		MA_CODE.index("bo_mau_thue_mat_hang") < MA_CODE.rindex("insert"))


@ca("chung tu: hong thi TUYET DOI khong dong dau da xong")
def _():
	# Day la cho ban cu sai nang nhat: dong dau xong ngay ca khi khong dung
	# duoc gi, nen to hong bien mat khoi moi danh sach.
	doan = MA.split("def _ghi_hong")[1].split("\ndef ")[0]
	dung("hàm ghi hỏng đặt cờ về 0", '"da_tao_chung_tu": 0' in doan)
	dung("có đếm số lần thử", "so_lan_thu" in doan)
	dung("KHÔNG có chỗ nào đặt cờ về 1 trong hàm này",
		'"da_tao_chung_tu": 1' not in doan)


@ca("chung tu: hang doi xep theo so lan thu, to hong khong chiem cho")
def _():
	dung("sắp xếp theo số lần thử trước",
		"so_lan_thu asc" in MA)


@ca("chung tu: hoa don DAU RA khong tu dung doanh thu")
def _():
	# Anh Viet chot 26/08/2026: dau ra ban le do Fabi xuat, so sach ben do da
	# ghi. He khong dung, va cung khong de chung nam mai trong danh sach con
	# sot - 103 dong bao dong gia thi y het mot danh sach khong ai doc.
	dung("có nhánh chặn đầu ra", "LOAI_RA" in MA_CODE)
	# Hang so SI van con, vi `_da_co_chung_tu` phai DOC ca hoa don ban de
	# biet to nao da co chung tu. Cai bi cam la DUNG mot to moi.
	dung("không có chỗ nào dựng hoá đơn bán",
		not co_cum('"doctype"', ":", "SI") and not co_cum("doctype", "=", "SI"))
	dung("chỉ dựng đúng hoá đơn mua", co_cum('"doctype"', ":", "PI"))


@ca("chung tu: cua con_sot soi bang SU THAT chu khong tin cai co")
def _():
	# Cai co da_tao_chung_tu la LOI HUA. 125 to deu dang bat co do ma khong
	# co chung tu nao. Nen phai di hoi chung tu that.
	doan = MA.split("def con_sot")[1].split("\n@frappe")[0]
	dung("có hỏi chứng từ thật", "_da_co_chung_tu" in doan)
	dung("không lọc theo cái cờ", '"da_tao_chung_tu": 1' not in doan)


@ca("chung tu: dung ca hai bang chung tu khi soi cho sot")
def _():
	doan = MA.split("def _da_co_chung_tu")[1].split("\ndef ")[0]
	dung("soi cả hoá đơn mua và hoá đơn bán", "(PI, SI)" in doan)


@ca("chung tu: ba cua mo ra ngoai, cac ham dung that thi khong")
def _():
	dung("có khai trong bảng cửa ngõ", '"minvoice_chung_tu.py"' in MA_CUA)
	doan = MA_CUA.split('"minvoice_chung_tu.py"')[1][:200]
	for ten in ("chay_tu_dong", "dung_hoa_don_mua"):
		dung("%s không mở ra ngoài" % ten, ('"%s"' % ten) not in doan)


@ca("chung tu: truong dem so lan thu duoc dung lai moi lan Migrate")
def _():
	dung("có gọi dựng nhóm trường",
		"minvoice_chung_tu.TRUONG_MOI" in MA_TRUONG)


# --------------------------------- ba hang rao them ngay 26/08/2026


@ca("dau ra: danh dau BO QUA HOP LE chu khong de trong danh sach con sot")
def _():
	# De 103 to trong danh sach viec phai lam la bao dong gia moi ngay, ma
	# mot danh sach keu oan thi y het mot danh sach khong ai doc. Dung cai
	# bay da lam 22 to dau vao nam im ca thang.
	doan = MA.split("def _mot_to")[1].split("\ndef ")[0]
	dung("đầu ra đi đường ghi xong", "_ghi_xong" in doan)
	# Cat dung tu dong soi LOAI_RA toi cau return cua chinh nhanh do.
	nhanh = doan.split("LOAI_RA")[1].split("return")[0]
	dung("nhánh đầu ra KHÔNG gọi ghi hỏng", "_ghi_hong" not in nhanh)
	dung("nhánh đầu ra gọi ghi xong", "_ghi_xong" in nhanh)
	dung("có nói rõ là Fabi xuất", "Fabi" in doan)


@ca("dau ra: cua con_sot dem rieng chu khong tron vao viec phai lam")
def _():
	doan = MA.split("def con_sot")[1].split("\n@frappe")[0]
	dung("có bỏ đầu ra khỏi danh sách", "LOAI_RA" in doan)
	dung("nhưng vẫn đếm để có người nhìn", "dau_ra_fabi" in doan)


@ca("hang rao 1: dung xong phai doi chieu tong voi hoa don dien tu")
def _():
	# Sai lang le con te hon khong dung: khong dung thi con dem duoc bang
	# `con_sot`, con dung sai thi no nam trong so nhu mot con so that.
	doan = MA.split("def dung_hoa_don_mua")[1].split("\ndef ")[0]
	dung("có so tổng chứng từ với tổng hoá đơn",
		"grand_total" in doan and "tong_tien" in doan)
	dung("lệch quá ngưỡng thì ném lỗi", "NGUONG_KHOP" in doan and "throw" in doan)
	dung("đối chiếu SAU khi ghi vào hệ",
		doan.index("insert") < doan.index("NGUONG_KHOP"))


@ca("hang rao 1: hong thi huy ca luot ghi cua to do")
def _():
	doan = MA.split("def _mot_to")[1].split("\ndef ")[0]
	dung("có gọi rollback", "rollback" in doan)
	# Mot to mot commit, nen rollback khong bao gio dung toi to truoc.
	dung("mỗi tờ một lần ghi sổ riêng",
		"frappe.db.commit()" in MA.split("def _chay")[1].split("\n@frappe")[0])


@ca("hang rao 2: KHONG bo hep cua so ngay khi di dung chung tu")
def _():
	# Ban cu chi ngo 60 ngay gan nhat, to cu hon thi vinh vien khong ai dung
	# va cung khong ai dem.
	doan = MA.split("def _chay")[1].split("\n@frappe")[0]
	dung("mốc đầu là hằng số, không phải trừ lùi vài chục ngày",
		"NGAY_BAT_DAU" in doan)
	dung("không còn add_days âm trong hàm chạy", "add_days" not in doan)


@ca("hang rao 3: chan trung theo so hoa don, va KHONG tu gan vao to co san")
def _():
	doan = MA.split("def _trung_theo_so_hoa_don")[1].split("\ndef ")[0]
	dung("soi theo nhà cung cấp và số hoá đơn",
		'"supplier"' in doan and '"bill_no"' in doan)
	dung("chỉ soi tờ chưa gắn mã hoá đơn điện tử",
		'"custom_minvoice_id"' in doan)
	dung("KHÔNG ghi gì vào chứng từ của người khác",
		"set_value" not in doan and "insert" not in doan and "save" not in doan)


@ca("tang keo: khong duoc dung o trang dau khi M-Invoice quen tra totalPage")
def _():
	# Ban truoc doc `resp.get("totalPage") or 1`, tuc ho quen tra o do mot
	# lan la minh dung sau trang dau va mat sach phan con lai, ma khong co gi
	# keu len ca. Day chinh la cho de nuot hoa don nhat cua tang keo.
	doan = MA_KEO.split("def _keo(")[1]
	dung("không còn rơi thẳng về 1", '(resp.get("totalPage") or 1)' not in doan)
	dung("có soi số tờ vừa nhận để đoán còn trang sau", "len(lo) < 100" in doan)


@ca("vo ruot: dem rieng va cho nguoi nhin thay, khong de nam im")
def _():
	# Ngay 26/08/2026 co 112 vo ruot DAU VAO, cai cu nhat tu 22/07, hon mot
	# thang chua lanh. Moi cai la mot hoa don mua co the dang thieu.
	doan = MA.split("def _dem_vo_ruot")[1].split("\n@frappe")[0]
	dung("đếm riêng đầu vào và đầu ra",
		"LOAI_VAO" in doan and "LOAI_RA" in doan)
	dung("có lấy cả tờ cũ nhất để biết nó nằm im bao lâu", "cu_nhat" in doan)
	dung("con_sot có trả về số vỏ ruột",
		'"vo_ruot"' in MA.split("def con_sot")[1].split("\n@frappe")[0]
		or '"vo_ruot": _dem_vo_ruot()' in MA)


@ca("vo ruot: cua lanh chi do ruot, KHONG dung chung tu nao")
def _():
	doan = MA.split("def lanh_vo_ruot")[1].split("\n@frappe")[0]
	dung("gọi lại tầng kéo", "minvoice_dong_bo" in doan)
	dung("KHÔNG dựng chứng từ", "dung_hoa_don_mua" not in doan and "_chay" not in doan)
	dung("có đếm trước và sau để biết lành được mấy tờ",
		"truoc" in doan and "sau" in doan)


@ca("cua ngo: bon cua mo ra ngoai, deu la doc hoac chay tay")
def _():
	doan = MA_CUA.split('"minvoice_chung_tu.py"')[1][:220]
	for ten in ("chay_bu", "con_sot", "lanh_vo_ruot", "mo_lai"):
		dung("cửa %s đã khai" % ten, ('"%s"' % ten) in doan)

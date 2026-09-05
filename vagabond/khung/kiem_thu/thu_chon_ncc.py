# -*- coding: utf-8 -*-
"""Ô chọn nhà cung cấp và câu trả lời "vì sao thiếu hoá đơn" (Issue #196).

Anh Việt 05/09/2026: năm nút chọn luồng thì rối, danh sách nhà cung cấp thì
bày hết ra thành một bảng chip dài.

Bộ ca này chốt phần NGUY HIỂM nhất của lần sửa đó. Ý chị Dung "list ra mà
thiếu có nghĩa là chưa hạch toán" không đúng với cách hệ đang chạy: bảng tick
còn lọc theo 365 ngày và còn giấu tờ đang nằm trong hồ sơ khác. Nếu màn hình
tin theo câu đó rồi mời người dùng gõ tay lại một khoản mà hệ ĐÃ có tờ hoá
đơn nháp, thì tới bước giám đốc duyệt máy sinh thêm một hoá đơn mua nữa,
thành hoá đơn trùng trên sổ.
"""

import io
import os

from vagabond import chon_ncc as cn
from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(
		os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


MOC = "2026-01-01"


def _hd(name, ds=1, con_no=100.0, ngay="2026-06-01"):
	return {"name": name, "docstatus": ds, "outstanding": con_no, "posting_date": ngay}


@ca("#196 vì sao thiếu: mỗi tờ đúng một lý do")
def _vi_sao_thieu():
	f = cn.vi_sao_thieu
	dung("tờ còn nháp", f(_hd("A", ds=0), MOC) == cn.LD_NHAP)
	dung("tờ đã huỷ", f(_hd("B", ds=2), MOC) == cn.LD_HUY)
	dung("tờ đã trả xong", f(_hd("C", con_no=0), MOC) == cn.LD_DA_TRA)
	dung("tờ âm tiền cũng là đã trả xong", f(_hd("C2", con_no=-5), MOC) == cn.LD_DA_TRA)
	dung("tờ đang nằm trong hồ sơ khác",
		f(_hd("D"), MOC, {"D": "APP-2026-0007"}) == cn.LD_HO_SO_KHAC)
	dung("tờ ngoài khoảng ngày",
		f(_hd("E", ngay="2025-05-01"), MOC) == cn.LD_NGOAI_KY)
	# Câu trả lời quan trọng nhất: tờ này LẼ RA phải thấy.
	dung("tờ bình thường thì trả về None", f(_hd("F"), MOC) is None)
	dung("không có mốc ngày thì không ai bị loại vì ngày",
		f(_hd("G", ngay="2001-01-01"), "") is None)
	dung("thiếu ngày cũng không nổ", f(_hd("H", ngay=""), MOC) is None)


@ca("#196 vì sao thiếu: thứ tự xét, nháp đứng trước mọi lý do khác")
def _thu_tu_xet():
	f = cn.vi_sao_thieu
	# Một tờ nháp, ngoài kỳ, chưa trả: phải báo NHÁP, vì đó là lý do duy
	# nhất người đọc làm được gì đó với nó.
	dung("nháp thắng ngoài kỳ",
		f(_hd("A", ds=0, ngay="2001-01-01"), MOC) == cn.LD_NHAP)
	# Tờ đã trả xong mà vẫn nằm trong một hồ sơ: báo ĐÃ TRẢ, vì hồ sơ kia
	# không giữ được gì nữa.
	dung("đã trả thắng hồ sơ khác",
		f(_hd("B", con_no=0), MOC, {"B": "APP-1"}) == cn.LD_DA_TRA)
	dung("hồ sơ khác thắng ngoài kỳ",
		f(_hd("C", ngay="2001-01-01"), MOC, {"C": "APP-1"}) == cn.LD_HO_SO_KHAC)
	dung("mọi lý do đều nằm trong bảng thứ tự bày ra màn",
		set(cn.THU_TU_LY_DO) == {cn.LD_NHAP, cn.LD_HUY, cn.LD_DA_TRA,
			cn.LD_HO_SO_KHAC, cn.LD_NGOAI_KY})


@ca("#196 gom lý do: tách được tờ chọn được ra khỏi tờ bị giấu")
def _gom_ly_do():
	ds = [_hd("A"), _hd("B", ds=0), _hd("C", con_no=0),
		_hd("D", ngay="2020-01-01"), _hd("E")]
	nhom, chon = cn.gom_ly_do(ds, MOC, {"E": "APP-9"})
	dung("hai tờ chọn được", [x["name"] for x in chon] == ["A"] or len(chon) == 1)
	dung("đúng tờ A chọn được", chon[0]["name"] == "A")
	dung("một tờ nháp", [x["name"] for x in nhom[cn.LD_NHAP]] == ["B"])
	dung("một tờ đã trả", [x["name"] for x in nhom[cn.LD_DA_TRA]] == ["C"])
	dung("một tờ ngoài kỳ", [x["name"] for x in nhom[cn.LD_NGOAI_KY]] == ["D"])
	dung("một tờ ở hồ sơ khác", [x["name"] for x in nhom[cn.LD_HO_SO_KHAC]] == ["E"])
	dung("bảng rỗng không nổ", cn.gom_ly_do([], MOC) == ({}, []))


@ca("#196 chip nhà cung cấp: tiền nháp KHÔNG cộng vào nợ đã ghi sổ")
def _chip_khong_lan_tien():
	# Codex chốt trên #196: cộng lẫn là sai số. Nhà này nợ 900 đã ghi sổ,
	# trong đó lập được 500, và còn 3 tờ nháp trị giá 70.
	c = cn.chip_ncc({"lap_duoc_so": 2, "lap_duoc_tien": 500, "qua_han_tien": 200,
		"no_ghi_so": 900, "so_hd_no": 4, "nhap_so": 3, "nhap_tien": 70})
	ma = [x["ma"] for x in c]
	dung("đủ bốn chip", ma == ["lap_duoc", "qua_han", "khong_lap_duoc", "nhap"])
	tien = dict((x["ma"], x["tien"]) for x in c)
	dung("chip lập được mang đúng 500", tien["lap_duoc"] == 500)
	dung("chip không lập được mang đúng phần chênh 400",
		tien["khong_lap_duoc"] == 400)
	dung("chip nháp mang tiền riêng của nó", tien["nhap"] == 70)
	dung("tiền nháp không cộng vào chip nào khác",
		tien["lap_duoc"] + tien["khong_lap_duoc"] == 900)


@ca("#196 chip nhà cung cấp: các ca biên")
def _chip_ca_bien():
	f = cn.chip_ncc
	dung("nhà sạch trơn thì không có chip nào", f({}) == [])
	dung("nợ bằng đúng phần lập được thì không có chip chênh",
		[x["ma"] for x in f({"lap_duoc_so": 1, "lap_duoc_tien": 500, "no_ghi_so": 500})]
		== ["lap_duoc"])
	# Đây chính là ca Codex cảnh báo: có chip nợ mà mở ra bảng trống.
	dung("nợ mà không lập được tờ nào thì chỉ còn chip giải thích",
		[x["ma"] for x in f({"lap_duoc_so": 0, "lap_duoc_tien": 0, "no_ghi_so": 800})]
		== ["khong_lap_duoc"])
	dung("nhà chỉ có hoá đơn nháp vẫn hiện được",
		[x["ma"] for x in f({"nhap_so": 5, "nhap_tien": 90})] == ["nhap"])
	dung("lệch nửa đồng do làm tròn thì bỏ qua",
		[x["ma"] for x in f({"lap_duoc_so": 1, "lap_duoc_tien": 500.2,
			"no_ghi_so": 500.4})] == ["lap_duoc"])
	dung("không quá hạn thì không có chip cảnh báo",
		"qua_han" not in [x["ma"] for x in f({"lap_duoc_so": 1, "lap_duoc_tien": 5,
			"no_ghi_so": 5, "qua_han_tien": 0})])


@ca("#196 thứ tự bày nhà cung cấp và ô tìm")
def _xep_va_loc():
	ds = [
		{"ncc": "N3", "ten": "Chỉ có nháp", "lap_duoc_so": 0, "no_ghi_so": 0, "nhap_so": 4},
		{"ncc": "N1", "ten": "Quá hạn nhiều", "lap_duoc_so": 2, "lap_duoc_tien": 300,
			"qua_han_tien": 300, "no_ghi_so": 300},
		{"ncc": "N2", "ten": "Nợ mà chưa lập được", "lap_duoc_so": 0, "no_ghi_so": 700},
		{"ncc": "N4", "ten": "Lập được không quá hạn", "lap_duoc_so": 1,
			"lap_duoc_tien": 900, "qua_han_tien": 0, "no_ghi_so": 900},
	]
	ra = [x["ncc"] for x in cn.xep_ncc(ds)]
	dung("quá hạn lên đầu, rồi tới lập được, rồi nợ suông, cuối là chỉ nháp",
		ra == ["N1", "N4", "N2", "N3"])
	dung("bảng rỗng không nổ", cn.xep_ncc([]) == [])
	# "Quá hạn nhiều" và "Lập được không quá hạn" đều chứa chữ đó, nên khớp
	# hai nhà mới đúng. Lọc chỉ thu hẹp danh sách, không tự đoán ý người gõ.
	dung("lọc khớp tên không phân biệt hoa thường",
		sorted(x["ncc"] for x in cn.loc_ncc(ds, "QUÁ HẠN")) == ["N1", "N4"])
	dung("gõ đủ chữ thì ra đúng một nhà",
		[x["ncc"] for x in cn.loc_ncc(ds, "quá hạn nhiều")] == ["N1"])
	dung("lọc khớp cả mã", [x["ncc"] for x in cn.loc_ncc(ds, "n3")] == ["N3"])
	dung("từ khoá rỗng thì giữ nguyên", len(cn.loc_ncc(ds, "")) == 4)


@ca("#196 phép thuần không chạm Frappe và không sửa dữ liệu")
def _phep_thuan_sach():
	s = _py("chon_ncc.py")
	# Dò "import frappe" và "frappe." chứ không dò chữ "frappe" trần: chính
	# lời chú thích của tệp có nhắc tới tên đó để nói rằng nó KHÔNG import.
	for xau in ("import frappe", "frappe.", "set_value", "db.sql", "save(",
			"delete", "submit"):
		la("chon_ncc.py không có %s" % xau, xau in s, False)


@ca("#196 màn hình đi qua đúng các cửa mới")
def _man_hinh_noi_dung_cua():
	j = _js("19-ho-so-tt.js")
	dung("ô chọn lấy dữ liệu từ cửa mới",
		"'vagabond.ho_so_tt.ds_ncc_chon'" in j)
	dung("nút vì sao thiếu gọi đúng cửa",
		"'vagabond.ho_so_tt.ly_do_thieu_hd'" in j)
	dung("không còn bày hết nhà cung cấp thành bảng chip",
		"posChipNut('data-hsn=\"' + h(x.ncc)" not in j)
	dung("dùng tấm trượt của nền, không dùng thẻ select",
		"sheet('Chọn nhà cung cấp'" in j)
	# Cửa cấm thẻ <select> đã có sẵn ở `thu_nguyen_tac_man_hinh`, không lặp
	# lại ở đây: dò chữ "<select" trần thì chính lời chú thích nhắc tới nó
	# cũng bị tính là vi phạm.
	dung("có ô tìm hoá đơn ngay lúc lập", "vgbOTim('hsHdTim'" in j)
	dung("ô tìm hoá đơn lọc trên DOM nên không mất tick",
		"vgbNoiOTim(b, 'hsHdTim', '[data-hsh]')" in j)
	dung("chọn hết nói rõ phạm vi", "Chọn hết đang hiện" in j)
	dung("chọn hết chỉ lấy tập đang hiện", "dangHien().forEach(ghiChon)" in j)


@ca("#196 màn Vì sao thiếu phải dặn KHÔNG gõ lại tờ còn nháp")
def _dan_khong_go_lai():
	j = _js("19-ho-so-tt.js")
	i = j.index("async function hsViSaoThieu(")
	than = j[i:j.index("\nasync function scrHoSoTTTao(", i)]
	dung("có câu dặn đừng gõ tay lại", "ĐỪNG gõ tay lại" in than)
	dung("nói rõ hậu quả là hoá đơn trùng", "hoá đơn trùng" in than)
	dung("bày đủ năm nhãn lý do",
		all(k in j for k in ("Còn nháp, chưa ghi sổ", "Đang nằm trong hồ sơ khác",
			"Ngoài khoảng ngày đang lọc", "Đã trả xong", "Đã huỷ")))
	# Màn này chỉ ĐỌC. Không được có đường nào ghi xuống dữ liệu cũ.
	for xau in ("tao(", "ghi_so", "submit", "xoa"):
		la("màn vì sao thiếu không có %s" % xau, xau in than, False)


@ca("#196 cửa máy chủ chỉ đọc, không sinh và không sửa hoá đơn cũ")
def _cua_may_chu_chi_doc():
	s = _py("ho_so_tt.py")
	for ten in ("def ds_ncc_chon(", "def ly_do_thieu_hd("):
		i = s.index(ten)
		than = s[i:s.index("\n@frappe.whitelist()", i) if "\n@frappe.whitelist()" in s[i:] else i + 4000]
		for xau in ("set_value", ".save(", ".insert(", ".submit(", "delete"):
			la("%s không có %s" % (ten[4:-1], xau), xau in than, False)
		dung("%s có kiểm quyền" % ten[4:-1], "_kiem(VAI_LAP" in than)
	dung("cửa tìm hoá đơn lúc lập nhận từ khoá",
		"def hoa_don_cho_tra(ncc=None, so_ngay=180, chi_qua_han=0, tu_khoa=\"\")" in s)
	dung("từ khoá khớp cả số hoá đơn của nhà cung cấp",
		'(r.bill_no or "")' in s)

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
	i = j.index("function hsViSaoThieu(")
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


# ---------------------------------------------------------------- vòng hai
#
# Sáu điểm Codex nêu trên PR #198 ngày 05/09/2026, cả sáu đều đúng. Mỗi cái
# một ca chốt lại để không tái phát.


@ca("#198 ô tìm hoá đơn phải sống sót qua mỗi lần tick")
def _o_tim_song_sot():
	# Đây là cái nặng nhất: mỗi lần tick một tờ là `go(scrHoSoTTTao, true)`
	# dựng lại cả màn, ô tìm về rỗng và bảng bày lại đầy đủ. Lúc đó nút
	# "Chọn hết đang hiện" vơ trọn danh sách, ngược hẳn cái tên nó mang.
	j = _js("19-ho-so-tt.js")
	dung("từ khoá giữ ngoài DOM", "\nvar hsHdTu = '';" in j)
	dung("dựng lại màn thì trả giá trị về ô", "oHd.value = hsHdTu;" in j)
	dung("gõ tới đâu ghi lại tới đó",
		"oHd.addEventListener('input', function () { hsHdTu = oHd.value; });" in j)
	# `vgbNoiOTim` chạy `chay()` một lần ngay lúc nối, nên phải gán giá trị
	# TRƯỚC nó thì bộ lọc mới sống lại. Gán sau là bày đủ bảng rồi mới điền
	# chữ vào ô, đúng cái lỗi đang vá.
	a = j.index("oHd.value = hsHdTu;")
	b = j.index("vgbNoiOTim(b, 'hsHdTim'")
	dung("gán giá trị đứng trước lúc nối bộ lọc", a < b)
	# Lập hồ sơ mới thì phải sạch, không mang từ khoá của hồ sơ trước sang.
	k = j.index("async function hsChonLoaiMoi(")
	dung("hồ sơ mới thì xoá từ khoá", "hsHdTu = '';" in j[k:k + 3000])


@ca("#198 tìm nhà cung cấp không dấu vẫn phải ra")
def _tim_khong_dau():
	# `sheet()` của 00-nen.js chỉ hạ chữ thường chứ không bỏ dấu, còn ô tìm
	# cũ có `mvKhongDau` cả hai phía. Đổi sang tấm trượt mà không bù lại là
	# gõ "dien luc" không còn ra "ĐIỆN LỰC".
	j = _js("19-ho-so-tt.js")
	dung("nhét bản không dấu vào trường tìm",
		"tim: mvKhongDau(x.ten) + ' ' + x.ncc" in j)


@ca("#198 màn Vì sao thiếu tra được TỪNG tờ, không cắt ở tờ thứ 7")
def _vi_sao_thieu_tra_duoc_tung_to():
	j = _js("19-ho-so-tt.js")
	i = j.index("async function scrViSaoThieu(")
	than = j[i:j.index("\nasync function scrHoSoTTTao(", i)]
	la("không còn cắt sáu tờ đầu", ".slice(0, 6)" in than, False)
	dung("có ô tìm riêng cho bảng tờ", "vgbOTim('hsVsTim'" in than)
	dung("ô tìm nối vào từng dòng", "vgbNoiOTim(b, 'hsVsTim', '[data-vshd]')" in than)
	dung("giữ từ khoá qua mỗi lần dựng lại", "oV.value = hsVsTu;" in than)
	# Gộp mọi nhóm thành một bảng phẳng: để thành từng khối có tiêu đề thì
	# lọc xong tiêu đề ở lại lơ lửng còn dòng thì biến mất.
	dung("gộp các nhóm thành một bảng phẳng", "dong.push({ g: g, x: x })" in than)
	s = _py("ho_so_tt.py")
	la("máy chủ không còn cắt 40 tờ", '"hoa_don": to[:40]' in s, False)
	dung("máy chủ trả tới 500 tờ và nói rõ khi bị cắt",
		'"hoa_don": to[:500]' in s and '"bi_cat"' in s)
	dung("màn hình nói ra khi bị cắt", "bi_cat" in than)


@ca("#198 ô chọn phải tìm được MỌI nhà cung cấp, kể cả nhà chỉ có HĐ đã trả")
def _tim_duoc_moi_nha():
	s = _py("ho_so_tt.py")
	i = s.index("def ds_ncc_chon(")
	than = s[i:s.index("\n@frappe.whitelist()", i)]
	dung("nạp cả danh mục nhà cung cấp", '"Supplier",' in than)
	dung("bỏ nhà đã tắt", '"disabled": 0' in than)
	# Nhà không nợ, không nháp thì các con số bằng 0 và phải nằm cuối bảng.
	f = cn.xep_ncc
	ds = [
		{"ncc": "A", "ten": "Không còn gì"},
		{"ncc": "B", "ten": "Chỉ có nháp", "nhap_so": 2},
		{"ncc": "C", "ten": "Nợ mà chưa lập được", "no_ghi_so": 5},
		{"ncc": "D", "ten": "Lập được", "lap_duoc_so": 1, "lap_duoc_tien": 9, "no_ghi_so": 9},
	]
	dung("bốn nhóm xếp đúng thứ tự", [x["ncc"] for x in f(ds)] == ["D", "C", "B", "A"])
	dung("nhà trắng trơn không có chip nào", cn.chip_ncc(ds[0]) == [])


@ca("#198 tờ ĐÃ HUỶ phải vào được phép phân loại")
def _to_da_huy_vao_duoc():
	# Lọc `docstatus < 2` là vứt tờ đã huỷ đi TRƯỚC khi phép thuần kịp phân
	# loại, nên nhãn "Đã huỷ" không bao giờ hiện, mà màn hình còn có thể nói
	# rằng mọi tờ đều đang thấy.
	s = _py("ho_so_tt.py")
	i = s.index("def ly_do_thieu_hd(")
	than = s[i:s.index("\ndef _hd_ho_so_giu(", i)]
	la("không còn lọc docstatus dưới 2", '"docstatus": ["<", 2]' in than, False)
	dung("lấy hết mọi tờ của nhà đó", '{"supplier": ncc}' in than)
	# Và phép thuần vẫn nhận ra tờ đã huỷ.
	dung("phép thuần trả về đúng lý do huỷ",
		cn.vi_sao_thieu({"name": "X", "docstatus": 2, "outstanding": 100,
			"posting_date": "2026-06-01"}, MOC) == cn.LD_HUY)


@ca("#198 câu báo lỗi phải nói việc làm tiếp, đúng QT-24")
def _bao_loi_noi_viec_lam_tiep():
	j = _js("19-ho-so-tt.js")
	i = j.index("async function scrViSaoThieu(")
	than = j[i:j.index("\nasync function scrHoSoTTTao(", i)]
	dung("nhắc kiểm mạng và bấm lại", "Kiểm lại mạng rồi bấm nút" in than)
	dung("nói rõ việc ở màn trước không bị kẹt theo",
		"vẫn tick và lập bình thường" in than)
	# Ô chọn nhà cung cấp trống cũng phải nói làm gì tiếp, không được chỉ
	# thông báo là trống rồi bỏ mặc người dùng đứng đó.
	k = j.index("function hsMoChonNcc(")
	than2 = j[k:j.index("\n/* ==================== XEM VÌ SAO THIẾU", k)]
	dung("ô chọn trống cũng chỉ việc làm tiếp",
		"mở lại màn này một lần" in than2 and "nhờ chị Dung" in than2)


@ca("#198 vòng hai: tra được tờ nằm NGOÀI 500 tờ máy chủ bày ra")
def _tra_duoc_to_ngoai_gioi_han():
	# Codex nêu vòng hai: cắt 500 tờ mỗi NHÓM rồi để màn hình lọc trên DOM
	# thì tờ thứ 501 không bao giờ tra ra được, dù dữ liệu có thật.
	s = _py("ho_so_tt.py")
	i = s.index("def ly_do_thieu_hd(")
	than = s[i:s.index("\ndef _hd_ho_so_giu(", i)]
	dung("cửa nhận từ khoá",
		'def ly_do_thieu_hd(ncc=None, so_ngay=365, tu_khoa="")' in s)
	dung("khớp cả mã hoá đơn lẫn số hoá đơn của nhà cung cấp",
		'(x["name"] or "") + " " + (x["so_hd_ncc"] or "")' in than)
	# Điều quan trọng nhất: lọc phải chạy TRƯỚC lúc cắt. Lọc sau thì tờ 501
	# đã bị vứt đi rồi, gõ đúng số của nó cũng không ra.
	a = than.index('if q:')
	b = than.index('to[:500]')
	dung("lọc theo từ khoá đứng TRƯỚC lúc cắt 500 tờ", a < b)
	dung("ghi chú kỹ thuật nói đúng là 500 tờ MỖI NHÓM", "500 to MOI NHOM" in than)

	j = _js("19-ho-so-tt.js")
	k = j.index("async function scrViSaoThieu(")
	thanJs = j[k:j.index("\nasync function scrHoSoTTTao(", k)]
	dung("màn hình gửi từ khoá lên máy chủ", "tu_khoa: hsVsTu" in thanJs)
	dung("bấm Enter là hỏi lại máy chủ chứ không chỉ lọc DOM",
		"hsVsDl = null; go(scrViSaoThieu, true);" in thanJs)
	dung("dòng nhắc nói rõ cách tra tờ ngoài khoảng", "bấm Enter" in thanJs)
	# Gõ hụt một lần không được làm người dùng kẹt trong màn không còn ô tìm.
	dung("gõ hụt vẫn còn ô tìm để tìm lại", "Xoá bớt chữ rồi bấm Enter tìm lại" in thanJs)


@ca("#198 vòng hai: rebase lên main giữ nguyên phần của phiên khác")
def _rebase_giu_ca_hai_ben():
	# main đã nhận v428 của phiên khác trong lúc PR này còn mở. Ba chỗ đụng
	# nhau đều là kiểu CẢ HAI BÊN CÙNG THÊM, nên luật là giữ cả hai chứ
	# không chọn bên nào (AGENTS.md điều 8, ngoại lệ).
	goc = os.path.dirname(GOI)
	patches = io.open(os.path.join(GOI, "patches.txt"), encoding="utf-8").read()
	dung("dòng v428 của phiên khác còn nguyên", "dong_bo_cau_truc #v428" in patches)
	dung("dòng v429 của mình cũng có", "dong_bo_cau_truc #v429" in patches)
	dung("v429 đứng sau v428", patches.index("#v428") < patches.index("#v429"))
	chay = io.open(os.path.join(GOI, "khung", "kiem_thu", "chay.py"),
		encoding="utf-8").read()
	dung("bộ ca của phiên khác còn được nạp", "thu_dat_banh" in chay)
	dung("bộ ca của mình cũng còn được nạp", "thu_chon_ncc" in chay)
	# Số phiên bản chỉ được TĂNG.
	js = _js("12-van-don.js")
	dung("APPVER là 429, không lùi về 428", "var APPVER = '429';" in js)
	assert goc

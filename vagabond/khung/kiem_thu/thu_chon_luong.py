# -*- coding: utf-8 -*-
"""Hai câu hỏi thay cho năm nút ở màn lập hồ sơ (Issue #196 phần A).

Anh Việt mở issue #196: *"Chị Dung và anh đều cảm thấy 5 nút của chỗ tạo APP
là quá rối. Anh muốn làm gọn lại"*.

Năm nút cũ bắt người ta đối chiếu ba tiêu chí cùng một lúc: tiền đi cho ai,
hoá đơn đã vào hệ chưa, có đi qua Purchasing không. v432 tách thành hai nhịp,
mỗi nhịp một tiêu chí, và KHÔNG bỏ luồng nào.

Bộ ca này canh đúng những chỗ mà một lần sửa giao diện dễ làm hỏng lặng lẽ:

  1. Một luồng mất đường vào. Năm mã luồng phải còn đủ và mỗi mã đúng một
     lần. Người dùng sẽ không báo "thiếu nút", họ chỉ đi nhầm đường khác.
  2. Nhánh gắn sai bảng. Trả thẳng cho nhà cung cấp mà lại bày hai thẻ hoàn
     ứng thì tiền chạy về nhầm người.
  3. Dòng dọn trạng thái bị rơi. Mỗi luồng dọn một bộ biến khác nhau; rơi
     một dòng là hồ sơ mới mang theo phần của hồ sơ cũ.
  4. Thôi ở câu 2 mà văng hẳn ra ngoài. Bắt bấm dấu cộng lại từ đầu chỉ vì
     lỡ chọn nhầm nhánh là bước lùi.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MA_LUONG = ("ncc", "tt", "tkct", "hu_hd", "hu_khd")


def _js(ten):
	return io.open(
		os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


def _doan(src, dau, cuoi):
	i = src.index(dau)
	return src[i:src.index(cuoi, i + len(dau))]


def _than_ham():
	src = _js("19-ho-so-tt.js")
	return _doan(src, "async function hsChonLoaiMoi() {", "\nfunction huTong(")


@ca("#196A hỏi làm hai nhịp, mỗi nhịp một tiêu chí")
def _hai_nhip():
	than = _than_ham()
	dung("câu 1 đánh số 1/2", "'Lập hồ sơ thanh toán · 1/2'" in than)
	dung("câu 2 đánh số 2/2", "'Lập hồ sơ thanh toán · 2/2'" in than)
	dung("câu 1 hỏi tiền đi cho ai", "'Tiền của tiệm lần này chuyển cho ai?'" in than)
	# Câu 2 dùng chung một chỗ khai cho cả hai nhánh, để hai nhánh không bao
	# giờ lệch lời nhau.
	src = _js("19-ho-so-tt.js")
	dung("câu 2 khai một chỗ dùng chung",
		"var HS_CAU_HOA_DON = 'Hoá đơn mua đã nằm trong hệ chưa?';" in src)
	dung("câu 2 lấy mô tả từ chỗ dùng chung", "HS_MO_TA_HOA_DON," in than)


@ca("#196A câu 2 nói thẳng tiêu chí thật, không bắt người ta suy ra")
def _cau_hai_noi_thang():
	"""Lỗi hiểu nhầm này có thật và đã ghi lại từ trước v432.

	"Có hoá đơn" ở màn này nghĩa là hoá đơn ĐÃ NẰM TRONG HỆ thành một hoá
	đơn mua còn nợ, chứ không phải cầm tờ hoá đơn giấy trong tay. Cầm tờ
	hoá đơn VAT thật mà kế toán chưa nhập thì vẫn phải đi đường "chưa vào
	hệ", vì chính đường đó mới sinh hoá đơn mua ra. Đi nhầm đường kia thì
	bảng tick trống trơn và người ta bỏ cuộc.
	"""
	src = _js("19-ho-so-tt.js")
	dung("hỏi đúng chữ đã nằm trong hệ", "Hoá đơn mua đã nằm trong hệ chưa?" in src)
	dung("nói rõ là hoá đơn kế toán đã nhập vào hệ",
		"Hỏi về tờ hoá đơn ĐÃ ĐƯỢC KẾ TOÁN NHẬP VÀO HỆ thành một hoá đơn mua còn nợ." in src)
	dung("nói thẳng cầm hoá đơn giấy vẫn là chưa có",
		'Cầm tờ hoá đơn giấy trong tay mà kế toán chưa nhập thì vẫn chọn "chưa có".' in src)


@ca("#196A đủ năm luồng, mỗi luồng đúng một đường vào")
def _du_nam_luong():
	src = _js("19-ho-so-tt.js")
	for ma in MA_LUONG:
		dung("luồng %s có đúng một thẻ" % ma, src.count("k: '%s'" % ma) == 1)
	# Ma cua cau 1 phai khac han nam ma luong. Dung trung chu `ncc` cho ca
	# nhanh lan luong thi doc code khong biet dang noi toi cai nao, ma ca
	# kiem do chuoi thi dem nham.
	dung("mã nhánh không trùng mã luồng",
		"k: 'ben_ban'" in src and "k: 'nguoi_ung'" in src)
	for ma in ("ben_ban", "nguoi_ung"):
		la("mã nhánh %s không phải mã luồng" % ma, ma in MA_LUONG, False)


@ca("#196A mỗi nhánh gắn đúng bảng của nó")
def _nhanh_gan_dung_bang():
	src = _js("19-ho-so-tt.js")
	tra = _doan(src, "var HS_LUONG_TRA_NCC = [", "\nvar HS_LUONG_HOAN_UNG")
	hoan = _doan(src, "var HS_LUONG_HOAN_UNG = [", "\nvar HS_CAU_HOA_DON")
	for ma in ("ncc", "tt", "tkct"):
		dung("luồng %s nằm ở nhánh trả nhà cung cấp" % ma, "k: '%s'" % ma in tra)
		la("luồng %s không lẫn sang nhánh hoàn ứng" % ma, "k: '%s'" % ma in hoan, False)
	for ma in ("hu_hd", "hu_khd"):
		dung("luồng %s nằm ở nhánh hoàn ứng" % ma, "k: '%s'" % ma in hoan)
		la("luồng %s không lẫn sang nhánh trả nhà cung cấp" % ma, "k: '%s'" % ma in tra, False)
	# Chon nhanh nao thi bay bang nao: sai mot chu o dong nay la tien chay
	# ve nham nguoi.
	dung("chọn người ứng thì bày bảng hoàn ứng",
		"ai === 'nguoi_ung' ? HS_LUONG_HOAN_UNG : HS_LUONG_TRA_NCC" in src)


@ca("#196A thứ tự khai luồng giữ nguyên như thời năm nút")
def _thu_tu_giu_nguyen():
	# Thu tu nay da co ca kiem rieng ben thu_tra_truoc.py tu luc them luong
	# tra truoc. Chot lai o day de doi bang khong lam xao tron ma khong ai
	# hay: nguoi dung da quen vi tri.
	src = _js("19-ho-so-tt.js")
	vt = [src.index("k: '%s'" % ma) for ma in MA_LUONG]
	dung("khai theo đúng thứ tự ncc, tt, tkct, hu_hd, hu_khd", vt == sorted(vt))


@ca("#196A thôi ở câu 2 thì quay lại câu 1, không văng ra ngoài")
def _thoi_o_cau_hai_quay_lai():
	than = _than_ham()
	dung("có vòng lặp bọc hai câu", "for (;;) {" in than)
	dung("thôi ở câu 1 mới thoát hẳn", "if (!ai) return;" in than)
	dung("thôi ở câu 2 thì quay lại", "if (!c) continue;" in than)
	# `return` o cau 2 la loi cu the phai chan: no dua nguoi ta ve man danh
	# sach, bat bam dau cong lai tu dau.
	la("câu 2 không dùng return để thoát", "if (!c) return;" in than, False)


@ca("#196A dọn trạng thái của từng luồng còn nguyên")
def _don_trang_thai():
	"""Mỗi luồng dọn một bộ biến khác nhau, rơi một dòng là hồ sơ mới mang
	theo phần của hồ sơ cũ. Chốt từng dòng chứ không chốt chung."""
	than = _than_ham()
	dung("trả trước gọi ttReset",
		"if (c === 'tt') { ttReset(); return go(scrTraTruocTao); }" in than)
	dung("chi từ TK công ty dọn đủ bộ của nó",
		"if (c === 'tkct') { huDong = []; huGhiChu = ''; huTkChi = ''; "
		"huCpThue = ''; huChonHd = {}; huSuaO = -1; return go(scrChiCongTyTao); }" in than)
	dung("hoàn ứng không hoá đơn dọn đủ bộ của nó",
		"if (c === 'hu_khd') { huDong = []; huGhiChu = ''; huTamUng = 0; "
		"huSuaO = -1; return go(scrHoanUngTao); }" in than)
	dung("hai luồng bảng tick xoá từ khoá tìm hoá đơn", "hsHdTu = '';" in than)
	dung("hoàn ứng có hoá đơn đặt đúng loại", "hsTaoLoai = 'Hoan ung HD';" in than)
	dung("công nợ nhà cung cấp đặt đúng loại", "hsTaoLoai = 'NCC';" in than)


@ca("#196A xoá hsTaoChon tới đâu thì xoá hsPhieuCua tới đó")
def _xoa_phieu_cua_theo_cap():
	"""Lỗi có thật trước v432, sửa luôn trong đợt này.

	`hsPhieuCua` giữ phiếu thanh toán nội bộ đã nối vào từng hoá đơn. Ba
	chỗ trong tệp xoá `hsTaoChon` đều xoá kèm `hsPhieuCua`, riêng chỗ lập
	hồ sơ mới thì quên. Hậu quả: nối phiếu vào một hoá đơn, bỏ giữa chừng
	không lưu, lập lại rồi tick trúng đúng hoá đơn đó thì phiếu cũ lặng lẽ
	dính lại vào hồ sơ mới. Không màn nào báo, chỉ lộ khi kế toán duyệt.

	Chốt bằng bất biến chứ không chốt một chỗ: HỄ có dòng gán `hsTaoChon =
	{}` thì trong cùng dòng đó phải có `hsPhieuCua = {}`.
	"""
	src = _js("19-ho-so-tt.js")
	thieu = []
	for i, dong in enumerate(src.split("\n"), 1):
		if "hsTaoChon = {}" not in dong or "hsPhieuCua = {}" in dong:
			continue
		# Dong KHAI BIEN thi khong phai cho don dep. `hsPhieuCua` khai rieng
		# o dong cua no, chot ngay ben duoi.
		if dong.lstrip().startswith("var hsTaoNcc"):
			continue
		thieu.append("%d: %s" % (i, dong.strip()[:70]))
	la("mọi chỗ xoá hsTaoChon đều xoá kèm hsPhieuCua", thieu, [])
	dung("hsPhieuCua có khai trị đầu", "var hsPhieuCua = {};" in src)
	dung("có ít nhất ba chỗ để bất biến này không rỗng",
		src.count("hsPhieuCua = {}") >= 3)


@ca("#196A hai câu hỏi vẫn là chip bấm, không phải thẻ select")
def _khong_dung_select():
	# AGENTS.md mục 2b: man nay khong duoc dung <select>. hoiChon ve chip
	# bam, doi sang select la vua trai quy uoc vua kho bam tren dien thoai.
	than = _than_ham()
	la("không có thẻ select", "<select" in than, False)
	dung("vẫn đi qua hoiChon", than.count("await hoiChon(") == 2)


@ca("#196A patches.txt có dòng đợt này và giữ nguyên dòng của phiên khác")
def _dang_ky():
	dong = [d.strip() for d in
		io.open(os.path.join(GOI, "patches.txt"), encoding="utf-8").read().splitlines()]
	dung("có dòng v432", "vagabond.patches.dong_bo_cau_truc #v432" in dong)
	# Hai dong nay cua hai phien khac, dot nay khong duoc lam mat.
	dung("giữ nguyên dòng v429", "vagabond.patches.dong_bo_cau_truc #v429" in dong)
	dung("giữ nguyên dòng v431", "vagabond.patches.dong_bo_cau_truc #v431" in dong)

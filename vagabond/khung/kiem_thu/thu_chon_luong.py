# -*- coding: utf-8 -*-
"""Hai câu hỏi thay cho năm nút ở màn lập hồ sơ (Issue #196 phần A).

Anh Việt mở issue #196: *"Chị Dung và anh đều cảm thấy 5 nút của chỗ tạo APP
là quá rối. Anh muốn làm gọn lại"*.

Năm nút cũ bắt người ta đối chiếu ba tiêu chí cùng một lúc: tiền đi cho ai,
hoá đơn đã vào hệ chưa, có đi qua Purchasing không. v433 tách thành hai nhịp,
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


@ca("#196A hỏi theo nhịp, mỗi nhịp một tiêu chí")
def _hoi_theo_nhip():
	src = _js("19-ho-so-tt.js")
	than = _than_ham()
	dung("câu 1 hỏi đường tiền đi",
		"var HS_CAU_DUONG_TIEN = 'Khoản chi này đi theo đường nào?';" in src)
	dung("câu 2 khai một chỗ dùng chung cho cả hai nhánh",
		"var HS_CAU_HOA_DON = 'Hoá đơn mua đã nằm trong hệ chưa?';" in src)
	dung("câu 2 đánh dấu là bước 2", "'Lập hồ sơ thanh toán · bước 2'" in src)
	dung("câu 2 đi qua đúng một cửa", than.count("hsHoiHoaDon(") == 1)


@ca("#196A câu hỏi phải được VẼ RA màn hình, không phải chỉ khai biến")
def _cau_hoi_duoc_ve_ra():
	"""Codex nêu trên PR #203, và nêu đúng.

	Bản đầu khai `HS_CAU_HOA_DON` rồi truyền cho `hoiChon` mỗi tiêu đề
	chung và phần mô tả, nên câu hỏi thật KHÔNG BAO GIỜ hiện lên. Người
	dùng thấy "Lập hồ sơ thanh toán · 2/2" rồi tới một đoạn giải thích,
	không thấy câu hỏi mà hai lựa chọn bên dưới đang trả lời.

	Ca kiểm cũ của phiên này chốt bằng "chuỗi có mặt trong tệp" nên bỏ lọt
	sạch: khai một biến không ai dùng vẫn qua. Đây đúng kiểu lỗi mà vòng
	#200 đã dính một lần với `vgbOTim`. Nay chốt bằng CHỖ DÙNG: câu hỏi
	phải nằm trong chính lời gọi `hoiChon`, và biến phải được nhắc tới
	nhiều hơn một lần (một lần khai, ít nhất một lần dùng).
	"""
	src = _js("19-ho-so-tt.js")
	goi = _doan(src, "function hsHoiHoaDon(", "\nasync function hsChonLoaiMoi(")
	dung("câu 2 nằm trong chính lời gọi hoiChon", "HS_CAU_HOA_DON" in goi)
	dung("câu 2 in đậm rồi mới tới lời giải thích",
		"'<b>' + HS_CAU_HOA_DON + '</b><br>' + HS_MO_TA_HOA_DON" in goi)
	than = _than_ham()
	dung("câu 1 cũng được vẽ ra chứ không chỉ khai",
		"'<b>' + HS_CAU_DUONG_TIEN + '</b><br>" in than)
	# Khai ma khong dung thi so lan nhac chi bang 1.
	for ten in ("HS_CAU_HOA_DON", "HS_CAU_DUONG_TIEN"):
		dung("%s có được dùng chứ không chỉ khai" % ten, src.count(ten) >= 2)


@ca("#196A câu 2 nói thẳng tiêu chí thật, không bắt người ta suy ra")
def _cau_hai_noi_thang():
	"""Lỗi hiểu nhầm này có thật và đã ghi lại từ trước v433.

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
	# Ma cua cau 1 phai khac han ma luong, tru `tkct` la vao thang nen dung
	# chinh ma luong cua no. Dung trung chu `ncc` cho ca nhanh lan luong thi
	# doc code khong biet dang noi toi cai nao, ma ca kiem do chuoi thi dem
	# nham.
	dung("câu 1 có đủ ba lựa chọn",
		"k: 'cong_no'" in src and "k: 'tkct'" in src and "k: 'nguoi_ung'" in src)
	for ma in ("cong_no", "nguoi_ung"):
		la("mã nhánh %s không trùng mã luồng nào" % ma, ma in MA_LUONG, False)


@ca("#196A mỗi nhánh gắn đúng bảng của nó")
def _nhanh_gan_dung_bang():
	src = _js("19-ho-so-tt.js")
	cn = _doan(src, "var HS_LUONG_CONG_NO = [", "\nvar HS_LUONG_HOAN_UNG")
	hoan = _doan(src, "var HS_LUONG_HOAN_UNG = [", "\nvar HS_CAU_HOA_DON")
	for ma in ("ncc", "tt"):
		dung("luồng %s nằm ở nhánh công nợ" % ma, "k: '%s'" % ma in cn)
		la("luồng %s không lẫn sang nhánh hoàn ứng" % ma, "k: '%s'" % ma in hoan, False)
	for ma in ("hu_hd", "hu_khd"):
		dung("luồng %s nằm ở nhánh hoàn ứng" % ma, "k: '%s'" % ma in hoan)
		la("luồng %s không lẫn sang nhánh công nợ" % ma, "k: '%s'" % ma in cn, False)
	# Chon nhanh nao thi bay bang nao: sai mot chu o dong nay la tien chay
	# ve nham nguoi.
	dung("chọn người ứng thì bày bảng hoàn ứng",
		"duong === 'nguoi_ung' ? HS_LUONG_HOAN_UNG : HS_LUONG_CONG_NO" in src)


@ca("#196A chi từ TK công ty vẫn vào được khi hoá đơn ĐÃ nằm trong hệ")
def _tkct_khong_bi_chan_boi_cau_hoa_don():
	"""Codex nêu trên PR #203, và nêu đúng. Đây là lỗi nặng nhất của vòng này.

	Bản đầu xếp `tkct` thành một thẻ của câu 2 với nhãn "Không có hoá đơn
	mua nào". Nhãn đó sai: `scrChiCongTyTao` có HAI chế độ theo ô "Loại chi
	phí thuế" - chi phí hợp lệ thì nó gọi `hoa_don_cho_tra` rồi cho TICK
	hoá đơn đang nợ, không hoá đơn thì gõ tay. Người có hoá đơn trong hệ mà
	phải chi từ tài khoản khác MB, trả lời THẬT ("đã có") thì bị đẩy sang
	`ncc` (tiền ra từ MB); muốn tới đúng chỗ thì phải trả lời dối. Bắt
	người ta nói dối với máy để đi đúng đường là hỏng nặng hơn cái rối mà
	đợt này định chữa.

	Cái tách `ncc` với `tkct` không phải hoá đơn đã vào hệ hay chưa, mà là
	TIỀN ĐI ĐƯỜNG NÀO (ho_so_tt.py dòng 62: NCC trả thẳng từ MB). Nên
	`tkct` thuộc về câu 1 và vào thẳng, không đi qua câu hỏi hoá đơn.
	"""
	src = _js("19-ho-so-tt.js")
	than = _than_ham()
	cn = _doan(src, "var HS_LUONG_CONG_NO = [", "\nvar HS_LUONG_HOAN_UNG")
	hoan = _doan(src, "var HS_LUONG_HOAN_UNG = [", "\nvar HS_CAU_HOA_DON")
	la("tkct không nằm trong bảng của câu 2 nhánh công nợ", "tkct" in cn, False)
	la("tkct không nằm trong bảng của câu 2 nhánh hoàn ứng", "tkct" in hoan, False)
	dung("tkct là một lựa chọn của câu 1", "k: 'tkct'" in than)
	# Vao thang: nhanh tkct phai `return` TRUOC loi goi cau 2.
	i_tkct = than.index("if (duong === 'tkct')")
	i_cau2 = than.index("hsHoiHoaDon(")
	dung("tkct vào thẳng, không phải trả lời câu hoá đơn trước", i_tkct < i_cau2)
	dung("tkct đi thẳng tới màn chi từ TK công ty",
		than.index("go(scrChiCongTyTao)") < i_cau2)
	# Mo ta phai noi ro no lam duoc CA HAI, khong dan nhan "khong co hoa don".
	dung("mô tả nói rõ tick hoá đơn đang nợ HOẶC gõ tay",
		"tick hoá đơn đang nợ hoặc gõ tay từng khoản" in than)
	la("không còn dán nhãn không có hoá đơn cho tkct",
		"Không có hoá đơn mua nào" in src, False)
	# Man kia that su co doc hoa don ra: neu ngay nao do bo di thi cau chot
	# tren thanh noi suong, nen chot luon o day.
	dung("màn chi từ TK công ty thật sự có nạp hoá đơn đang nợ",
		"api('vagabond.ho_so_tt.hoa_don_cho_tra', { ncc: huNguoi" in src)


@ca("#196A thứ tự trong từng bảng giữ nguyên như thời năm nút")
def _thu_tu_giu_nguyen():
	"""Người dùng đã quen vị trí, đổi bảng thì đừng xáo trộn thêm.

	`tkct` được nâng lên câu 1 nên nó KHÔNG còn nằm trong dãy năm mã nữa,
	đó là đổi có chủ ý (xem ca kiểm tkct ở trên). Những gì còn giữ được thì
	vẫn chốt: trong bảng công nợ, `ncc` đứng trước `tt` y như thời năm nút;
	trong bảng hoàn ứng, `hu_hd` đứng trước `hu_khd`; và bảng công nợ khai
	trước bảng hoàn ứng.
	"""
	src = _js("19-ho-so-tt.js")
	dung("ncc đứng trước tt", src.index("k: 'ncc'") < src.index("k: 'tt'"))
	dung("tt đứng trước hu_hd", src.index("k: 'tt'") < src.index("k: 'hu_hd'"))
	dung("hu_hd đứng trước hu_khd",
		src.index("k: 'hu_hd'") < src.index("k: 'hu_khd'"))


@ca("#196A thôi ở câu 2 thì quay lại câu 1, không văng ra ngoài")
def _thoi_o_cau_hai_quay_lai():
	than = _than_ham()
	dung("có vòng lặp bọc hai câu", "for (;;) {" in than)
	dung("thôi ở câu 1 mới thoát hẳn", "if (!duong) return;" in than)
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
		"huDong = []; huGhiChu = ''; huTkChi = ''; huCpThue = ''; "
		"huChonHd = {}; huSuaO = -1;" in than)
	dung("hoàn ứng không hoá đơn dọn đủ bộ của nó",
		"if (c === 'hu_khd') { huDong = []; huGhiChu = ''; huTamUng = 0; "
		"huSuaO = -1; return go(scrHoanUngTao); }" in than)
	dung("hai luồng bảng tick xoá từ khoá tìm hoá đơn", "hsHdTu = '';" in than)
	dung("hoàn ứng có hoá đơn đặt đúng loại", "hsTaoLoai = 'Hoan ung HD';" in than)
	dung("công nợ nhà cung cấp đặt đúng loại", "hsTaoLoai = 'NCC';" in than)


@ca("#196A xoá hsTaoChon tới đâu thì xoá hsPhieuCua tới đó")
def _xoa_phieu_cua_theo_cap():
	"""Lỗi có thật trước v433, sửa luôn trong đợt này.

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
	src = _js("19-ho-so-tt.js")
	goi = _doan(src, "function hsHoiHoaDon(", "\nasync function hsChonLoaiMoi(")
	la("không có thẻ select ở câu 1", "<select" in than, False)
	la("không có thẻ select ở câu 2", "<select" in goi, False)
	dung("câu 1 đi qua hoiChon", than.count("await hoiChon(") == 1)
	dung("câu 2 đi qua hoiChon", goi.count("return hoiChon(") == 1)


@ca("#196A patches.txt có dòng đợt này và giữ nguyên dòng của phiên khác")
def _dang_ky():
	dong = [d.strip() for d in
		io.open(os.path.join(GOI, "patches.txt"), encoding="utf-8").read().splitlines()]
	dung("có dòng v433", "vagabond.patches.dong_bo_cau_truc #v433" in dong)
	# Ba dong nay cua cac phien khac, dot nay khong duoc lam mat.
	#
	# Rieng #v432 la cua phien lam man Quan ly nguoi dung (PR #199). Dot nay
	# ban dau cung dinh lay so 432, ho merge truoc nen phai nhuong. Nguy hiem
	# o cho git KHONG bao xung dot: hai ben cung doi APPVER thanh '432' va
	# cung them dung mot dong `#v432`, gop lai thanh MOT dong, tuc la ban dong
	# bo cau truc cua dot nay se khong bao gio chay ma khong ai hay. Bat duoc
	# nho doc APPVER va patches.txt tren origin/main NGAY TRUOC khi dat so.
	dung("giữ nguyên dòng v429", "vagabond.patches.dong_bo_cau_truc #v429" in dong)
	dung("giữ nguyên dòng v431", "vagabond.patches.dong_bo_cau_truc #v431" in dong)
	dung("giữ nguyên dòng v432 của phiên khác",
		"vagabond.patches.dong_bo_cau_truc #v432" in dong)
	dung("v433 đứng sau v432", dong.index("vagabond.patches.dong_bo_cau_truc #v432")
		< dong.index("vagabond.patches.dong_bo_cau_truc #v433"))

# -*- coding: utf-8 -*-
"""Màn danh sách hồ sơ thanh toán và ô chọn tài khoản (Issue #196 phần C).

Chị Dung, qua issue #196: *"Sau khi thanh toán xong thì có log. Để sau 1 thời
gian cần tìm lại số app hay nhà cung cấp đó thanh toán khi nào chỉ cần lọc là
ra"*. Ba mảnh của câu đó: ô tìm, ngày đã chi hiện ngay trên danh sách, và chip
lọc theo tài khoản đã chi.

Anh Việt 06/09/2026: *"chỗ chọn tk nợ tại sao lại bắt gõ tay? Phải chọn được
từ danh mục tài khoản đã cấu hình chứ nhỉ?"*.

Bộ ca này canh bốn chỗ mà một lần sửa màn hình dễ làm hỏng lặng lẽ:

  1. `hsTim` quay lại thành tham số chết. Nó đã từng như vậy: được gửi lên
     máy chủ mà không có ô nhập nào đặt giá trị cho nó.
  2. Bản xuất Excel không gửi đủ ô lọc. Tệp rộng hơn cái đang bày trên màn là
     đưa nhầm số liệu mà không ai đối chiếu lại.
  3. Ô tìm mất chữ sau mỗi lần bấm chip, vì màn vẽ lại.
  4. Ô chọn tài khoản quay lại kiểu bắt gõ từ khoá trước khi được nhìn thấy
     gì, hoặc cắt danh mục ở một con số cố định.
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


def _doan(src, dau, cuoi):
	i = src.index(dau)
	return src[i:src.index(cuoi, i + len(dau))]


def _man_danh_sach():
	return _doan(_js("19-ho-so-tt.js"), "async function scrHoSoTT() {", "\n/* ---------- Lap ho so")


@ca("#196C ô tìm có thật, không còn là tham số chết")
def _o_tim_co_that():
	than = _man_danh_sach()
	dung("có ô nhập trên màn", 'id="hsTimO"' in than)
	# Day moi la cho quan trong: PHAI co dong dat gia tri cho `hsTim`. Truoc
	# v434 chi co dong doc `hsTim` gui len may chu, khong dong nao ghi vao no.
	# v434 vong 2 tach lam hai bien nen cau gan doi hinh. Y dinh giu nguyen:
	# phai co dong GHI vao `hsTim`, khong chi doc no.
	dung("có chỗ ghi giá trị vào hsTim", "hsTim = hsTimGo;" in than)
	dung("vẫn gửi từ khoá lên máy chủ", "if (hsTim) ts.tu_khoa = hsTim;" in than)
	dung("bấm Enter mới đi hỏi máy chủ", "if (e.key !== 'Enter') return;" in than)


@ca("#196C ô tìm không mất chữ sau mỗi lần vẽ lại màn")
def _o_tim_giu_chu():
	"""Cùng cái bẫy đã vấp ở ô tìm hoá đơn kỳ trước.

	Màn này vẽ lại sau mỗi lần bấm chip, nên phải trả chữ về ô TRƯỚC khi nối
	phím. Gán sau là người ta gõ xong bấm một chip là mất chữ vừa gõ.
	"""
	than = _man_danh_sach()
	dung("trả giá trị về ô", "oTim.value = hsTimGo;" in than)
	a = than.index("oTim.value = hsTimGo;")
	b = than.index("oTim.addEventListener('keydown'")
	dung("gán giá trị đứng trước lúc nối phím", a < b)


@ca("#196C gõ xong bấm chip trước khi bấm Enter thì KHÔNG mất chữ")
def _go_roi_bam_chip_khong_mat_chu():
	"""Codex nêu trên PR #207, và nêu đúng.

	Bản đầu chỉ có MỘT biến `hsTim`, và nó chỉ được ghi lúc bấm Enter. Ai gõ
	xong rồi bấm một chip ngày, chip loại, chip trạng thái hay chip tài khoản
	thay vì bấm Enter thì màn vẽ lại, dòng trả giá trị về ô đưa lại chữ CŨ,
	chữ vừa gõ biến mất không dấu vết. Không màn nào báo.

	Nay tách làm hai: `hsTimGo` là chữ đang nằm trong ô, `hsTim` là chữ đã áp
	và đang được gửi lên máy chủ. Gõ tới đâu ghi lại tới đó, nhưng vẫn chỉ
	hỏi máy chủ khi bấm Enter.
	"""
	j = _js("19-ho-so-tt.js")
	than = _man_danh_sach()
	dung("có hai biến riêng cho ô tìm", "var hsTkChi = '', hsTimGo = '';" in j)
	dung("gõ tới đâu ghi lại tới đó",
		"oTim.addEventListener('input', function () { hsTimGo = oTim.value; hsVeNhacTim(); });"
		in than)
	# Van chi hoi may chu khi bam Enter, khong hoi theo tung phim.
	dung("chỉ áp khi bấm Enter", "hsTim = hsTimGo;" in than)
	la("không gọi máy chủ trong lúc gõ",
		"oTim.addEventListener('input', function () { hsTimGo = oTim.value; go(" in than, False)


@ca("#196C dòng nhắc dưới ô tìm đổi ngay theo từng phím")
def _dong_nhac_doi_ngay_theo_phim():
	"""Codex nêu vòng hai trên PR #207, và nêu đúng.

	Bản trước dựng câu "Đã gõ nhưng chưa tìm" một lần duy nhất lúc vẽ màn,
	còn sự kiện nhập chỉ ghi `hsTimGo`. Nên gõ thêm chữ thì dòng nhắc vẫn
	đứng yên ở trạng thái cũ, nói sai với cái người ta đang nhìn.

	Cách gỡ phải đắp chữ vào ĐÚNG cái ô nhắc, không được vẽ lại cả màn: vẽ
	lại là mất chỗ con trỏ đang đứng, mà gõ tới đâu gọi máy chủ tới đó thì
	còn tệ hơn.
	"""
	j = _js("19-ho-so-tt.js")
	than = _man_danh_sach()
	nhac = _doan(j, "function hsVeNhacTim() {", "\nasync function scrHoSoTT() {")
	dung("có ô riêng cho dòng nhắc", 'id="hsTimNhac"' in than)
	dung("ô nhắc để rỗng lúc vẽ màn, chữ do hàm nhắc đắp vào",
		'id="hsTimNhac" style="font-size:11.5px;margin-top:7px;line-height:1.5"></div>' in than)
	dung("vẽ lại dòng nhắc ngay lúc dựng màn", "hsVeNhacTim();" in than)
	dung("so chữ đang gõ với chữ đã áp", "if (go !== hsTim) {" in nhac)
	dung("nói rõ đã gõ nhưng chưa tìm", "Đã gõ nhưng chưa tìm." in nhac)
	dung("nói rõ đang lọc theo chữ nào", "Đang lọc theo" in nhac)
	# Hai dieu cam: khong ve lai ca man va khong hoi may chu trong ham nhac.
	la("dòng nhắc không vẽ lại cả màn", "go(scrHoSoTT" in nhac, False)
	la("dòng nhắc không gọi máy chủ", "api(" in nhac, False)
	# Chu nguoi ta go duoc dap thang vao innerHTML, phai qua bo loc the.
	dung("chữ người ta gõ phải qua bộ lọc thẻ", "h(go)" in nhac)


@ca("#196C hễ còn bật bộ lọc thì phải còn đường gỡ ra")
def _con_bat_loc_thi_con_duong_go():
	"""Codex nêu trên PR #207, và nêu đúng cả cho hàng chip đã có từ trước.

	`tk_chi` và `loai_cp_thue` chỉ được ghi trên hồ sơ luồng Chi từ TK công
	ty, nên đổi chip loại sang Công nợ NCC là danh sách rỗng. Trước đây hàng
	chip bị giấu luôn theo, tức là bộ lọc vẫn còn bật, vẫn được gửi lên máy
	chủ, mà không còn nút nào để tắt. Màn hình trống trơn và người ta không
	hiểu vì sao.
	"""
	than = _man_danh_sach()
	dung("còn bật lọc chi phí thuế thì vẫn bày hàng chip",
		"hsLoai === 'TK cong ty' || hsCpThue ?" in than)
	dung("còn bật lọc tài khoản thì vẫn bày hàng chip",
		"if (tkCo.length <= 1 && !hsTkChi) return '';" in than)
	# Cai dang chon phai luon co mat trong hang chip, khong thi bam tat bang gi.
	dung("cộng thêm cái đang chọn vào hàng chip",
		"if (hsTkChi && tkCo.indexOf(hsTkChi) < 0) tkCo.push(hsTkChi);" in than)
	dung("nói rõ vì sao danh sách rỗng và bấm đâu để bỏ lọc",
		"Bấm <b>Mọi tài khoản chi</b> để bỏ lọc." in than)
	# KHONG tu xoa bo loc: xoa lang le mot lua chon nguoi ta vua bam la kieu
	# hong nguoc lai, va cung la thu Codex canh o chieu kia.
	la("không tự xoá bộ lọc của người dùng", "hsTkChi = '';\n" in than, False)


@ca("#196C ngày đã chi hiện ngay trên danh sách")
def _hien_ngay_da_chi():
	than = _man_danh_sach()
	dung("có bày ngày thanh toán", "r.ngay_thanh_toan" in than)
	dung("bày theo kiểu ngày Việt", "hsNgayVn(r.ngay_thanh_toan)" in than)
	# Doc theo O NGAY chu khong suy tu trang thai: ho so ghi nhan tu truoc khi
	# co o nay van o trang thai Da thanh toan ma o ngay trong.
	la("không suy ngày từ trạng thái",
		"trang_thai === 'Da thanh toan' ? hsNgayVn" in than, False)
	s = _py("ho_so_tt.py")
	dung("máy chủ có trả ô ngày thanh toán", '"ngay_thanh_toan", "ma_giao_dich",' in s)


@ca("#196C chip lọc theo tài khoản đã chi")
def _chip_tai_khoan_chi():
	than = _man_danh_sach()
	s = _py("ho_so_tt.py")
	dung("có hàng chip tài khoản", "data-hstkc=" in than)
	dung("gửi tk_chi lên máy chủ", "if (hsTkChi) ts.tk_chi = hsTkChi;" in than)
	dung("máy chủ nhận tham số tk_chi", "loai_cp_thue=None, tk_chi=None):" in s)
	dung("máy chủ lọc theo tk_chi",
		'loc_ra = [o for o in loc_ra if (o.get("tk_chi") or "") == tk_chi]' in s)
	# Dem chip tren bo CHUA loc. Dua tk_chi vao `loc` cua get_all thi bam mot
	# chip xong cac chip kia rong het va khong bam lai duoc.
	dung("máy chủ đếm chip trên bộ chưa lọc", '"tk_chi_co": tk_co,' in s)
	la("không đưa tk_chi vào bộ lọc get_all", 'loc["tk_chi"]' in s, False)
	# Mot tai khoan thi khong can hang chip - TRU KHI dang bat bo loc, xem ca
	# kiem "he con bat bo loc thi phai con duong go ra".
	dung("một tài khoản mà không lọc thì giấu hàng chip",
		"if (tkCo.length <= 1 && !hsTkChi) return '';" in than)


@ca("#196C xuất Excel gửi ĐỦ mọi ô lọc đang bày trên màn")
def _xuat_excel_du_o_loc():
	"""Tệp tải về phải đúng bằng cái đang nhìn.

	Trước v434 nút xuất chỉ gửi `trang_thai`, `ncc`, `loai`. Ba ô lọc còn lại
	rơi mất, nên đang lọc "chi phí không hợp lệ" mà bấm xuất thì ra cả bộ.
	Không màn nào báo, chỉ lộ khi có người cộng lại.
	"""
	than = _man_danh_sach()
	nut = _doan(than, "if (bx) bx.onclick", "var bs = document.getElementById('hsSepay');")
	for o in ("trang_thai = hsTT", "ncc = hsNcc", "loai = hsLoai",
			"tu_khoa = hsTim", "loai_cp_thue = hsCpThue", "tk_chi = hsTkChi"):
		dung("nút xuất gửi %s" % o.split(" = ")[0], "t2." + o in nut)
	s = _py("ho_so_tt.py")
	xuat = _doan(s, "def xuat_excel(", "\trows = kq[\"rows\"]")
	for o in ("tu_khoa=tu_khoa", "loai_cp_thue=loai_cp_thue", "tk_chi=tk_chi"):
		dung("máy chủ chuyển tiếp %s" % o.split("=")[0], o in xuat)


@ca("#196C chọn tài khoản Nợ: bày cả danh mục, không bắt gõ trước")
def _chon_tai_khoan_bay_ca_danh_muc():
	"""Anh Việt nêu 06/09/2026, và nêu đúng.

	Bản cũ bắt gõ một từ khoá TRƯỚC rồi mới tra về tối đa 40 dòng khớp. Ba
	cái sai: phải đoán chữ để gõ trong khi chưa được nhìn thấy gì; gõ sai một
	chữ là màn báo "không thấy tài khoản nào khớp" rồi trả về tay không; và
	cái chốt 40 dòng thì lặng lẽ.
	"""
	j = _js("19-ho-so-tt.js")
	than = _doan(j, "async function huChonTaiKhoan(", "\nasync function huChonTep(")
	la("không còn bắt gõ từ khoá trước", "hoiNhap(" in than, False)
	la("không còn cắt 40 dòng", ".slice(0, 40)" in than, False)
	dung("lấy hết danh mục", "gioi_han: 0" in j)
	dung("giữ lại danh mục đã tải, không tải lại mỗi dòng", "if (huTkDs) return huTkDs;" in j)
	# `hoiChon` tra ve null khi bam Thoi; `sheet` dong lai ma khong goi gi ca,
	# de treo loi hua mai mai.
	dung("đi qua hoiChon để còn đường bấm Thôi", "await hoiChon(" in than)
	dung("vẫn giữ được tài khoản đang chọn", "dang_chon || ''" in than)


@ca("#196C phép tính số dòng tối đa: gọi THẬT chứ không dò chữ")
def _gioi_han_tk_goi_that():
	"""Codex nêu vòng hai trên PR #207, và nêu đúng.

	Bản trước để phép tính nằm thẳng trong `ho_so_tt.py` (có `import frappe`)
	nên ca kiểm chỉ dò được chuỗi trong mã nguồn. Dò chuỗi không chứng minh
	được gì: một biến khai ra rồi không dùng vẫn qua được.

	Nay phép tính nằm ở `chon_ncc.gioi_han_tk`, là phép THUẦN, gọi thẳng
	được. Hai đầu vào xấu Codex chỉ ra đều được canh: số âm KHÔNG lặng lẽ
	thành lấy hết, chữ không phải số KHÔNG ném ValueError trần.
	"""
	dung("không truyền thì giữ 40 như cũ", cn.gioi_han_tk(None) == 40)
	dung("chuỗi rỗng cũng giữ 40", cn.gioi_han_tk("") == 40)
	dung("toàn khoảng trắng cũng giữ 40", cn.gioi_han_tk("   ") == 40)
	dung("số 0 là LẤY HẾT", cn.gioi_han_tk(0) == 0)
	dung('chuỗi "0" cũng là lấy hết', cn.gioi_han_tk("0") == 0)
	dung("số dương giữ nguyên", cn.gioi_han_tk(7) == 7)
	dung("chuỗi có khoảng trắng hai đầu vẫn đọc được", cn.gioi_han_tk("  40 ") == 40)
	# JSON khong phan biet so nguyen voi so thuc, nen 3.0 la nguoi goi that
	# tha chu khong phai dau vao xau.
	dung("số thực tròn vẫn nhận", cn.gioi_han_tk(3.0) == 3)
	dung('chuỗi "3.0" vẫn nhận', cn.gioi_han_tk("3.0") == 3)
	for xau in (-5, "-1", "abc", "1.5", "3,5"):
		nem = False
		try:
			cn.gioi_han_tk(xau)
		except cn.GioiHanXau:
			nem = True
		dung("đầu vào xấu %r phải ném lỗi có tên" % (xau,), nem)


@ca("#196C máy chủ đổi số dòng tối đa xấu thành lời nhắn có chữ")
def _gioi_han_tk_loi_co_chu():
	"""`GioiHanXau` ném ra ngoài màn hình thì người ta chỉ thấy một dòng
	ValueError trần, không biết phải làm gì tiếp. QT-24 của AGENTS.md: lời
	báo lỗi phải nói việc kế tiếp."""
	s = _py("ho_so_tt.py")
	than = _doan(s, "def ds_tai_khoan(", "\ndef _sinh_hoa_don_hoan_ung(")
	ma = "\n".join(d for d in than.split("\n") if not d.strip().startswith("#"))
	la("không còn tự tính trong hàm chạm hệ", "int(gioi_han or 40)" in ma, False)
	dung("gọi phép tính thuần", "chon_ncc.gioi_han_tk(gioi_han)" in than)
	dung("bắt đúng lỗi có tên", "except chon_ncc.GioiHanXau:" in than)
	dung("nói việc kế tiếp: gửi số nguyên không âm", "Gửi số nguyên không âm" in than)
	dung("nói cả đường lấy hết", "hoặc gửi 0 để lấy hết danh mục" in than)
	dung("cả hai nhánh đều dùng chung con số đã tính",
		than.count("limit_page_length=han,") == 2)


@ca("#196C patches.txt có dòng đợt này và giữ nguyên dòng của phiên khác")
def _dang_ky():
	dong = [d.strip() for d in
		io.open(os.path.join(GOI, "patches.txt"), encoding="utf-8").read().splitlines()]
	dung("có dòng v434", "vagabond.patches.dong_bo_cau_truc #v434" in dong)
	for cu in ("#v431", "#v432", "#v433"):
		dung("giữ nguyên dòng %s" % cu, "vagabond.patches.dong_bo_cau_truc " + cu in dong)

# -*- coding: utf-8 -*-
"""Rà soát phá huỷ phân hệ Hồ sơ thanh toán APP (v413, 04/09/2026).

Không đi theo happy path. Mười một chỗ dưới đây đều là đường mà một người
dùng bình thường đi được, và trước 04/09/2026 đều dẫn tới mất tiền thật,
kẹt luồng, hoặc mất dấu vết giải trình.

Xuất phát từ ca thật: Uyên không nối được phiếu thanh toán nội bộ vào hồ sơ
hoàn ứng. Kéo sợi chỉ đó ra thì lộ cả một chùm.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


def _goc(ten):
	return io.open(os.path.join(os.path.dirname(GOI), ten), encoding="utf-8").read()


def _doan(src, tu, den):
	i = src.index(tu)
	return src[i:src.index(den, i + len(tu))]


# ================================================== phiếu thanh toán nội bộ


@ca("v413 nối chồng phiếu nội bộ thì DỪNG HẲN, không ghi log rồi đi tiếp")
def _khoa_phieu_nem_loi():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def _khoa_phieu_noi_bo(", "\ndef ")
	dung("có ném lỗi", "frappe.throw(" in than)
	dung("hết bỏ qua bằng continue", "\t\t\t\tcontinue\n" not in than)
	# Dong dau khong duoc boc try/except: hong ma van cho ho so ra doi thi
	# phieu van hien trong bang chon va noi duoc vao ho so thu hai.
	dung("dòng dấu không nuốt lỗi", "except Exception:" not in than)


@ca("v413 hồ sơ bị TỪ CHỐI hoặc HUỶ thì nhả phiếu nội bộ ra, không giữ chỗ")
def _ho_so_chet_nha_phieu():
	src = _py("ho_so_tt.py")
	dung("có hàm nhả", "def _nha_het_phieu_noi_bo(doc):" in src)
	than = _doan(src, "def duyet(name, buoc, ly_do=", "\ndef ")
	tc = _doan(than, 'elif buoc == "tu_choi":', 'elif buoc == "huy":')
	dung("nhánh từ chối có nhả", "_nha_het_phieu_noi_bo(doc)" in tc)
	huy = than[than.index('elif buoc == "huy":'):]
	dung("nhánh huỷ có nhả", "_nha_het_phieu_noi_bo(doc)" in huy)


@ca("v413 nhả phiếu chỉ khi KHÔNG còn dòng nào khác của hồ sơ đang giữ")
def _nha_phieu_dem_dong_con():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def _tra_phieu_noi_bo(", "\n@frappe.whitelist()")
	dung("có đếm dòng con", "select count(*)" in than)
	dung("đếm đúng bảng dòng", "tabVagabond Ho So TT Dong" in than)
	dung("lọc theo đúng phiếu", "ifnull(de_nghi_chi, '') = %s" in than)
	# Con dong khac giu thi phai RETURN, khong duoc nha.
	i_dem = than.index("select count(*)")
	i_nha = than.index('set_value(DNC, ma_phieu, "ho_so_tt", None')
	dung("đếm trước rồi mới nhả", i_dem < i_nha)


@ca("v413 máy chủ soi phiếu nội bộ trước khi ghi: trùng, sai tiền, chưa duyệt")
def _soi_phieu():
	src = _py("ho_so_tt.py")
	# v416 them cong tac `theo_tien` cho luong co hoa don, neo bat theo tien
	# ham chu khong bat nguyen chu ky.
	dung("có hàm soi", "def _soi_phieu_noi_bo(sach" in src)
	than = _doan(src, "def _soi_phieu_noi_bo(sach", "\ndef ")
	dung("chặn một phiếu hai dòng", "đang nối vào hai khoản trong cùng hồ sơ" in than)
	dung("chặn phiếu chưa duyệt", "TT_PHIEU_NOI_BO" in than)
	dung("chặn số tiền lệch", "abs(flt(d.get(\"so_tien\")) - tien_phieu) > 1" in than)


@ca("v413 hàm soi được gọi TRƯỚC khi hồ sơ được chèn, để lỗi thì cuộn sạch")
def _soi_goi_truoc_insert():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def tao_hoan_ung(", "\n@frappe.whitelist()")
	dung("có gọi", "_soi_phieu_noi_bo(sach)" in than)
	dung("gọi trước khi dựng doc",
		than.index("_soi_phieu_noi_bo(sach)") < than.index('frappe.new_doc("Vagabond Ho So TT")'))


# ================================================================= tiền và duyệt


@ca("v413 cấp giám đốc cũng chặn tự duyệt, và chặn một người ký cả hai cấp")
def _gd_khong_tu_duyet():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def duyet(name, buoc, ly_do=", "\ndef ")
	gd = _doan(than, 'elif buoc == "gd":', 'elif buoc == "tu_choi":')
	dung("chặn người lập tự duyệt", "doc.nguoi_tao == toi" in gd)
	dung("chặn người đã ký cấp kế toán", '(doc.fin_boi or "") == toi' in gd)
	# Cap ke toan von da co chot nay, giu nguyen.
	fin = _doan(than, 'elif buoc == "fin":', 'elif buoc == "gd":')
	dung("cấp kế toán vẫn giữ chốt cũ", "doc.nguoi_tao == toi" in fin)


@ca("v413 đổi tài khoản nhận sau khi đã duyệt thì hạ về chờ giám đốc ký lại")
def _doi_tk_phai_ky_lai():
	src = _py("ho_so_tt.py")
	dung("có hàm", "def _doi_tk_thi_ky_lai(doc):" in src)
	than = _doan(src, "def _doi_tk_thi_ky_lai(doc):", "\n@frappe.whitelist()")
	dung("chỉ động tới hồ sơ đã duyệt", "if doc.trang_thai != TT_DA_DUYET:" in than)
	dung("hạ về chờ giám đốc", 'db_set("trang_thai", TT_CHO_GD' in than)
	dung("xoá chữ ký giám đốc cũ", 'db_set("gd_boi", ""' in than)
	# Ca hai duong doi tai khoan deu phai goi.
	dung("đường gõ tay có gọi", "_doi_tk_thi_ky_lai(doc)" in _doan(src, "def sua_tk_nhan(", "\n@frappe.whitelist()"))
	dung("đường chọn có gọi", "_doi_tk_thi_ky_lai(doc)" in _doan(src, "def doi_tk_nhan(", "\n# ---"))


@ca("v413 dò SePay so với số THẬT SỰ phải chuyển, không so với tổng tiền")
def _sepay_so_con_lai():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def kiem_sepay(", "\n@frappe.whitelist()")
	dung("đọc con_lai", '"con_lai"' in than)
	dung("có số phải chuyển", "phai_chuyen = flt(d.get(\"con_lai\")) or flt(d[\"tong_tien\"])" in than)
	dung("so với số phải chuyển", 'flt(o.get("chi")) >= phai_chuyen - 1' in than)
	dung("hết so thẳng với tổng tiền", 'flt(o.get("chi")) >= flt(d["tong_tien"]) - 1' not in than)


@ca("v413 ghi nhận đã trả mà bỏ trống ô mã thì GIỮ mã đã khớp tay, không xoá trắng")
def _khong_xoa_ma_giao_dich():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def danh_dau_da_tra(", "\n@frappe.whitelist()")
	dung("có rào", 'if (ma_giao_dich or "").strip():' in than)
	dung("hết ghi đè vô điều kiện",
		'\tdoc.ma_giao_dich = (ma_giao_dich or "").strip()\n' not in than)


@ca("v413 hồ sơ đã duyệt hoặc đã chi thì không gỡ chứng từ ra được nữa")
def _khong_go_tep_sau_duyet():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def go_tep_dong(", "\n# ---")
	dung("chặn theo trạng thái", "doc.trang_thai in (TT_DA_DUYET, TT_DA_TRA)" in than)
	dung("có ghi vết", "_ghi_vet(" in than)


# ======================================================================= app


@ca("v413 app đọc cờ lỗi trước, không kết luận nhầm là không có phiếu nào")
def _app_doc_co_loi():
	src = _js("19-ho-so-tt.js")
	than = _doan(src, "async function huNoiPhieuNoiBo(", "async function huXemVaNoiPhieu(")
	dung("đọc kq.loi", "if (kq && kq.loi) {" in than)
	dung("đọc lỗi trước khi đếm danh sách",
		than.index("kq.loi") < than.index("if (!ds.length)"))


@ca("v413 app chặn nối cùng một phiếu vào hai khoản của một hồ sơ")
def _app_chan_noi_trung():
	src = _js("19-ho-so-tt.js")
	than = _doan(src, "async function huXemVaNoiPhieu(", "\nasync function ")
	dung("có dò dòng khác", "j !== i && (d && d.de_nghi_chi" in than)
	dung("chặn trước khi gọi máy chủ",
		than.index("Phiếu đã dùng rồi") < than.index("xem_phieu_noi_bo"))
	# Bang chon cung phai danh dau phieu da dung.
	ban = _doan(src, "async function huNoiPhieuNoiBo(", "async function huXemVaNoiPhieu(")
	dung("bảng chọn có đánh dấu", "ĐÃ NỐI Ở KHOẢN SỐ" in ban)


@ca("v413 hai thẻ hoàn ứng nói rõ khác nhau ở chỗ hoá đơn đã vào hệ hay chưa")
def _hai_the_hoan_ung():
	"""Ý ĐỊNH GỐC GIỮ NGUYÊN, chỗ đọc và hai câu về phiếu nội bộ thì đổi.

	Ca kiểm này dựng ở v413 để chốt một việc: hai thẻ hoàn ứng phải nói rõ
	chúng khác nhau ở chỗ hoá đơn ĐÃ vào hệ hay CHƯA. Ý đó còn nguyên và
	dưới đây vẫn chốt nó.

	Hai chỗ phải sửa lại ở v432:

	1. Chỗ đọc. Hai thẻ không còn nằm trong thân `hsChonLoaiMoi` nữa mà ở
	   bảng `HS_LUONG_HOAN_UNG` khai ngay trên hàm, vì màn này đổi từ năm
	   nút thành hai câu hỏi (issue #196 phần A).

	2. Hai câu về phiếu thanh toán nội bộ. v413 chốt "đường DUY NHẤT nối
	   được phiếu thanh toán nội bộ" và "KHÔNG nối được phiếu thanh toán
	   nội bộ ở đường này". Anh Việt chốt 04/09/2026 cho nối phiếu ở CẢ
	   đường hoàn ứng có hoá đơn (phiếu chỉ đóng vai chứng từ, không đụng
	   số tiền - xem `hsODongPhieu` và `_soi_phieu_noi_bo(dong,
	   theo_tien=False)`). Từ hôm đó hai câu ấy sai sự thật, mà sai theo
	   hướng đẩy người ta sang nhầm đường, nên v432 bỏ hẳn. Ca kiểm giờ
	   chốt chiều ngược lại: KHÔNG được có lại hai câu đó.
	"""
	src = _js("19-ho-so-tt.js")
	than = _doan(src, "var HS_LUONG_HOAN_UNG = [", "\nvar HS_CAU_HOA_DON")
	dung("thẻ trên nói đã có trong hệ", "Đã có, đang nợ trên sổ" in than)
	dung("thẻ dưới nói chưa có", "nhan: 'Chưa có'" in than)
	# Ma cua hai the khong duoc doi, doi la vo duong di.
	dung("mã thẻ giữ nguyên", "k: 'hu_hd'" in than and "k: 'hu_khd'" in than)
	# Cau hoi chung phai noi thang "da nam trong he", vi do moi la tieu chi
	# that. Xem chu thich dai o `hsChonLoaiMoi`.
	dung("câu hỏi chung hỏi đúng tiêu chí",
		"var HS_CAU_HOA_DON = 'Hoá đơn mua đã nằm trong hệ chưa?';" in src)
	dung("nói thẳng cầm hoá đơn giấy vẫn là chưa có",
		'Cầm tờ hoá đơn giấy trong tay mà kế toán chưa nhập thì vẫn chọn "chưa có".' in src)
	la("bỏ câu DUY NHẤT đã sai từ 04/09/2026",
		"đường DUY NHẤT nối được phiếu thanh toán nội bộ" in src, False)
	la("bỏ câu KHÔNG nối được đã sai từ 04/09/2026",
		"KHÔNG nối được phiếu thanh toán nội bộ ở đường này" in src, False)


@ca("v413 patches.txt có dòng đợt này")
def _dang_ky():
	dong = [d.strip() for d in _goc("vagabond/patches.txt").splitlines()]
	dung("có dòng v413", "vagabond.patches.dong_bo_cau_truc #v413" in dong)
	dung("giữ nguyên dòng v410", "vagabond.patches.dong_bo_cau_truc #v410" in dong)

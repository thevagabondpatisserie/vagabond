# -*- coding: utf-8 -*-
"""Cửa sửa và huỷ của cấp giám đốc (v418, 04/09/2026).

Anh Việt lập thử một phiếu nộp quỹ NQ-2026-01629 rồi bỏ đó ở trạng thái
Nháp. Tới lúc làm biên nhận THẬT cho đúng ngày đó thì máy chặn vì "đã có
phiếu trùm lên khoảng ngày", mà trên màn không có một nút nào gỡ phiếu nháp
kia ra. Một cái ngõ cụt do chính phần mềm dựng lên.

Anh Việt 04/09/2026: *"luôn có nút sửa/huỷ (chứ không xoá) dành cho cấp
giám đốc cho mọi loại phiếu, em ghi vào backend"*.

Bộ ca này chốt ba thứ dễ trôi mất ở lần sửa sau: huỷ là huỷ MỀM chứ không
xoá, lý do là bắt buộc, và phiếu đã huỷ thôi giữ chỗ khoảng ngày.
"""

import io
import json
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


def _dt(ten):
	return json.load(io.open(
		os.path.join(GOI, "vagabond", "doctype", ten, ten + ".json"), encoding="utf-8"))


def _ham(src, ten):
	"""Cắt lấy thân một hàm cấp mô đun, từ dòng def tới dòng def kế tiếp."""
	i = src.index("\ndef %s(" % ten)
	j = src.find("\ndef ", i + 5)
	return src[i:j if j > 0 else len(src)]


def _o(dt, ten):
	for f in dt["fields"]:
		if f.get("fieldname") == ten:
			return f
	return None


# =============================================== 1. mô đun dùng chung


@ca("v418 có mô đun giam_doc_sua_huy làm chỗ chốt luật dùng chung")
def _co_mo_dun():
	s = _py("giam_doc_sua_huy.py")
	for t in ("def duoc_sua_huy(", "def sach_ly_do(", "def chan(",
			"def doc_ly_do(", "def ghi_vet(", "def dong_dau_huy(",
			"def da_huy("):
		dung("có %s" % t, t in s)


@ca("v418 cấp giám đốc đúng bộ vai mà ho_so_tt và de_nghi_chi đang dùng")
def _cung_bo_vai():
	s = _py("giam_doc_sua_huy.py")
	la("vai giám đốc", 'VAI_GD = {"AP Giám đốc", "System Manager"}' in s, True)
	# Hai mô đun kia phải khai y hệt, không được sinh ra khái niệm giám đốc
	# thứ hai trong cùng một hệ.
	la("ho_so_tt cùng bộ", 'VAI_GD = {"AP Giám đốc", "System Manager"}' in _py("ho_so_tt.py"), True)
	la("de_nghi_chi cùng bộ",
		'VAI_GIAM_DOC = {"AP Giám đốc", "System Manager"}' in _py("de_nghi_chi.py"), True)


@ca("v418 lý do là bắt buộc và phải dài hơn mức gõ cho có")
def _bat_ly_do():
	s = _py("giam_doc_sua_huy.py")
	dung("có ngưỡng độ dài", "DAI_LY_DO_TOI_THIEU = 8" in s)
	than = _ham(s, "sach_ly_do")
	dung("chặn khi ngắn", "raise ValueError(" in than)
	dung("gọt khoảng trắng", '" ".join(str(ly_do or "").split())' in than)


@ca("v418 mô đun dùng chung KHÔNG có một đường xoá nào")
def _khong_xoa():
	s = _py("giam_doc_sua_huy.py")
	for xau in ("frappe.delete_doc", ".delete(", "DELETE FROM", "delete from"):
		la("không có %s" % xau, xau in s, False)


# =============================================== 2. nộp quỹ


@ca("v418 nộp quỹ có trạng thái huỷ, và huỷ nằm NGOÀI nhóm giữ chỗ")
def _nq_trang_thai():
	s = _py("nop_quy.py")
	dung("có TT_HUY", 'TT_HUY = "Đã huỷ"' in s)
	dung("có nhóm giữ chỗ", "TT_CON_GIU_CHO = (TT_NHAP, TT_CHO_KY, TT_DA_NOP)" in s)
	# Chính cái này là thứ gỡ ngõ cụt của NQ-2026-01629: nếu có ngày nào đó
	# ai đó thêm TT_HUY vào nhóm giữ chỗ thì phiếu huỷ lại chặn phiếu thật.
	dung("huỷ không giữ chỗ", "TT_CON_GIU_CHO = (TT_NHAP, TT_CHO_KY, TT_DA_NOP, TT_HUY)" not in s)
	dt = _dt("vagabond_nop_quy")
	la("doctype có Đã huỷ", "Đã huỷ" in (_o(dt, "trang_thai") or {}).get("options", ""), True)


@ca("v418 _phieu_trum chỉ đếm phiếu còn giữ chỗ")
def _nq_trum():
	than = _ham(_py("nop_quy.py"), "_phieu_trum")
	dung("lọc theo nhóm giữ chỗ", '"trang_thai": ["in", list(TT_CON_GIU_CHO)]' in than)


@ca("v418 nop_quy.huy chặn vai ở máy chủ, bắt lý do, và không xoá")
def _nq_huy():
	than = _ham(_py("nop_quy.py"), "huy")
	dung("chặn vai", "giam_doc_sua_huy.chan(" in than)
	dung("bắt lý do", "giam_doc_sua_huy.doc_ly_do(" in than)
	dung("chặn huỷ hai lần", "giam_doc_sua_huy.da_huy(" in than)
	dung("đóng dấu vết", "giam_doc_sua_huy.dong_dau_huy(" in than)
	dung("đặt trạng thái huỷ", "doc.trang_thai = TT_HUY" in than)
	la("không xoá", "delete" in than.lower(), False)


@ca("v418 huỷ phiếu nộp quỹ phải NHẢ các ca nó đang giữ")
def _nq_nha_ca():
	s = _py("nop_quy.py")
	than = _ham(s, "_nha_ca")
	dung("xoá ô phieu_nop", '"phieu_nop", ""' in than)
	dung("trả ca về Đã chốt", "ca_quay.TT_DA_CHOT" in than)
	# Quên nhả là khoá vĩnh viễn các ca đó: `tao()` sẽ chặn mãi với câu "ca
	# này đã nằm trong phiếu ... rồi", mà phiếu đó thì không còn hiệu lực.
	dung("huỷ có gọi nhả", "_nha_ca(doc, ve_da_chot=" in _ham(s, "huy"))


@ca("v418 sửa phiếu đã ký nhận thì ĐẬP chữ ký, không chỉnh lén")
def _nq_sua_dap_ky():
	than = _ham(_py("nop_quy.py"), "sua")
	dung("chặn vai", "giam_doc_sua_huy.chan(" in than)
	dung("bắt lý do", "giam_doc_sua_huy.doc_ly_do(" in than)
	dung("xoá chữ ký bên nhận", 'doc.chu_ky_ben_nhan = ""' in than)
	dung("rơi về Chờ ký nhận", "doc.trang_thai = TT_CHO_KY" in than)
	dung("đổi tiền thì xoá luôn ký giao", 'doc.chu_ky_ben_giao = ""' in than)
	dung("rơi về Nháp", "doc.trang_thai = TT_NHAP" in than)
	dung("phiếu đã huỷ thì không sửa", "if doc.trang_thai == TT_HUY:" in than)


@ca("v418 sửa khoảng ngày phải kiểm lại đụng phiếu khác, bỏ qua chính mình")
def _nq_sua_trum():
	than = _ham(_py("nop_quy.py"), "sua")
	dung("kiểm trùm", "_phieu_trum(doc.get(\"diem_ban\"), tu, den, bo_qua=doc.name)" in than)
	dung("tính lại kỳ vọng", "doc.tien_ky_vong = gom_tien_mat(" in than)


@ca("v418 doctype nộp quỹ có đủ bốn ô vết huỷ, và đều chỉ đọc")
def _nq_o_vet():
	dt = _dt("vagabond_nop_quy")
	for ten in ("huy_boi", "ten_nguoi_huy", "huy_luc", "ly_do_huy"):
		o = _o(dt, ten)
		dung("có ô %s" % ten, o is not None)
		la("ô %s chỉ đọc" % ten, (o or {}).get("read_only"), 1)
		dung("ô %s có trong field_order" % ten, ten in dt["field_order"])


@ca("v418 chi_tiet nộp quỹ trả về quyền sửa huỷ và cả lý do huỷ")
def _nq_chi_tiet():
	than = _ham(_py("nop_quy.py"), "chi_tiet")
	for o in ('"duoc_sua_huy"', '"ly_do_huy"', '"ten_nguoi_huy"', '"huy_luc"'):
		dung("trả %s" % o, o in than)


# =============================================== 3. đề nghị chi


@ca("v418 đề nghị chi có trạng thái huỷ thật, khác hẳn Bị trả lại")
def _dnc_trang_thai():
	s = _py("de_nghi_chi.py")
	dung("có TT_HUY", 'TT_HUY = "Da huy"' in s)
	dung("có nhãn tiếng Việt", 'TT_HUY: "Đã huỷ"' in s)
	# Chip cu khoa "da_huy" dang tro toi nhom BI TRA LAI va nguoi dung da
	# quen bam tu 20/08. Doi y nghia cua no la doi cai ma ho da quen.
	dung("chip cũ giữ nguyên", '("da_huy", "Bị trả lại", (TT_TRA_LAI,)),' in s)
	dung("chip huỷ dùng khoá riêng", '("huy", "Đã huỷ", (TT_HUY,)),' in s)
	dt = _dt("vagabond_de_nghi_chi")
	la("doctype có Da huy", "Da huy" in (_o(dt, "trang_thai") or {}).get("options", ""), True)


@ca("v418 de_nghi_chi.huy chặn phiếu đã chi và phiếu đang nối vào hồ sơ")
def _dnc_huy():
	than = _ham(_py("de_nghi_chi.py"), "huy")
	dung("chặn vai", "giam_doc_sua_huy.chan(" in than)
	dung("bắt lý do", "giam_doc_sua_huy.doc_ly_do(" in than)
	# Tien da roi khoi tai khoan that, do doi soat SePay xac nhan. Bo phieu
	# luc do la so mat dau vet cua mot lan tien di ra.
	dung("chặn phiếu đã chi", "if doc.trang_thai == TT_DA_CHI:" in than)
	dung("chặn phiếu đã nối hồ sơ", "tabVagabond Ho So TT Dong" in than)
	dung("gỡ khỏi hộp việc", "_het_viec(doc.name)" in than)
	la("không xoá", "delete" in than.lower(), False)


@ca("v418 phiếu đã huỷ không đi tiếp được trong chuỗi duyệt")
def _dnc_khong_di_tiep():
	s = _py("de_nghi_chi.py")
	than = _ham(s, "duoc_duyet_khong")
	# TT_HUY khong nam trong bang `can`, nen ham tra ve False. Neu ai do
	# them no vao bang do thi phieu huy lai duyet duoc.
	la("huỷ không có bước duyệt", "TT_HUY" in than, False)
	dung("gửi duyệt chỉ nhận Nháp và Bị trả lại",
		"if doc.trang_thai not in (TT_NHAP, TT_TRA_LAI):" in _ham(s, "gui_duyet"))
	# Webhook SePay chi quet phieu dang cho chi, nen phieu huy khong the tu
	# nhay sang Da chi.
	dung("webhook chỉ quét phiếu chờ chi",
		'filters={"trang_thai": ["in", [TT_CHO_KE_TOAN, TT_HOAN_TAT]]}' in _ham(s, "_phieu_cho_chi"))


@ca("v418 phiếu đã huỷ không nối được vào hồ sơ hoàn ứng")
def _dnc_khong_noi():
	s = _py("ho_so_tt.py")
	dung("chỉ nhận phiếu đã qua duyệt",
		'TT_PHIEU_NOI_BO = ("Hoan tat", "Da chi")' in s)


@ca("v418 doctype đề nghị chi có đủ bốn ô vết huỷ")
def _dnc_o_vet():
	dt = _dt("vagabond_de_nghi_chi")
	for ten in ("huy_boi", "ten_nguoi_huy", "huy_luc", "ly_do_huy"):
		dung("có ô %s" % ten, _o(dt, ten) is not None)
		dung("ô %s có trong field_order" % ten, ten in dt["field_order"])


# =============================================== 4. cửa ngõ và màn hình


@ca("v418 ba cửa mới đều đã khai trong danh sách cửa ngõ")
def _cua_ngo():
	s = _py("khung/kiem_thu/thu_cua_ngo.py")
	nq = s[s.index('"nop_quy.py"'):s.index('"nop_quy.py"') + 400]
	dung("nop_quy có huy", '"huy"' in nq)
	dung("nop_quy có sua", '"sua"' in nq)
	dnc = s[s.index('"de_nghi_chi.py"'):s.index('"de_nghi_chi.py"') + 1200]
	dung("de_nghi_chi có huy", '"huy",' in dnc)


@ca("v418 màn nộp quỹ có nút Sửa, nút Huỷ và màn Sửa riêng")
def _man_nop_quy():
	s = _js("21-ke-toan-khac.js")
	dung("nút Sửa", "id=\"nqSua\"" in s)
	dung("nút Huỷ", "id=\"nqHuy\"" in s)
	dung("có màn Sửa", "async function scrNopQuySua()" in s)
	dung("gọi cửa huỷ", "'vagabond.nop_quy.huy'" in s)
	dung("gọi cửa sửa", "'vagabond.nop_quy.sua'" in s)
	# Nut chi ve khi MAY CHU bao du vai. Man khong tu suy theo hasRole.
	dung("nút theo cờ máy chủ", "d.duoc_sua_huy && d.trang_thai !== 'Đã huỷ'" in s)
	dung("bắt lý do trước khi gọi", "bat_buoc: true" in s)
	dung("chip Đã huỷ", "['Đã huỷ', 'Đã huỷ']" in s)
	dung("màu chip Đã huỷ", "'Đã huỷ': ['#f2f4f7', '#98a2b3']" in s)


@ca("v418 màn thanh toán nội bộ có nút Huỷ của giám đốc")
def _man_ttnb():
	s = _js("16-mua-hang.js")
	dung("nút Huỷ", "id=\"ttnbHuy\"" in s)
	dung("gọi cửa huỷ", "'vagabond.de_nghi_chi.huy'" in s)
	dung("nút theo cờ máy chủ", "if (d.huy_duoc) {" in s)
	dung("bảng báo phiếu đã huỷ", "d.trang_thai === 'Da huy'" in s)


@ca("v418 màn biên nhận tiền cũng lọc được nhóm Đã huỷ")
def _man_bnt():
	dung("chip Đã huỷ", "['Đã huỷ', 'Đã huỷ']" in _js("39-bien-nhan-tien.js"))

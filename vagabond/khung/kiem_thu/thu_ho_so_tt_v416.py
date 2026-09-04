# -*- coding: utf-8 -*-
"""Bốn việc treo của phân hệ APP, làm nốt (v416, 04/09/2026).

Bản v413 rà phá huỷ ra mười một lỗ hổng, bịt chín, còn bốn cái để lại vì
chúng chạm sổ cái hoặc cần anh Việt chốt cách hạch toán. Anh Việt chốt ngày
04/09/2026, nay làm nốt. Kèm một lỗi một dòng của phiên khác đang làm chết
màn KPI trên site.
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


# ===================================================== 1. lỗi nhập của kpi.py


@ca("v416 kpi.py nhập cfg_o thật sự, không để trong phần chú thích")
def _kpi_nhap_cfg_o():
	src = _py("kpi.py")
	dung("nhập đủ hai tên", "from vagabond.lib import cfg, cfg_o" in src)
	dung("hết đẩy cfg_o vào noqa", "import cfg  # noqa: E402, cfg_o" not in src)
	# Va van con cho DUNG no, khong thi sua nham huong.
	dung("vẫn có chỗ dùng", "cfg_o(TRUONG_CAU_HINH)" in src)


# ============================================ 2. đua tranh khi ghi nhận đã trả


@ca("v416 ghi nhận đã trả khoá bản ghi TRƯỚC khi đọc trạng thái")
def _khoa_truoc_khi_doc():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def danh_dau_da_tra(", "\n@frappe.whitelist()")
	dung("có khoá", "for_update=True" in than)
	# Khoa PHAI dat truoc get_doc: khoa sau thi da doc so cu roi.
	dung("khoá trước khi đọc hồ sơ",
		than.index("for_update=True") < than.index('frappe.get_doc("Vagabond Ho So TT", name)'))
	dung("vẫn giữ chốt đã làm rồi", 'if doc.trang_thai == TT_DA_TRA:' in than)
	dung("khoá hỏng thì vẫn chạy tiếp", "khong khoa duoc ho so khi ghi nhan" in than)


# ================================== 3. hồ sơ đã sinh hoá đơn thì không giết suông


@ca("v416 Từ chối và Huỷ đều chặn khi hồ sơ đã sinh hoá đơn ghi sổ")
def _chan_giet_ho_so():
	src = _py("ho_so_tt.py")
	dung("có hàm đọc hoá đơn", "def _hoa_don_da_sinh(doc):" in src)
	dung("có hàm chặn", "def _chan_giet_ho_so_da_sinh_hoa_don(doc, viec):" in src)
	than = _doan(src, "def _hoa_don_da_sinh(doc):", "\ndef _chan_giet")
	dung("chỉ tính hoá đơn đã ghi sổ", 'get_value("Purchase Invoice", ma, "docstatus")) == 1' in than)
	d2 = _doan(src, "def duyet(name, buoc, ly_do=", "\ndef ")
	tc = _doan(d2, 'elif buoc == "tu_choi":', 'elif buoc == "huy":')
	dung("nhánh từ chối có chặn", '_chan_giet_ho_so_da_sinh_hoa_don(doc, "Từ chối")' in tc)
	huy = d2[d2.index('elif buoc == "huy":'):]
	dung("nhánh huỷ có chặn", '_chan_giet_ho_so_da_sinh_hoa_don(doc, "Huỷ")' in huy)


@ca("v416 KHÔNG tự huỷ hoá đơn hộ, chỉ chặn và chỉ ra thứ tự đúng")
def _khong_tu_huy_hoa_don():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def _chan_giet_ho_so_da_sinh_hoa_don(", "\ndef ")
	dung("có ném lỗi", "frappe.throw(" in than)
	# Tuyet doi khong duoc goi cancel: huy chung tu da ghi so la dong so cai.
	dung("không gọi cancel", ".cancel(" not in than)
	dung("chỉ ra thứ tự đúng", "huỷ những hoá đơn đó bên Next trước" in than)


# ============================================= 4. trừ tạm ứng và mốc so SePay


@ca("v416 cổng SePay so với số THẬT SỰ chuyển, không so tổng tiền")
def _cong_sepay_so_con_lai():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def danh_dau_da_tra(", "\n@frappe.whitelist()")
	dung("có số phải chuyển", "phai_chuyen = flt(doc.con_lai) or flt(doc.tong_tien)" in than)
	dung("cổng dùng số đó", "duyet_chi.sepay_du(phai_chuyen, da_chi)" in than)
	dung("hết so thẳng tổng tiền", "sepay_du(flt(doc.tong_tien), da_chi)" not in than)


@ca("v416 trừ tạm ứng thì nhắc rõ phần bù trừ 1411 còn phải làm tay")
def _nhac_tam_ung():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def danh_dau_da_tra(", "\n@frappe.whitelist()")
	dung("chỉ nhắc khi có tạm ứng", "if flt(doc.da_tam_ung) > 0:" in than)
	dung("có ghi vết", "_ghi_vet(doc.name, nhac)" in than)
	dung("trả về cho màn hình", '"nhac_tam_ung": nhac' in than)
	dung("nói rõ quỹ 1411", "quỹ 1411" in than)


# ================== 5. nối phiếu nội bộ làm CHỨNG TỪ trên màn có hoá đơn


@ca("v416 màn có hoá đơn nhận de_nghi_chi, và KHÔNG so số tiền với phiếu")
def _noi_phieu_lam_chung_tu():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def tao(ncc=None, hoa_don=None", "\n@frappe.whitelist()")
	dung("đọc de_nghi_chi từ dòng gửi lên", 'x.get("de_nghi_chi")' in than)
	dung("cất vào dòng hồ sơ", '"de_nghi_chi": ma_phieu or None,' in than)
	dung("soi phiếu nhưng bỏ phép so tiền", "_soi_phieu_noi_bo(dong, theo_tien=False)" in than)


@ca("v416 phép soi có công tắc theo_tien, mặc định VẪN so như cũ")
def _cong_tac_theo_tien():
	src = _py("ho_so_tt.py")
	dung("có công tắc", "def _soi_phieu_noi_bo(sach, theo_tien=True):" in src)
	than = _doan(src, "def _soi_phieu_noi_bo(sach, theo_tien=True):", "\ndef ")
	dung("phép so tiền nằm sau công tắc", "if theo_tien and tien_phieu > 0" in than)
	# Hai chot con lai KHONG duoc dinh cong tac: noi trung va chua duyet thi
	# luong nao cung phai chan.
	dung("vẫn chặn nối trùng", "đang nối vào hai khoản trong cùng hồ sơ" in than)
	dung("vẫn chặn phiếu chưa duyệt", "TT_PHIEU_NOI_BO" in than)
	# Luong hoan ung khong hoa don van so tien nhu cu.
	hu = _doan(src, "def tao_hoan_ung(", "\n@frappe.whitelist()")
	dung("luồng không hoá đơn vẫn so tiền", "_soi_phieu_noi_bo(sach)" in hu)


@ca("v416 phiếu nối ở màn có hoá đơn vẫn bị KHOÁ và được kéo tệp sang")
def _khoa_va_dap_tep():
	src = _py("ho_so_tt.py")
	than = _doan(src, "def tao(ncc=None, hoa_don=None", "\n@frappe.whitelist()")
	dung("có khoá phiếu", "_khoa_phieu_noi_bo(doc.name, dong)" in than)
	dung("có kéo tệp", "_dap_tep_phieu_noi_bo(doc)" in than)
	dung("khoá ngay sau khi chèn",
		than.index("doc.insert(ignore_permissions=True)") < than.index("_khoa_phieu_noi_bo(doc.name, dong)"))
	t2 = _doan(src, "def _dap_tep_phieu_noi_bo(doc):", "\ndef ")
	dung("giữ tệp cũ, chỉ thêm vào sau", "moi = cu + [m for m in them if m not in cu]" in t2)


@ca("v416 app gửi de_nghi_chi lên và dọn ô khi bỏ tick hoá đơn")
def _app_gui_va_don():
	src = _js("19-ho-so-tt.js")
	dung("có ô nhớ", "var hsPhieuCua = {};" in src)
	dung("có nút trên dòng", "function hsODongPhieu(maHd)" in src)
	dung("gửi lên máy chủ", "o.de_nghi_chi = hsPhieuCua[m].trim();" in src)
	# Bo tick hoa don ma con giu phieu la khoa nham mot phieu chang cua ai.
	dung("bỏ tick thì gỡ phiếu", "delete hsTaoChon[ma]; delete hsPhieuCua[ma];" in src)
	dung("lập xong thì dọn", "hsPhieuCua = {};" in src)


@ca("v416 nút nối phiếu chỉ hiện ở luồng hoàn ứng và trên dòng đã tick")
def _nut_dung_cho():
	src = _js("19-ho-so-tt.js")
	dung("có điều kiện kép", "(laHU && da ? hsODongPhieu(r.hoa_don) : '')" in src)
	# Bam nut khong duoc lam bo tick chinh hoa don do.
	dung("chặn nổi lên", "e.stopPropagation(); e.preventDefault();" in src)


@ca("v416 patches.txt có dòng đợt này")
def _dang_ky():
	dong = [d.strip() for d in _goc("vagabond/patches.txt").splitlines()]
	dung("có dòng v416", "vagabond.patches.dong_bo_cau_truc #v416" in dong)
	dung("giữ nguyên dòng v414", "vagabond.patches.dong_bo_cau_truc #v414" in dong)

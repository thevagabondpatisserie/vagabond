"""Ca kiểm cho ô "Hoàn ứng vào tài khoản nào" trên MỌI màn hoàn ứng.

Anh Việt 28/08/2026: *"Khi Uyên làm APP hoàn ứng có hoá đơn và APP hoàn ứng
không có hoá đơn, thì bị thiếu chỗ tài khoản chuyển đến, vì 2 cái này đều là
gộp hoá đơn của các NCC rồi cần chuyển là chuyển đến tài khoản của Nguyễn
Hoàng Việt ngân hàng ACB."*

Bốn điều bộ ca này canh:

  1. CẢ HAI màn hoàn ứng đều có ô chọn tài khoản. Trước đó chỉ màn không hoá
     đơn có, còn màn có hoá đơn lặng lẽ lấy tài khoản mặc định của người ứng.
  2. Không có tài khoản mặc định ngầm khi người ứng có từ hai tài khoản. ACB
     đứng trước OCB theo bảng chữ cái, nên "lấy cái đầu tiên" nghĩa là mọi hồ
     sơ ai không để ý đều chảy vào ACB.
  3. Tài khoản phải THUỘC VỀ đúng người được hoàn ứng.
  4. Lựa chọn được LƯU vào ô `tk_nhan`, không tan thành ba chuỗi rời.

Mọi ca chạy trên phép THUẦN: đọc mã nguồn, không cần Frappe, không cần site,
không cần mạng, không cần thư viện requests.
"""

import io
import json
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


def _js(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


def _than(s, dau, cuoi):
	i = s.find(dau)
	if i < 0:
		return ""
	j = s.find(cuoi, i + len(dau))
	return s[i:j if j > i else len(s)]


# ------------------------------------ 1. Cả hai màn hoàn ứng đều có ô chọn


@ca("tk nhan: man hoan ung CO hoa don co o chon tai khoan")
def _co_hoa_don_co_o_chon():
	s = _js("19-ho-so-tt.js")
	t = _than(s, "async function scrHoSoTTTao()", "\nfunction huTong(")
	dung("goi cua tai khoan hoan ung", "vagabond.ho_so_tt.ds_tk_hoan_ung" in t)
	dung("co nhan tren man", "Hoàn ứng vào tài khoản nào" in t)
	dung("co chip chon", "data-hstk=" in t)
	dung("gui tk_hoan len backend", "tk_hoan: laHU ? hsTkHoan" in t)


@ca("tk nhan: man hoan ung KHONG hoa don van giu o chon")
def _khong_hoa_don_giu_o_chon():
	s = _js("19-ho-so-tt.js")
	t = _than(s, "async function scrHoanUngTao()", "async function huLaySepay(")
	dung("goi cua tai khoan hoan ung", "vagabond.ho_so_tt.ds_tk_hoan_ung" in t)
	dung("co nhan tren man", "Hoàn ứng về tài khoản nào" in t)
	dung("gui tk_hoan len backend", "tk_hoan: huTkHoan" in t)


# ---------------------------- 2. Không có tài khoản mặc định ngầm khi có 2


@ca("tk nhan: hai tai khoan tro len thi KHONG tu chon thay nguoi dung")
def _khong_chon_thay():
	s = _js("19-ho-so-tt.js")
	t = _than(s, "async function scrHoanUngTao()", "async function huLaySepay(")
	# Duong cu lay tkHu[0] tuc la ACB, vi ACB dung truoc OCB.
	dung("bo nep lay cai dau bang", "if (!huTkHoan && tkHu.length) huTkHoan = tkHu[0].ma;" not in t)
	dung("chi tu chon khi co dung mot", "tkHu.length === 1" in t)
	t2 = _than(s, "async function scrHoSoTTTao()", "\nfunction huTong(")
	dung("man co hoa don cung vay", "dtk.length === 1" in t2)


@ca("tk nhan: chua chon thi chan CA hai nut, ke ca luu nhap")
def _chan_khi_chua_chon():
	s = _js("19-ho-so-tt.js")
	t = _than(s, "async function scrHoSoTTTao()", "\nfunction huTong(")
	dung("man co hoa don chan", "if (laHU && !hsTkHoan) return baoTin(" in t)
	t2 = _than(s, "async function scrHoanUngTao()", "async function huLaySepay(")
	dung("man khong hoa don chan", "if (!huTkHoan) return baoTin(" in t2)


# ------------------------------- 3. Tài khoản phải của đúng người được hoàn


@ca("tk nhan: danh sach loc theo dung nguoi duoc hoan ung")
def _loc_theo_nguoi():
	s = _doc("ho_so_tt.py")
	t = _than(s, "def ds_tk_hoan_ung(", "\ndef ")
	dung("nhan tham so nguoi", "nguoi=None" in t)
	dung("loc theo chu tai khoan", "_cua_nguoi(b, ma_nguoi)" in t)
	# Nguoi do chua khai tai khoan nao thi lui ve danh sach chung, khong chan.
	dung("khong chan khi chua khai", "doan = 1" in t)
	n = _than(s, "def _cua_nguoi(", "\ndef ")
	dung("chi nhan party la Supplier", '"Supplier"' in n)
	dung("so dung ma nguoi", "== ma_ncc" in n)


@ca("tk nhan: chan tai khoan cua NGUOI KHAC, khong cho chuyen nham tui")
def _chan_tui_nguoi_khac():
	s = _doc("ho_so_tt.py")
	t = _than(s, "def _dat_tk_nhan(", "\ndef ")
	dung("co doi chieu chu tai khoan", "_ncc_cua_tk_hoan(ten)" in t)
	dung("chan khi khac chu", "chu != ma_nguoi" in t)
	dung("bao ro la cua ai", "không phải của người được hoàn ứng" in t)
	# Tai khoan khong co that thi phai bao, khong duoc lang le bo qua.
	dung("chan tai khoan khong co that", 'exists("Bank Account", ten)' in t)


@ca("tk nhan: man hinh doi nguoi ung thi nap lai danh sach tai khoan")
def _doi_nguoi_thi_nap_lai():
	s = _js("19-ho-so-tt.js")
	t = _than(s, "async function scrHoSoTTTao()", "\nfunction huTong(")
	# Giu chip cua nguoi truoc sau khi doi nguoi chinh la duong chuyen nham.
	dung("neo cache vao nguoi dang chon", "hsTkCua !== hsTaoNguoiUng" in t)
	dung("doi nguoi thi bo chip cu", "hsTkCua = hsTaoNguoiUng; hsTkHoan = '';" in t)
	dung("bo nguoi thi don sach", "hsTkDs = null; hsTkCua = ''; hsTkHoan = '';" in t)


# --------------------------------------- 4. Lựa chọn được LƯU, không bốc hơi


@ca("tk nhan: doctype co o tk_nhan kieu Link Bank Account")
def _doctype_co_o():
	p = os.path.join(GOI, "vagabond", "doctype", "vagabond_ho_so_tt", "vagabond_ho_so_tt.json")
	with io.open(p, encoding="utf-8") as f:
		d = json.load(f)
	o = [x for x in d["fields"] if x["fieldname"] == "tk_nhan"]
	la("co dung mot o tk_nhan", len(o), 1)
	la("kieu Link", o[0]["fieldtype"], "Link")
	la("tro vao Bank Account", o[0]["options"], "Bank Account")
	dung("nam trong field_order", "tk_nhan" in d["field_order"])
	# Phai dung ngay tren ba o cu, khong thi mo Desk ra thay hai cho khai
	# tai khoan cach nhau nua man hinh.
	fo = d["field_order"]
	la("dung ngay truoc ten_nhan", fo.index("tk_nhan") + 1, fo.index("ten_nhan"))


@ca("tk nhan: CA HAI cua tao ho so deu ghi lua chon xuong tk_nhan")
def _ca_hai_cua_deu_ghi():
	s = _doc("ho_so_tt.py")
	t1 = _than(s, "def tao(", "\n# ---")
	dung("cua tao nhan tk_hoan", "tk_hoan=None" in t1)
	dung("cua tao ghi xuong tk_nhan", "doc.tk_nhan = _dat_tk_nhan(" in t1)
	t2 = _than(s, "def tao_hoan_ung(", "\n@frappe.whitelist()")
	dung("cua hoan ung ghi xuong tk_nhan", "doc.tk_nhan = _dat_tk_nhan(" in t2)
	# Mot cho duy nhat cho ca hai luong, de hai man khong cu xu khac nhau.
	la("dung chung dung mot ham", s.count("def _dat_tk_nhan("), 1)


@ca("tk nhan: ba o ten - so tk - ngan hang lay tu Bank Account, khong go tay")
def _ba_o_lay_tu_bank_account():
	s = _doc("ho_so_tt.py")
	t = _than(s, "def _dat_tk_nhan(", "\ndef ")
	dung("doc tu Bank Account", "_tk_tu_bank_account(ten)" in t)
	dung("tra ve ma tai khoan de luu", "return ten" in t)


@ca("tk nhan: co cua CHON tai khoan tren ho so da lap, khong chi go tay")
def _cua_chon_tren_ho_so():
	s = _doc("ho_so_tt.py")
	t = _than(s, "def doi_tk_nhan(", "\n# ---")
	dung("dung chung hang rao", "_dat_tk_nhan(doc, tk_hoan, chu)" in t)
	dung("hoan ung soi theo nguoi ung", "doc.nguoi_ung or doc.nha_cung_cap" in t)
	dung("ho so da tra thi khong sua", "TT_DA_TRA" in t)
	dung("ghi vet ai doi", "_ghi_vet(" in t)
	j = _js("19-ho-so-tt.js")
	dung("man hinh co nut chon", "data-hsv=\"chontk\"" in j)
	dung("man hinh goi dung cua", "vagabond.ho_so_tt.doi_tk_nhan" in j)
	# Duong go tay van con cho ho so chua khai Bank Account.
	dung("van giu duong go tay", "vagabond.ho_so_tt.sua_tk_nhan" in j)


@ca("tk nhan: thieu tai khoan thi chan ngay o cua gui di duyet")
def _chan_luc_gui_di_duyet():
	s = _doc("ho_so_tt.py")
	t = _than(s, 'if buoc == "gui_fin":', "elif buoc ==")
	dung("chi chan ho so hoan ung", "(LOAI_HU, LOAI_HU_HD)" in t)
	# Chan theo SO TAI KHOAN chu khong theo link, de ho so cu go tay ba o
	# van di duoc.
	dung("chan theo so tai khoan", 'doc.stk_nhan or ""' in t)
	dung("chi ro nut phai bam", "Chọn TK nhận" in t)

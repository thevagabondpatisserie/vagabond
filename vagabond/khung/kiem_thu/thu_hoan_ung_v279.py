"""Ca kiểm cho vòng sửa v279 của luồng hoàn ứng.

Anh Việt giao 22/08/2026, sau khi dùng thật bản v278:
  1. Thiếu nút xoá dòng, phải viết vào backend cho mọi nơi dùng chung.
  2. Hoàn ứng không hoá đơn không cần chọn NCC, chỉ chọn tài khoản ACB/OCB
     và phải hiện cả số tài khoản.
  3. Xuất bộ hồ sơ lỗi máy chủ 500.
  4. Nút tải bản thể hiện hoá đơn phải nằm ngay cạnh hoá đơn lúc chọn.
  5. Thiếu ô Lấy từ sao kê ACB.
  6. Chặn thiếu chứng từ lúc gửi, ngưỡng miễn trừ 200.000đ.

Mọi ca chạy trên phép THUẦN: không cần Frappe thật, không cần site, không
cần mạng, không cần thư viện requests.
"""

import io
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


# ----------------------------------------------------- Hàng rào chứng từ 200k


@ca("chung tu: khoan duoi 200k KHONG bi doi giay to")
def _duoi_nguong_thi_tha():
	from vagabond import ho_so_tt as hs

	la("nguong dung 200.000", hs.NGUONG_MIEN_CHUNG_TU, 200000.0)
	# Chat deu tay moi khoan thi Uyen phai chup ca hoa don gui xe 5.000d.
	dong = [{"noi_dung": "Gửi xe", "so_tien": 5000, "loai_chung_tu": "", "tep": []}]
	la("khoan 5k qua duoc", hs.thieu_chung_tu(dong, {}), [])
	dong = [{"noi_dung": "Cà phê", "so_tien": 199999, "loai_chung_tu": "", "tep": []}]
	la("khoan 199.999 van qua", hs.thieu_chung_tu(dong, {}), [])


@ca("chung tu: khoan tu 200k tro len phai chon loai chung tu")
def _tu_nguong_phai_khai():
	from vagabond import ho_so_tt as hs

	dong = [{"noi_dung": "Sửa máy", "so_tien": 200000, "loai_chung_tu": "", "tep": []}]
	thieu = hs.thieu_chung_tu(dong, {})
	la("dung mot khoan bi bat", len(thieu), 1)
	la("dung so thu tu", thieu[0]["stt"], 1)
	dung("noi ro chua chon loai", "chưa chọn loại chứng từ" in thieu[0]["vi_sao"])


@ca("chung tu: loai bat buoc tep ma chua dinh thi chan")
def _bat_buoc_tep():
	from vagabond import ho_so_tt as hs

	dm = {"Hoá đơn VAT": {"bat_buoc_tep": 1}, "Bảng kê không hoá đơn": {"bat_buoc_tep": 0}}
	dong = [{"noi_dung": "Mua ly", "so_tien": 500000, "loai_chung_tu": "Hoá đơn VAT", "tep": []}]
	thieu = hs.thieu_chung_tu(dong, dm)
	la("bi chan", len(thieu), 1)
	dung("noi ro thieu tep", "bắt buộc có tệp" in thieu[0]["vi_sao"])
	# Co tep roi thi qua.
	dong[0]["tep"] = ["FILE-1"]
	la("dinh tep xong thi qua", hs.thieu_chung_tu(dong, dm), [])


@ca("chung tu: van con CUA THOAT cho khoan that su khong co giay")
def _cua_thoat():
	from vagabond import ho_so_tt as hs

	# Quy trinh nao phien qua thi nguoi ta tim duong di vong, luc do mat ca
	# nhung khoan dang le chan duoc. Nen phai co duong khai that.
	dm = {"Bảng kê không hoá đơn": {"bat_buoc_tep": 0}}
	dong = [{"noi_dung": "Bồi dưỡng thợ", "so_tien": 900000,
	         "loai_chung_tu": "Bảng kê không hoá đơn", "tep": []}]
	la("loai khong doi tep thi qua", hs.thieu_chung_tu(dong, dm), [])


@ca("chung tu: tep dang chuoi nhieu dong cung doc duoc")
def _tep_dang_chuoi():
	from vagabond import ho_so_tt as hs

	dm = {"Hoá đơn VAT": {"bat_buoc_tep": 1}}
	dong = [{"noi_dung": "Mua ly", "so_tien": 500000,
	         "loai_chung_tu": "Hoá đơn VAT", "tep": "FILE-1\nFILE-2"}]
	la("chuoi nhieu dong van tinh la co tep", hs.thieu_chung_tu(dong, dm), [])


@ca("chung tu: chi chan luc GUI, luu nhap thi khong")
def _chi_chan_luc_gui():
	s = _doc("ho_so_tt.py")
	i = s.find("def tao_hoan_ung(")
	j = s.find("\ndef ", i + 10)
	than = s[i:j]
	# Nhap la cho lam do. Bat du giay to ngay tu dong dau thi khong ai luu
	# nhap duoc nua, ma nhap chinh la thu giu cho nguoi ta khoi phai lam mot
	# leo trong mot lan ngoi.
	dung("co chan", "_chan_thieu_chung_tu(sach)" in than)
	k = than.find("_chan_thieu_chung_tu(sach)")
	truoc = than[max(0, k - 260):k]
	dung("chi chan khi gui_luon", "if cint(gui_luon):" in truoc)


# ------------------------------------------------------------ Xoá một dòng


@ca("xoa dong: chi xoa duoc khi ho so CHUA qua cua duyet nao")
def _chi_xoa_khi_con_sua_duoc():
	from vagabond import ho_so_tt as hs

	# Ho so da gui ke toan ma nguoi lap van rut dong ra duoc thi con so chi
	# Dung nhin luc duyet khong con la con so duoc duyet.
	dung("nhap thi sua duoc", hs.TT_NHAP in hs.TT_SUA_DUOC_RUOT)
	dung("bi tra lai thi sua duoc", hs.TT_TU_CHOI in hs.TT_SUA_DUOC_RUOT)
	dung("cho ke toan thi KHONG", hs.TT_CHO_FIN not in hs.TT_SUA_DUOC_RUOT)
	dung("cho giam doc thi KHONG", hs.TT_CHO_GD not in hs.TT_SUA_DUOC_RUOT)
	dung("da duyet thi KHONG", hs.TT_DA_DUYET not in hs.TT_SUA_DUOC_RUOT)
	dung("da thanh toan thi KHONG", hs.TT_DA_TRA not in hs.TT_SUA_DUOC_RUOT)


@ca("xoa dong: KHONG cho xoa dong cuoi cung, khong de lai ho so rong")
def _khong_xoa_het_ruot():
	s = _doc("ho_so_tt.py")
	i = s.find("def xoa_dong(")
	than = s[i:i + 2600]
	dung("chan khi chi con mot dong", "if len(doc.dong) <= 1:" in than)
	dung("chi duong huy ca ho so", "huỷ cả hồ sơ" in than)


@ca("xoa dong: TRA LAI phieu noi bo da noi, khong de phieu ket vinh vien")
def _tra_lai_phieu():
	s = _doc("ho_so_tt.py")
	i = s.find("def xoa_dong(")
	than = s[i:i + 2600]
	dung("goi tra phieu", "_tra_phieu_noi_bo(phieu, name)" in than)
	j = s.find("def _tra_phieu_noi_bo(")
	nen = s[j:j + 1200]
	# Phai xoa dung moi phieu cua CHINH ho so nay, khong duoc go phieu ma ho
	# so khac dang giu.
	dung("chi go khi dung ho so", 'get_value(DNC, ma_phieu, "ho_so_tt") == ten_ho_so' in nen)


@ca("xoa dong: KHONG xoa tep khoi may chu")
def _khong_xoa_tep():
	s = _doc("ho_so_tt.py")
	i = s.find("def xoa_dong(")
	than = s[i:i + 2600]
	# Bam nham mot cai la mat anh chung tu khong lay lai duoc.
	dung("noi ro khong xoa tep", "KHÔNG xoá tệp khỏi máy chủ" in than)
	dung("khong goi delete", "frappe.delete_doc" not in than)


@ca("xoa dong: man hinh co nut xoa o CA hai cho, dang lap va da lap")
def _man_hinh_co_nut():
	s = _js("19-ho-so-tt.js")
	dung("co o xoa tren bang dang lap", "function huOXoa(" in s)
	dung("co ham xoa dong dang lap", "async function huXoaDong(" in s)
	dung("co ham xoa dong ho so da lap", "async function hsXoaDongHoSo(" in s)
	dung("goi dung cua backend", "vagabond.ho_so_tt.xoa_dong" in s)
	# Hoi lai truoc khi xoa: thao tac nay khong lui duoc, ma ngon tay tren
	# dien thoai cham nham rat de.
	i = s.find("async function huXoaDong(")
	dung("co hoi lai", "await xacNhan(" in s[i:i + 1200])


# ------------------------------- Hoàn ứng về tài khoản, không phải về NCC


@ca("hoan ung: man hinh chon TAI KHOAN chu khong con chon nha cung cap")
def _chon_tai_khoan():
	s = _js("19-ho-so-tt.js")
	i = s.find("async function scrHoanUngTao()")
	j = s.find("async function huLaySepay(")
	than = s[i:j if j > i else i + 9000]
	dung("goi cua tai khoan hoan ung", "vagabond.ho_so_tt.ds_tk_hoan_ung" in than)
	dung("nhan dung y nghia", "Hoàn ứng về tài khoản nào" in than)
	# Danh sach nha cung cap phai bien mat khoi man nay.
	dung("khong con goi ds_nguoi_ung", "ds_nguoi_ung" not in than)
	dung("khong con chip nha cung cap", "data-hun=" not in than)


@ca("hoan ung: chip tai khoan hien CA SO TAI KHOAN, khong chi ten ngan hang")
def _hien_so_tai_khoan():
	s = _doc("ho_so_tt.py")
	i = s.find("def ds_tk_hoan_ung(")
	than = s[i:i + 2600]
	# Hai tai khoan de lan khi chi nhin ten ngan hang.
	dung("tra ve so tai khoan", '"so_tk":' in than)
	dung("nhan gop ten va so", '" · " + b["bank_account_no"]' in than)


@ca("hoan ung: van suy ra ma NCC de treo cong no dung cho")
def _van_treo_cong_no():
	s = _doc("ho_so_tt.py")
	i = s.find("def tao_hoan_ung(")
	j = s.find("\ndef ", i + 10)
	than = s[i:j]
	dung("suy ma NCC tu tai khoan", "_ncc_cua_tk_hoan(tk_hoan)" in than)
	# Tai khoan chua gan Party thi phai chi ro cho phai khai, khong duoc im.
	dung("chi ro cho phai khai", "điền ô Party" in than)
	k = s.find("def _ncc_cua_tk_hoan(")
	nen = s[k:k + 900]
	dung("chi nhan party la Supplier", '"Supplier"' in nen)


@ca("hoan ung: danh sach rong thi bay tam tai khoan cong ty, khong chan nguoi ta")
def _rong_thi_doan():
	s = _doc("ho_so_tt.py")
	i = s.find("def ds_tk_hoan_ung(")
	than = s[i:i + 2600]
	# Tha hien thua vai dong con hon hien bang trong va chan nguoi ta lap
	# ho so.
	dung("co co bao la ban doan", '"doan": doan' in than)
	dung("lui ve tai khoan cong ty", "doan = 1" in than)


# ---------------------------------------------------- Sao kê nhiều ngân hàng


@ca("sao ke: doc duoc CA ACB lan OCB, khong dinh cung mot tai khoan")
def _sao_ke_hai_ngan_hang():
	s = _doc("ho_so_tt.py")
	i = s.find("def sepay_ocb(")
	than = s[i:i + 2600]
	dung("nhan tham so tai khoan", "tai_khoan=None" in than)
	dung("bo trong thi giu nep cu", '(tai_khoan or "").strip() or _bank_account_quy()' in than)
	dung("tra ve ten ngan hang cho man hinh", '"ngan_hang":' in than)
	s2 = _js("19-ho-so-tt.js")
	# Moi tai khoan mot nut, sinh tu danh sach chu khong go cung "OCB".
	dung("sinh nut theo tung tai khoan", "data-husk=" in s2)
	dung("nut mang ten ngan hang that", "Lấy từ sao kê ' +" in s2)
	dung("khong go cung ten OCB nua", "Lấy từ sao kê OCB" not in s2)


# ------------------------------ Bản thể hiện hoá đơn, tải ngay lúc chọn


@ca("ban the hien: dinh vao HOA DON chu khong vao ho so")
def _dinh_vao_hoa_don():
	s = _doc("ho_so_tt.py")
	i = s.find("def dinh_tep_hoa_don(")
	than = s[i:i + 2400]
	# Dinh vao ho so thi lan sau hoa don ay nam trong ho so khac lai phai
	# tai len lan nua, va ai mo hoa don tren Next cung khong thay dau.
	dung("tro ve Purchase Invoice", '"attached_to_doctype": "Purchase Invoice"' in than)
	dung("de rieng tu", '"is_private": 1' in than)
	dung("chan hoa don khong co that", 'frappe.db.exists("Purchase Invoice", hoa_don)' in than)


@ca("ban the hien: nut nam ngay canh hoa don luc chon, kem so ban da co")
def _nut_canh_hoa_don():
	s = _js("19-ho-so-tt.js")
	dung("co nut tren tung dong", "function hsONutBanTheHien(" in s)
	dung("co ham tai len", "async function hsTaiBanTheHien(" in s)
	dung("goi dung cua backend", "vagabond.ho_so_tt.dinh_tep_hoa_don" in s)
	# Bam nut khong duoc lam tick chon hoa don nhay theo.
	i = s.find("data-hsbth]')")
	dung("chan noi len", "e.stopPropagation()" in s[max(0, i - 300):i + 400])


@ca("ban the hien: dem MOT LUOT ca danh sach, khong hoi tung dong")
def _dem_mot_luot():
	s = _doc("ho_so_tt.py")
	i = s.find("def dem_tep_hoa_don(")
	than = s[i:i + 1800]
	dung("nhan ca danh sach", '"attached_to_name": ["in", ds]' in than)
	s2 = _js("19-ho-so-tt.js")
	j = s2.find("async function hsDemBanTheHien(")
	nen = s2[j:j + 1400]
	# Man chon hoa don bay vai chuc dong; hoi tung dong la vai chuc luot mang.
	dung("chi hoi ma chua biet", "HS_DEM_BTH[m] === undefined" in nen)
	# Ve lai vo co la cuop mat o nguoi ta dang go.
	dung("chi ve lai khi co so moi", "if (doi) veLaiNutBanTheHien();" in nen)


# ------------------------------ v280: nhom tai khoan tam ung la 141, khong phai 1411


@ca("tam ung: hoi ca NHOM 141 nen ACB o so cai 1412 khong bi rot")
def _nhom_tam_ung():
	s = _doc("ho_so_tt.py")
	# Ngay 22/08/2026 v279 len that: bang chon tai khoan hoan ung chi hien
	# moi OCB. Ly do that: OCB o so cai 1411, ACB o 1412, ma _tk_ung hoi
	# dung chuoi "1411". Hoi ca nhom 141 thi ca hai deu vao.
	dung("co hang so nhom", 'TK_NHOM_TAM_UNG = "141"' in s)
	dung("van giu hang so OCB rieng", 'TK_QUY_TAM_UNG = "1411"' in s)

	i = s.find("def _tk_ung(")
	than = s[i:i + 400]
	dung("_tk_ung hoi ca nhom", "TK_NHOM_TAM_UNG" in than)
	la("_tk_ung khong con hoi rieng 1411", "TK_QUY_TAM_UNG" in than, False)


@ca("tam ung: bang TK cong ty tru ca nhom 141 ra, khong chi tru 1411")
def _tk_cong_ty_tru_ca_nhom():
	s = _doc("ho_so_tt.py")
	i = s.find("def ds_tk_cong_ty(")
	than = s[i:i + 2000]
	# Neu chi tru 1411 thi tai khoan tam ung ACB se hien nham trong bang
	# "tai khoan cong ty", ke toan chon vao la hach toan sai quy.
	dung("tru ca nhom", "TK_NHOM_TAM_UNG" in than)


@ca("tam ung: tai khoan MAC DINH tra ve DUNG MOT cai, khong doc so lieu so hai")
def _mac_dinh_van_1411():
	"""Luat nay doi ngay 28/08/2026, ghi lai vi sao.

	Ban cu chot cung 1411 va CAM hoi ca nhom 141, ly do: hoi ca nhom thi ham
	luc tra ACB luc tra OCB tuy thu tu ban ghi, sao ke doc ra so hai.

	Anh Viet bo tai khoan OCB ngay 28/08/2026. Giu nguyen luat cu thi man
	hinh doi mai mot sao ke khong bao gio ve nua, vi 1411 la chinh cai vua
	tat. Nay cho hoi ca nhom 141 NHUNG chi lay tai khoan CON BAT - do la
	cach moi de bao dam van chi co mot cai, dung cai lo ma luat cu lo.
	"""
	s = _doc("ho_so_tt.py")
	i = s.find("def _bank_account_quy(")
	than = s[i:i + 1400]
	dung("van uu tien 1411 khi no con bat", "TK_QUY_TAM_UNG" in than)
	dung("hoi ca nhom 141", "TK_NHOM_TAM_UNG" in than)
	# Day moi la cai chan viec doc ra so hai: tai khoan da tat khong duoc tra.
	dung("chi lay tai khoan con bat", '"disabled": 0' in than)
	dung("co chot thu tu", "order_by" in than)

"""Ca kiểm cho uỷ nhiệm chi và tài khoản chi của hồ sơ thanh toán.

Chị Dung 28/08/2026 bấm "Ghi nhận đã thanh toán" trên hồ sơ APP.26.08.018
và máy trả về "Tỷ giá nguồn là bắt buộc". Gốc là bút toán chi tiền không
biết tiền đi ra từ tài khoản nào.

Anh Việt cùng ngày: *"Em thêm 1 nút đính kèm UNC dùm anh để chị Dung đính
kèm UNC lên các APP rồi mới ghi nhận được thanh toán của TẤT CẢ CÁC APP."*

Bốn nhóm ca:

  1. Phép thuần: tách và gộp mã tệp, chọn tài khoản chi, tỷ giá, kiểm tệp.
  2. Hàng rào uỷ nhiệm chi có mặt đúng chỗ trong luồng ghi nhận thanh toán.
  3. Bút toán chi luôn có tài khoản nguồn và tỷ giá, và uỷ nhiệm chi được
     chép sang bút toán TRƯỚC khi ghi sổ.
  4. Thư báo nhà cung cấp: gửi từ hộp thu mua, gửi bản sao cho kế toán,
     đính uỷ nhiệm chi, và có khối đề nghị đối chiếu công nợ.

Mọi ca chạy trên phép THUẦN hoặc đọc mã nguồn: không cần Frappe, không
cần site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")

MOC_FRAPPE = "# ------------------------------------------------------- phần cần Frappe"


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


def _js(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


def _than_ham(s, dau):
	"""Cắt từ dòng def tới hết tệp.

	KHÔNG cắt ở dòng trống đầu tiên: thân hàm nào cũng có dòng trống, cắt
	như vậy là chỉ soi được vài dòng đầu rồi tưởng là đã soi hết.
	"""
	i = s.find(dau)
	return s[i:] if i >= 0 else ""


# ---------------------------------------------------- 1. Phép thuần


@ca("unc: tach va gop ma tep nhan ca ba dang nguoi ta ghi")
def _tach_gop():
	from vagabond import tra_tien_app as t

	la("xuong dong", t.tach_ma("a\nb\nc"), ["a", "b", "c"])
	la("dau phay", t.tach_ma("a,b"), ["a", "b"])
	la("cham phay", t.tach_ma("a;b"), ["a", "b"])
	la("bo trung", t.tach_ma("a\na\nb"), ["a", "b"])
	la("bo khoang trang", t.tach_ma("  a  \n\n b "), ["a", "b"])
	la("rong", t.tach_ma(None), [])
	la("gop lai", t.gop_ma(["a", "b", "a", "", None]), "a\nb")
	la("di roi ve", t.tach_ma(t.gop_ma(["x", "y"])), ["x", "y"])


@ca("unc: du_unc chi dung khi co it nhat mot to")
def _du():
	from vagabond import tra_tien_app as t

	la("khong to nao", t.du_unc(0), False)
	la("mot to", t.du_unc(1), True)
	la("nhieu to", t.du_unc(5), True)
	la("None", t.du_unc(None), False)
	la("chuoi rac", t.du_unc("x"), False)


@ca("tk chi: uu tien tai khoan tien gui ngan hang 112x")
def _chon_tk():
	from vagabond import tra_tien_app as t

	la(
		"112 thang 1411",
		t.chon_tk_ngan_hang(["1411 - Tạm ứng - TV", "11211 - Tiền gửi MB Bank - TV"]),
		"11211 - Tiền gửi MB Bank - TV",
	)
	la("khong co 112 thi lay cai dau", t.chon_tk_ngan_hang(["1411 - Tạm ứng - TV"]), "1411 - Tạm ứng - TV")
	la("rong thi rong", t.chon_tk_ngan_hang([]), "")
	la("bo dong rong", t.chon_tk_ngan_hang(["", None, "1121 - x"]), "1121 - x")


@ca("tk chi: ty gia cung loai tien la 1, khac loai tien KHONG doan bua")
def _ty_gia():
	from vagabond import tra_tien_app as t

	la("cung VND", t.ty_gia_chi("VND", "VND"), 1.0)
	la("khong phan biet hoa thuong", t.ty_gia_chi("vnd", "VND"), 1.0)
	la("khac loai tien", t.ty_gia_chi("USD", "VND"), 0.0)
	la("thieu mot ve", t.ty_gia_chi("", "VND"), 0.0)
	la("thieu ca hai", t.ty_gia_chi(None, None), 0.0)


@ca("unc: kiem tep bat tep rong va tep qua nang")
def _kiem_tep():
	from vagabond import tra_tien_app as t

	la("tep tot", t.kiem_tep("unc.pdf", 200000), "")
	dung("khong ten", "chưa có tên" in t.kiem_tep("", 100))
	dung("tep rong", "rỗng" in t.kiem_tep("unc.pdf", 0))
	dung("qua nang", "quá 12 MB" in t.kiem_tep("unc.pdf", 13 * 1024 * 1024))
	la("dung nguong thi van nhan", t.kiem_tep("unc.pdf", 12 * 1024 * 1024), "")


@ca("unc: cau bao thieu UNC noi ra viec phai lam, khong noi ten truong")
def _cau_bao():
	from vagabond import tra_tien_app as t

	c = t.loi_thieu_unc("APP.26.08.018")
	dung("co ma ho so", "APP.26.08.018" in c)
	dung("chi cho bam", "Đính kèm UNC" in c)
	dung("noi ro SePay khong thay duoc", "SePay" in c)
	for cam in ("unc_tep", "docstatus", "Payment Entry", "paid_from"):
		dung("khong lo ten ky thuat %s" % cam, cam not in c)

	k = t.loi_khong_ro_tk("The Vagabond")
	dung("co ten cong ty", "The Vagabond" in k)
	dung("khong lo ten truong", "default_bank_account" not in k)


@ca("tep tra_tien_app: phan thuan KHONG cham Frappe")
def _thuan_that():
	s = _doc("tra_tien_app.py")
	dung("co moc chia hai phan", MOC_FRAPPE in s)
	than = s.split(MOC_FRAPPE)[0]
	for cam in ("import frappe", "frappe.", "requests"):
		dung("phan thuan khong co %s" % cam, cam not in than)


# ------------------------------------- 2. Hàng rào uỷ nhiệm chi đúng chỗ


@ca("hang rao: ghi nhan thanh toan hoi UNC truoc khi dung but toan")
def _chan_truoc():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def danh_dau_da_tra(")
	i_chan = than.find("loi_thieu_unc")
	i_but = than.find("_tao_but_toan(")
	dung("co hang rao UNC", i_chan > 0)
	dung("co dung but toan", i_but > 0)
	dung("chan TRUOC khi dung but toan", i_chan < i_but)


@ca("hang rao: ap cho MOI loai ho so, khong loc theo loai")
def _moi_loai():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def danh_dau_da_tra(")
	khuc = than[: than.find("_tao_but_toan(")]
	for loai in ("LOAI_NCC", "LOAI_HU", "LOAI_TKCT"):
		dung("khong loc theo %s truoc hang rao" % loai, ("doc.loai" not in khuc) or (loai not in khuc))


@ca("hang rao: go UNC ra duoc truoc khi tra, KHONG go duoc sau khi tra")
def _go_duoc():
	from vagabond import tra_tien_app as t

	dung("con nhap thi go duoc", "Nhap" in t.TT_GO_DUOC_UNC)
	dung("cho ke toan thi go duoc", "Cho ke toan" in t.TT_GO_DUOC_UNC)
	dung("da duyet thi van go duoc", "Da duyet" in t.TT_GO_DUOC_UNC)
	dung("DA THANH TOAN thi khong go duoc", "Da thanh toan" not in t.TT_GO_DUOC_UNC)
	dung("huy thi khong go duoc", "Huy" not in t.TT_GO_DUOC_UNC)


@ca("hang rao: go UNC la go lien ket, KHONG xoa tep khoi may chu")
def _khong_xoa():
	s = _doc("tra_tien_app.py")
	than = _than_ham(s, "def go_unc(")
	dung("khong xoa File", "delete_doc" not in than and "db.delete" not in than)
	dung("chi go lien ket", "attached_to_doctype" in than)


# --------------------------------- 3. Bút toán chi có tài khoản và tỷ giá


@ca("but toan: luon dien tai khoan nguon, khong con phu thuoc loai ho so")
def _paid_from():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def _tao_but_toan(")
	khuc = than[: than.find("def _tao_but_toan_tkct")]
	dung("goi ham suy ra tai khoan chi", "tk_tien_chi(" in khuc)
	dung("dien paid_from", "pe.paid_from = tk_nh" in khuc)
	dung("khong ro thi dung lai", "loi_khong_ro_tk" in khuc)
	# Cai bay cu: chi dien paid_from cho rieng loai TK cong ty.
	dung(
		"khong con dieu kien chi loai TK cong ty moi dien",
		"if (doc.loai or LOAI_NCC) == LOAI_TKCT and doc.tk_chi:" not in khuc,
	)


@ca("but toan: ty gia phai co, va khong duoc dat bua khi khac loai tien")
def _ty_gia_but_toan():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def _tao_but_toan(")
	khuc = than[: than.find("def _tao_but_toan_tkct")]
	dung("co dat ty gia nguon", "source_exchange_rate" in khuc)
	dung("dat qua phep thuan", "ty_gia_chi(" in khuc)
	i_dat = khuc.find("pe.source_exchange_rate = tg")
	i_chan = khuc.find("if not tg:")
	dung("chan truoc khi dat", 0 < i_chan < i_dat)


@ca("but toan: chep UNC sang but toan TRUOC khi ghi so")
def _chep_truoc_ghi_so():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def _tao_but_toan(")
	khuc = than[: than.find("def _tao_but_toan_tkct")]
	i_chep = khuc.find("chep_unc(")
	i_nop = khuc.find("pe.insert(")
	i_so = khuc.find("pe.submit()")
	dung("co chep UNC", i_chep > 0)
	dung("chep sau khi but toan co ten", i_nop < i_chep)
	dung("chep TRUOC khi ghi so", i_chep < i_so)

	tkct = _than_ham(s, "def _tao_but_toan_tkct(")
	j_chep = tkct.find("chep_unc(")
	j_so = tkct.find("je.submit()")
	dung("luong TK cong ty cung chep", j_chep > 0)
	dung("cung chep truoc khi ghi so", j_chep < j_so)


@ca("chep UNC: tro cung duong dan, khong tai lai noi dung tep")
def _chep_tro_duong():
	s = _doc("tra_tien_app.py")
	than = _than_ham(s, "def chep_unc(")
	dung("dung file_url", "file_url" in than)
	dung("khong doc noi dung tep", "get_content" not in than)
	dung("chan chep hai lan", "frappe.db.exists" in than)


@ca("tk chi: nam duong, xet tu cu the toi chung")
def _nam_duong():
	s = _doc("tra_tien_app.py")
	than = _than_ham(s, "def tk_tien_chi(")
	khuc = than[: than.find("def _bank_account_cua")]
	thu_tu = [
		khuc.find("Bank Account\", ten_ba"),
		khuc.find("Mode of Payment Account"),
		khuc.find("default_bank_account"),
		khuc.find("is_company_account"),
		khuc.find("default_cash_account"),
	]
	for i, v in enumerate(thu_tu):
		dung("duong %d co mat" % (i + 1), v > 0)
	la("dung thu tu tu cu the toi chung", thu_tu, sorted(thu_tu))


# ------------------------------------------- 4. Thư báo nhà cung cấp


@ca("thu bao: gui tu hop thu thu mua, gui ban sao cho ke toan")
def _hop_thu():
	s = _doc("ho_so_tt.py")
	dung("khai hop thu thu mua", 'EMAIL_THU_MUA = "purchasing@thevagabondpatisserie.com"' in s)
	dung("khai hop thu ke toan", 'EMAIL_KE_TOAN = "account@thevagabondpatisserie.com"' in s)
	than = _than_ham(s, "def gui_email_ncc(")
	khuc = than[: than.find("def _tep_dinh_thu")]
	dung("gui tu thu mua", "sender=EMAIL_THU_MUA" in khuc)
	dung("gui ban sao ke toan", "EMAIL_KE_TOAN" in khuc)
	dung("khong con gui tu hop erp", "erp@thevagabondpatisserie.com" not in khuc)


@ca("thu bao: gui thu nghiem thi KHONG lam phien ke toan va khong danh dau")
def _thu_nghiem():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def gui_email_ncc(")
	khuc = than[: than.find("def _tep_dinh_thu")]
	dung("co duong gui thu", "thu_nghiem" in khuc)
	dung("gui thu thi khong cc ai", "cc=[] if thu else [EMAIL_KE_TOAN]" in khuc)
	i_thu = khuc.find("if thu:")
	i_dau = khuc.find('doc.db_set("email_da_gui"')
	dung("thoat truoc khi danh dau da gui", 0 < i_thu < i_dau)
	dung("tieu de mang chu gui thu", '"[GỬI THỬ] " if thu else ""' in khuc)


@ca("thu bao: gui thu xem duoc mat la thu TRUOC khi ho so da tra")
def _thu_truoc_khi_tra():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def gui_email_ncc(")
	khuc = than[: than.find("def _tep_dinh_thu")]
	dung(
		"khong chan gui thu boi trang thai",
		"cint(gui_that) and not cint(thu_nghiem)" in khuc,
	)
	# Gui THAT thi van phai doi ho so da tra, khong duoc noi long.
	dung("gui that van doi da tra", "doc.trang_thai != TT_DA_TRA" in khuc)


@ca("danh sach: bay co thieu uy nhiem chi ngay tren dong ho so")
def _bay_thieu_unc():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def danh_sach(")
	khuc = than[: than.find("def _truong_hddt_pi")]
	dung("doc o luu UNC", '"unc_tep"' in khuc)
	dung("tinh co_unc", 'o["co_unc"]' in khuc)

	j = _js("19-ho-so-tt.js")
	dung("man hinh doc co_unc", "r.co_unc" in j)
	dung("chi bay khi da duyet", "r.trang_thai === 'Da duyet' && !r.co_unc" in j)


@ca("man ho so: nut gui thu dung duoc o moi trang thai cua ho so NCC")
def _nut_gui_thu():
	j = _js("19-ho-so-tt.js")
	dung("co nut gui thu", "data-hsv=\"guithuthu\"" in j)
	dung("truyen co gui thu", "thu_nghiem: 1" in j)
	dung("nut gui that chi hien khi da tra", "daTra ? '<button class=\"btn\" data-hsv=\"guithu\"" in j)


@ca("thu bao: dinh uy nhiem chi bang NOI DUNG chu khong bang duong dan")
def _dinh_thu():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def _tep_dinh_thu(")
	khuc = than[: than.find("def _thu_html")]
	dung("doc noi dung tep", "get_content()" in khuc)
	dung("khong gui duong dan", "file_url" not in khuc)
	dung("hong mot tep khong lam hong ca thu", "log_error" in khuc)


@ca("thu bao: co khoi de nghi doi chieu cong no, co moc thoi gian")
def _doi_chieu():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def _o_doi_chieu(")
	khuc = than[: than.find("def _nut_doi_chieu")]
	dung("co tieu de khoi", "Đề nghị đối chiếu công nợ" in khuc)
	dung("hoi tien da ve chua", "về tài khoản" in khuc)
	dung("hoi cong no con lai", "còn lại bao nhiêu" in khuc)
	dung("co moc thoi gian", "05 ngày làm việc" in khuc)


@ca("thu bao: mau robin egg lay tu khung thu chung, khong go cung ma mau")
def _mau():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def _thu_html(")
	khuc = than[: than.find("def _o_doi_chieu")]
	dung("lay mau tu nhan_su", "from vagabond.nhan_su import XANH" in khuc)
	dung("truyen mau vao khoi doi chieu", "_o_doi_chieu(XANH, XANH_DAM)" in khuc)


@ca("thu bao: tu gui ngay sau khi ghi nhan, va nuot loi de khong hong ho so")
def _tu_gui():
	s = _doc("ho_so_tt.py")
	than = _than_ham(s, "def _tu_gui_thu_bao(")
	khuc = than[: than.find("def _tao_but_toan(")]
	dung("ho so hoan ung thi khong gui", "LOAI_HU" in khuc)
	dung("thieu email thi noi ro", "chưa có email" in khuc)
	dung("nuot loi", "except Exception" in khuc)
	dung("ghi nhat ky khi hong", "log_error" in khuc)

	tra = _than_ham(s, "def danh_dau_da_tra(")
	dung("goi sau khi da luu ho so", "_tu_gui_thu_bao(doc, gui_thu)" in tra)


# ------------------------------------------------- 5. Màn hình hồ sơ


@ca("man ho so: co nut dinh kem UNC va khoi hien cac to da dinh")
def _man_hinh():
	j = _js("19-ho-so-tt.js")
	dung("co nut", "data-hsv=\"dinhunc\"" in j)
	dung("nhan nut tieng Viet", "Đính kèm uỷ nhiệm chi" in j)
	dung("goi dung cua ngo", "vagabond.tra_tien_app.dinh_unc" in j)
	dung("co duong go", "vagabond.tra_tien_app.go_unc" in j)
	dung("nhac khi chua co to nao", "Chưa có uỷ nhiệm chi" in j)


@ca("man ho so: UNC khong hien hai lan o khoi tep dinh kem chung")
def _khong_trung():
	j = _js("19-ho-so-tt.js")
	dung("co loc trung", "uncMa[f.file]" in j)
	dung("dung ban da loc de ve", "tepChung.map(" in j)


@ca("man ho so: bao ro khi thu bao tu gui khong di duoc")
def _bao_thu():
	j = _js("19-ho-so-tt.js")
	dung("doc ket qua thu", "kq2.thu" in j)
	dung("gui duoc thi bao", "Đã gửi thư báo" in j)
	dung("khong gui duoc thi noi vi sao", "th.vi_sao" in j)


@ca("cua ngo: bon ham mo ra ngoai cua tra_tien_app deu da ghi danh")
def _cua_ngo():
	from vagabond.khung.kiem_thu.thu_cua_ngo import CUA_NGO

	la(
		"dung bon ten",
		sorted(CUA_NGO.get("tra_tien_app.py") or []),
		["dinh_unc", "ds_unc", "go_unc", "soat_tk_chi"],
	)

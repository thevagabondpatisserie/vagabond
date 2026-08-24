"""QT-31 / SKILL_BANK_ROUTING: ô ngân hàng phải là ô chọn, không được là ô gõ.

Anh Việt chốt 23/08/2026 sau khi cùng một lỗi quay lại lần thứ hai:

  17/08/2026  màn hoàn tiền, gõ "MB"          -> Không tìm thấy Ngan hang: MB
  22/08/2026  màn đơn đã huỷ, gõ "VietinBank" -> Không tìm thấy Ngan hang: VietinBank

Gốc chung: trường `ngan_hang` là ô Link trỏ vào doctype Bank, mà tên đầy đủ
trong Bank là "VIETINBANK - Ngân hàng TMCP Công thương Việt Nam". Người ta gõ
tên thương mại, Frappe đòi tên đầy đủ.

Ca kiểm ở đây canh cả ba mặt:

  1. Hàm khớp tên chạy đúng trên chính 581 dòng danh mục thật.
  2. Máy chủ chuẩn hoá TRƯỚC khi ghi, không tin chuỗi màn gửi xuống.
  3. Màn hình không dựng lại một ô nhập tự do cho ngân hàng.

Mặt thứ ba là mặt đáng giá nhất: hai mặt kia sửa xong là hết lỗi hôm nay,
còn mặt này mới chặn được lỗi quay lại lần thứ ba.

Mọi ca chạy trên phép THUẦN: không cần Frappe, không cần site, không cần
mạng, không cần thư viện requests. Cố ý KHÔNG import vagabond.ngan_hang, vì
tệp đó có `import frappe` ở đầu mà máy chạy CI thì tay không - đọc mã nguồn
rồi chạy đúng ba khối thuần là đủ.
"""

import io
import json
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


def _js(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


def _danh_muc():
	with io.open(os.path.join(GOI, "du_lieu", "napas.json"), encoding="utf-8") as f:
		return [(str(x[0]).strip(), str(x[1]).strip()) for x in json.load(f) if x and x[0]]


def _khop():
	"""Nạp hàm thuần khop_ten mà không kéo theo Frappe."""
	src = _doc("ngan_hang.py")
	ns = {}
	for mau in (
		r"^BI_DANH = \{.*?^\}",
		r"^def _khong_dau\(s\):.*?(?=^\S|\Z)",
		r"^def khop_ten\(tu_khoa, danh_muc\):.*?(?=^def |\Z)",
	):
		m = re.search(mau, src, re.S | re.M)
		if not m:
			raise AssertionError("khong tach duoc khoi %r trong ngan_hang.py" % mau)
		exec(compile(m.group(0), "ngan_hang.py", "exec"), ns)
	return ns["khop_ten"]


# ------------------------------ Tầng phép thuần


@ca("khop ten: go 'VietinBank' ra dung ten day du, dung ca lam ket phieu")
def _vietinbank():
	k = _khop()
	ds = _danh_muc()
	r = k("VietinBank", ds)
	# Chinh chuoi nay lam quan ly khong gui duyet duoc ngay 22/08/2026.
	dung("ra dung mot ten", r["ten"] == "VIETINBANK - Ngân hàng TMCP Công thương Việt Nam")
	dung("khop bang ma", r["cach"] == "ma ngan hang")
	for t in ("vietinbank", "VIETINBANK", "VIETINBANK - Ngân hàng TMCP Công thương Việt Nam"):
		la("go %r cung ra the" % t, k(t, ds)["ten"], r["ten"])


@ca("khop ten: ma, ten thuong mai va go khong dau deu ra dung ngan hang")
def _ba_duong():
	k = _khop()
	ds = _danh_muc()
	la("ma MB", k("MB", ds)["ten"], "MB - Ngân hàng TMCP Quân đội")
	la("ten thuong mai", k("Vietcombank", ds)["ten"], "VCB - Ngân hàng TMCP Ngoại thương Việt Nam")
	# Nhan vien quay go nhanh tren dien thoai, bat go dung dau la bat go lai.
	la("go khong dau", k("quan doi", ds)["ten"], "MB - Ngân hàng TMCP Quân đội")
	la("go co dau", k("Quân đội", ds)["ten"], "MB - Ngân hàng TMCP Quân đội")


@ca("khop ten: thu MA truoc roi moi do chuoi, dao thu tu la chon nham")
def _thu_tu():
	k = _khop()
	ds = _danh_muc()
	# Chuoi "mb" nam trong ten nhieu ngan hang khac. Neu do chuoi chay truoc
	# thi "MB" se dinh vao mot ngan hang khong phai Quan doi.
	do_chuoi = [t for t, _ in ds if "mb" in t.lower()]
	dung("qua mot ngan hang chua chuoi mb", len(do_chuoi) > 1)
	la("van ra Quan doi", k("MB", ds)["ten"], "MB - Ngân hàng TMCP Quân đội")


@ca("khop ten: khong chac thi TRA GOI Y chu khong doan bua")
def _khong_doan_bua():
	k = _khop()
	ds = _danh_muc()
	# Mot ma nhieu chi nhanh (KBNN, NHNN). Doan ho la ghi sai ngan hang cho
	# mot khoan tien that.
	r = k("KBNN", ds)
	la("khong tu chon", r["ten"], "")
	dung("co goi y de nguoi ta chon", len(r["goi_y"]) > 1)
	r2 = k("khong-co-ngan-hang-nao-ten-nay", ds)
	la("khong bia", r2["ten"], "")
	la("khong goi y hu", r2["goi_y"], [])
	# Chuoi rong khong duoc rot vao ngan hang dau tien cua danh muc.
	la("chuoi rong", k("", ds)["ten"], "")


# ------------------------------ Tầng máy chủ


@ca("may chu chuan hoa TRUOC khi ghi, khong tin chuoi man gui xuong")
def _may_chu_chan():
	s = _doc("don_huy.py")
	i = s.find("def tao_hoan(")
	than = s[i:i + 4500]
	dung("co goi chuan hoa", "chuan_hoa_hoac_bao(" in than)
	j = than.find("chuan_hoa_hoac_bao(")
	k = than.find('"ngan_hang":')
	dung("chuan hoa nam truoc luc ghi", 0 < j < k)


@ca("cua ngo: khop_ten va chuan_hoa_hoac_bao KHONG duoc mo ra ngoai")
def _cua_ngo():
	s = _doc("khung/kiem_thu/thu_cua_ngo.py")
	dung("co canh cua cho ngan_hang.py", '"ngan_hang.py"' in s)
	src = _doc("ngan_hang.py")
	# chuan_hoa_hoac_bao co quyen TAO ban ghi Bank moi. Mo ra ngoai la cho
	# bat ky ai bom them ngan hang vao danh muc.
	i = src.find("def chuan_hoa_hoac_bao(")
	la("chuan_hoa_hoac_bao khong whitelist", "@frappe.whitelist()" in src[max(0, i - 200):i], False)
	j = src.find("def khop_ten(")
	la("khop_ten khong whitelist", "@frappe.whitelist()" in src[max(0, j - 200):j], False)


# ------------------------------ Tầng màn hình, ca canh gác


# Man nao co o ngan hang. Them man moi thi them vao day.
MAN_CO_NGAN_HANG = ("29-don-huy.js", "11-khach-ca-hop-dong.js")


@ca("man hinh: khong man nao dung o GO TU DO cho ngan hang")
def _khong_o_go_tu_do():
	"""Ca canh gac. Do la ca dat gia nhat trong tep nay.

	Sua giao dien la het loi hom nay. Ca nay moi chan duoc lan thu ba.
	"""
	for ten in MAN_CO_NGAN_HANG:
		s = _js(ten)
		for dong in s.split("\n"):
			if "<input" not in dong:
				continue
			d = dong.lower()
			if "ngân hàng" in d or "ngan hang" in d or "dhnh" in d:
				raise AssertionError(
					"%s con mot o <input> cho ngan hang: %s\n"
					"Doi thanh nut goi nhChon() theo QT-31." % (ten, dong.strip()[:110])
				)
		dung("%s co goi nhChon" % ten, "nhChon(" in s)


@ca("man don huy: o ngan hang la NUT chon, khong con doc bang lay('dhNH')")
def _o_chon():
	s = _js("29-don-huy.js")
	dung("co nut chon", "data-dhnh" in s)
	dung("bam nut thi mo nhChon", "nhChon(dhF.ngan_hang" in s)
	# Doc mot o khong con ton tai se XOA TRANG lua chon vua chon.
	la("khong doc o cu nua", "lay('dhNH')" in s, False)


# ------------------------------ Khối 2: dấu tiếng Việt và ô bằng chứng


@ca("chip ly do huy: co dau tieng Viet va chi co MOT bang")
def _chip_co_dau():
	s = _doc("don_huy.py")
	dung("bang nam o may chu", "LY_DO_HUY = (" in s)
	for nhan in ("Khách đổi ý", "Khách đặt nhầm ngày", "Bếp không kịp làm",
			"Hết nguyên liệu", "Trùng đơn", "Khác"):
		dung("co nhan %r" % nhan, '"%s"' % nhan in s)
	js = _js("29-don-huy.js")
	# Man phai VE TU bang cua may chu. Truoc day man tu dung danh sach chip
	# bang chinh chuoi khoa, nen chip hien "Khach dat nham ngay" khong dau.
	dung("man doc bang tu may chu", "f.ly_do_chon.forEach(" in js)
	dung("ve NHAN chu khong ve KHOA", "h(r.ten)" in js)
	dung("ban du phong cung co dau", "Khách đặt nhầm ngày" in js)


@ca("bang chung: BAT BUOC o may chu chu khong chi lam mo nut")
def _bang_chung_bat_buoc():
	s = _doc("don_huy.py")
	i = s.find("def tao_hoan(")
	than = s[i:i + 5000]
	dung("co loc tep", "_bang_chung_hop_le(" in than)
	dung("thieu anh thi chan", "Chưa có ảnh bằng chứng" in than)
	# Lam mo nut tren man chi la phep lich su. Ai goi thang cua van lap duoc
	# phieu trang bang chung neu may chu khong chan.
	j = than.find("tep_bc = _bang_chung_hop_le(")
	k = than.find("ho_so = frappe.get_doc(")
	dung("chan truoc khi dung ho so", 0 < j < k)
	# Va phai chan TRUOC khi tieu mat mot ma OTP cua nguoi ta.
	o = than.find("_otp_kiem(otp")
	dung("chan truoc khi hoi OTP", 0 < j < o)


@ca("bang chung: loc theo tep CO THAT, khong tin danh sach man gui len")
def _bang_chung_co_that():
	s = _doc("don_huy.py")
	i = s.find("def _bang_chung_hop_le(")
	than = s[i:i + 1800]
	# Gui ma bia thi phieu mang mot danh sach anh khong mo duoc, ma van qua
	# duoc phep kiem "da co bang chung".
	dung("do tep con that", 'frappe.db.exists("File", ma)' in than)


@ca("bang chung: de RIENG TU, va co mat o CA HAI cho")
def _bang_chung_rieng_tu():
	s = _doc("don_huy.py")
	i = s.find("def _gan_bang_chung(")
	than = s[i:i + 2400]
	# Anh khung chat co ten va so dien thoai khach.
	dung("dat rieng tu", '"is_private": 1' in than)
	dung("gan ve ho so", "attached_to_doctype" in than)
	dung("chep sang phieu chi", '"Payment Entry"' in than)
	dung("khong nhan doi tep that", "ignore_if_duplicate=True" in than)


@ca("man don huy: o tai len bang chung co dien giai va co thumbnail")
def _o_bang_chung_tren_man():
	js = _js("29-don-huy.js")
	dung("co nut chon anh", "data-dhbc" in js)
	dung("co nut go tung anh", "data-dhgo" in js)
	dung("co ham them anh", "async function dhThemBangChung(" in js)
	dung("ve thumbnail", "dhLaAnh(" in js)
	dung("co cau dien giai", "Chụp hình khung chat với khách" in js)
	# Dung lai duong tai cua tep 19, khong dung duong rieng: hai duong tai la
	# hai cho phai nho dat is_private, quen mot cho la anh khach nam cong khai.
	dung("dung lai duong tai chung", "huUpTep(" in js)
	la("khong dung duong tai rieng", "FormData(" in js, False)


@ca("man don huy: chua du thi nut Gui bi lam mo VA noi ro thieu gi")
def _nut_mo():
	js = _js("29-don-huy.js")
	dung("co ham liet ke thieu", "function dhConThieu(" in js)
	dung("nut co the bi mo", "disabled" in js)
	dung("noi ro con thieu gi", "Còn thiếu" in js)
	i = js.find("function dhConThieu(")
	than = js[i:i + 700]
	for o in ("ảnh bằng chứng", "ngân hàng", "lý do huỷ", "số tài khoản"):
		dung("dem thieu %r" % o, o in than)


# ------------------------------ Khối 3: đuôi luồng, uỷ nhiệm chi


@ca("uy nhiem chi: luong huy don phai NOI phieu chi vao ho so")
def _noi_phieu_chi():
	"""Thieu dong nay la ket ca duoi luong.

	`hoan_tien.dinh_unc` va `hoan_tien.tai_unc` deu doc `phieu_chi` tren ho
	so. Luong huy don sinh Payment Entry thang chu khong qua buoc doi soat,
	nen truoc day o nay de trong: ke toan khong co cho dinh uy nhiem chi,
	Sales cung khong tai duoc gi gui khach.
	"""
	ht = _doc("hoan_tien.py")
	i = ht.find("def _sinh_chung_tu(")
	than = ht[i:i + 3000]
	# Tu 23/08/2026 viec noi nay lam o day chu khong o `don_huy.tao_hoan`
	# nua, vi hai phieu bay gio sinh tai buoc doi soat.
	dung("noi phieu chi", "ho_so.phieu_chi = chi.name" in than)
	dung("noi ca phieu thu", "ho_so.phieu_thu = thu.name" in than)
	dung("co o phieu_thu tren doctype", '"fieldname": "phieu_thu"' in ht)


@ca("uy nhiem chi: co phieu chi roi thi khong doi doi soat nua")
def _khong_doi_doi_soat_thua():
	ht = _doc("hoan_tien.py")
	i = ht.find("def _pe_cua(")
	than = ht[i:i + 3000]
	j = than.find("if not d.phieu_chi:")
	k = than.find("if not cint(d.da_doi_soat):")
	# Hoi doi soat truoc thi ke toan cam uy nhiem chi that trong tay van bi
	# chan, ma chan xong cung khong ai go duoc vi phieu chi thi da co san.
	dung("hoi phieu chi truoc", 0 < j < k)


# ------------------------------ v283: Sales chỉ lập hồ sơ, kế toán sinh phiếu


@ca("huy don: Sales KHONG con dung chung tu ke toan trong yeu cau cua minh")
def _sales_khong_dung_chung_tu():
	"""Đây là ca chốt cả quyết định 23/08/2026 của anh Việt.

	Trước đó `tao_hoan` dựng luôn hai Payment Entry trong yêu cầu của Sales.
	Sales không có quyền trên Payment Entry - và đúng là không nên có - nên
	luồng chưa từng chạy được lần nào kể từ khi dựng 21/08.

	Ai sau này định "cho tiện" mà dựng lại phiếu ngay trong hàm đó thì ca
	này đỏ, kèm câu giải thích vì sao không được.
	"""
	s = _doc("don_huy.py")
	la("khong con ham dung phieu tien", "def _phieu(" in s, False)
	i = s.find("def tao_hoan(")
	than = s[i:]
	la("tao_hoan khong tao Payment Entry", 'frappe.new_doc("Payment Entry")' in than, False)
	la("tao_hoan khong goi _phieu", "_phieu(" in than, False)
	dung("co ghi ro vi sao", "sinh muộn hơn một nhịp" in than or "không sinh phiếu tiền" in than.lower())


@ca("huy don: hai phieu sinh o buoc doi soat, ben hoan_tien")
def _sinh_o_doi_soat():
	s = _doc("hoan_tien.py")
	dung("co ham dung cap phieu", "def _lap_cap_phieu_huy_don(" in s)
	i = s.find("def _sinh_chung_tu(")
	than = s[i:i + 3000]
	dung("_sinh_chung_tu co nhanh huy don", "LOAI_HUY_PANCAKE" in than)
	dung("goi ham dung cap phieu", "_lap_cap_phieu_huy_don(" in than)
	# Ho so huy don KHONG co hoa don nao, nen nhanh nay phai dung TRUOC dong
	# doc Sales Invoice, khong thi no o ngay tai do.
	j = than.find("if loai == LOAI_HUY_PANCAKE:")
	k = than.find("si = frappe.get_doc(SI, ho_so.hoa_don)")
	dung("nhanh huy don dung truoc luc doc hoa don", 0 < j < k)


@ca("huy don: van du HAI CHAN thu va chi, van de NHAP")
def _van_hai_chan():
	s = _doc("hoan_tien.py")
	i = s.find("def _lap_cap_phieu_huy_don(")
	than = s[i:i + 5000]
	dung("co chan thu", '"Receive"' in than)
	dung("co chan chi", '"Pay"' in than)
	# Chi lap phieu chi thi TK 131 cua Khach le Online du No, trong nhu khach
	# con no dung bang so vua tra. Chi Dung chot 21/08 dieu 2.
	dung("noi ro vi sao hai chan", "131" in than or "giữ hộ" in than)
	# De NHAP: khong duoc submit ho. Ke toan dinh uy nhiem chi roi moi ghi so.
	la("khong tu ghi so", ".submit()" in than, False)


@ca("huy don: ve chung mot man Phieu hoan tien, KHONG de them man moi")
def _chung_mot_man():
	"""Anh Việt 23/08/2026: "Đừng đẻ thêm màn nữa nha"."""
	s = _doc("hoan_tien.py")
	i = s.find("def doi_soat(")
	than = s[i:i + 3000]
	# Loc cu la `if d.get("hoa_don")`, gat sach ho so huy don ra khoi vong
	# quet nen chung nam mai o "Cho chi".
	dung("doi soat do theo ma do", 'd["ma_do"]' in than or "ma_do_soat(" in than)
	la("khong con loc cung theo hoa don", 'ds = [d for d in ds if d.get("hoa_don")]' in than, False)
	# Man danh sach phai hien duoc ma don thay cho ma hoa don.
	j = s.find("def ds(trang_thai")
	dung("danh sach tra ve ma don", '"ma_don_pancake"' in s[j:j + 2500])
	js = _js("11-khach-ca-hop-dong.js")
	dung("the hien ma don tren the", "x.ma_don_pancake" in js)
	dung("co chip nhan ra loai", "HUỶ ĐƠN" in js)


@ca("do sao ke: ho so huy don do theo MA DON, khong con do ca cau")
def _do_ma_don():
	"""DOI TU CA CAU SANG MA TRAN, v294 ngay 24/08/2026.

	Ban v292 do ca cau noi dung chuyen khoan, vi `khop_giao_dich` luc do chi
	chan chu so o phia SAU nen do "92252" tran se dinh vao mot dong chua
	"192252".

	Nhung ca cau hong nang hon, va du lieu that ngay 24/08 da chung minh:

	    app bao go : THE VAGABOND HOAN TIEN 92245
	    sao ke that: MBCT VAGABOND HOAN TIEN DON HANG 92245 D237BVMB/870581

	Chi Dung bo chu THE, them hai chu DON HANG, ngan hang chen MBCT o dau.
	Ca cau truot, may khong khop, va chi phai bam nut thu cong luc 14:31.

	Nay `doi_soat_sepay.co_ma` chan chu so CA HAI DAU nen do ma tran vua an
	toan vua bat duoc moi cach go. Xem `thu_doi_soat_sepay.py`.
	"""
	src = _doc("hoan_tien.py")
	ns = {}
	m = re.search(r"^def ma_do_soat\(ho_so\):.*?(?=^def |\Z)", src, re.S | re.M)
	assert m, "khong tach duoc ma_do_soat"
	ns["LOAI_HUY_PANCAKE"] = "Huy don Pancake"
	exec(compile(m.group(0), "hoan_tien.py", "exec"), ns)
	f = ns["ma_do_soat"]
	la("co hoa don thi do theo hoa don", f({"hoa_don": "HDB-26-08-00553"}), "HDB-26-08-00553")
	la("huy don do theo MA DON tran",
		f({"hoa_don": "", "loai_hoan": "Huy don Pancake",
		   "ma_don_pancake": "92252",
		   "noi_dung_ck": "THE VAGABOND HOAN TIEN 92252"}),
		"92252")
	# THA KHONG KHOP CON HON KHOP NHAM mot lan tien ra: phieu bi loi cu xoa
	# mat ma thi `noi_dung_ck` con tro lai mot chuoi la con cua MOI dong hoan
	# tien, khop bua vao bat ky dong nao.
	la("mat ma don thi tra rong, khong lay chuoi cut lam ma do",
		f({"hoa_don": "", "loai_hoan": "Huy don Pancake",
		   "ma_don_pancake": "", "noi_dung_ck": "THE VAGABOND HOAN TIEN "}),
		"")
	la("khong ro thi tra rong", f({"hoa_don": "", "loai_hoan": "", "noi_dung_ck": "x"}), "")


@ca("do sao ke: HAI duong doi soat dung chung mot phep, khong duoc lech")
def _hai_duong_mot_phep():
	"""Ngày 16/08/2026 hai đường lệch nhau đã tốn của tiệm một ngày.

	Xem ghi chú dài ở `chon_ma_khop`.
	"""
	s = _doc("hoan_tien.py")
	for ten in ("def doi_soat(", "def sepay_tien_ra("):
		i = s.find(ten)
		than = s[i:i + 3000]
		dung("%s dung ma_do_soat" % ten.strip("def ("), "ma_do_soat(" in than)


@ca("bang chung: chep sang phieu chi luc phieu ra doi, van de rieng tu")
def _bang_chung_theo_sang():
	s = _doc("hoan_tien.py")
	dung("co ham chep", "def _chep_bang_chung_sang_phieu(" in s)
	i = s.find("def _chep_bang_chung_sang_phieu(")
	than = s[i:i + 1800]
	dung("dat rieng tu", '"is_private": 1' in than)
	dung("khong nhan doi tep that", "ignore_if_duplicate=True" in than)
	# Luc goi ham nay thi tien da ra khoi tai khoan that roi, mot cai anh
	# khong chep duoc khong duoc lam hong buoc doi soat.
	dung("khong nem loi", "log_error" in than)

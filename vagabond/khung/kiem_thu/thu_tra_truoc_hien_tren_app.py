"""Ca kiểm cho vòng sửa 03/09/2026: phiếu trả trước phải nhìn thấy được.

Hai người báo cùng một họ lỗi trong một buổi:

  Uyên: *"chỗ này không có mục Tạo phiếu thanh toán trước cho NCC, nên khi
  em tạo TT thì bên app sẽ không hiện lên ạ, trên desktop thì có hiện ạ"*.
  Phiếu trả trước là một phiếu chi, không phải một hồ sơ thanh toán, nên màn
  Hồ sơ thanh toán không đọc tới nó; mà bảng chip lọc của màn đó có năm luồng
  lúc lập nhưng chỉ có bốn chip lọc. Lập được mà không tìm lại được.

  Chị Dung: màn Duyệt phiếu chi báo dấu tích xanh "không có phiếu nào cần xử
  lý", trong khi màn Hồ sơ thanh toán đang có tám bộ chờ chị chuyển tiền,
  vài bộ quá hạn từ 12/08. Ô rỗng đếm theo ô `tt`, mà `tt` bị trễ hẹn ăn
  trùm, nên hồ sơ càng để lâu càng bị đếm sót.

Mọi ca chạy trên phép THUẦN và trên văn bản tệp: không cần Frappe thật,
không cần site, không cần mạng, không cần thư viện requests.
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


# ------------------------------------------------- Dịch bước phiếu chi


@ca("tra truoc: dich du nam buoc cua workflow duyet phieu chi")
def _dich_du_buoc():
	from vagabond import tra_truoc as tt

	la("nhap", tt.dich_buoc(tt.TT_NHAP), "Nhap")
	la("cho ke toan", tt.dich_buoc(tt.TT_CHO_FIN), "Cho ke toan")
	la("cho giam doc", tt.dich_buoc(tt.TT_CHO_GD), "Cho giam doc")
	la("da ghi so", tt.dich_buoc(tt.TT_DA_GHI_SO), "Da thanh toan")
	la("bi tra lai", tt.dich_buoc(tt.TT_TRA_LAI), "Tu choi")


@ca("tra truoc: buoc la khong lam dong bien mat khoi moi chip")
def _buoc_la_van_co_cho():
	from vagabond import ho_so_tt as hs
	from vagabond import tra_truoc as tt

	# Tra ve mot ma KHONG nam trong THU_TU thi man hinh dung chip nao cung
	# khong bat duoc dong do, va no bien mat lang le.
	for buoc in ("", None, "Trang thai la hoac hoac"):
		la("buoc la -> Nhap", tt.dich_buoc(buoc), "Nhap")
	for ma in tt.DICH_TRANG_THAI.values():
		dung("ma %s co trong THU_TU cua man" % ma, ma in hs.THU_TU)


@ca("tra truoc: chi buoc chua ket thuc moi tinh la con treo")
def _con_treo_dung():
	from vagabond import tra_truoc as tt

	dung("nhap con treo", tt.con_treo(tt.TT_NHAP))
	dung("cho ke toan con treo", tt.con_treo(tt.TT_CHO_FIN))
	dung("cho giam doc con treo", tt.con_treo(tt.TT_CHO_GD))
	dung("bi tra lai con treo", tt.con_treo(tt.TT_TRA_LAI))
	dung("da ghi so thi het treo", not tt.con_treo(tt.TT_DA_GHI_SO))


# --------------------------------------- Phiếu mới lập vào thẳng bước kế toán


@ca("tra truoc: phieu moi lap KHONG con nam o buoc Nhap")
def _khong_dung_o_nhap():
	from vagabond import tra_truoc as tt

	s = _doc("tra_truoc.py")
	dung("dat trang thai dau la buoc ke toan", "pe.workflow_state = TT_CHO_FIN" in s)
	dung("khong con dat ve Nhap", "pe.workflow_state = TT_NHAP" not in s)
	la("ten buoc trung workflow that", tt.TT_CHO_FIN, "Chờ FIN kiểm tra")


@ca("tra truoc: cau bao cho nguoi lap khop voi trang thai that")
def _cau_bao_khop_that():
	s = _doc("tra_truoc.py")
	# Cau "dang cho ke toan kiem tra" chi dung khi phieu THAT SU nam o buoc
	# ke toan. Truoc 03/09 no noi vay ma de phieu o Nhap - ke toan khong he
	# thay buoc Nhap, nen cau bao la sai.
	dung("van bao dang cho ke toan", "đang chờ kế toán kiểm tra" in s)
	dung("tra ve trang thai buoc ke toan", 'pe.get("workflow_state") or TT_CHO_FIN' in s)
	dung("chi duong ve man Ho so thanh toan", "chip Trả trước NCC" in s)


# ------------------------------------------------- Chip lọc và đường nhìn


@ca("man Ho so TT: du chip loc cho ca NAM luong lap duoc")
def _du_chip_loc():
	s = _js("19-ho-so-tt.js")
	for ma in ("'NCC'", "'Tra truoc'", "'Hoan ung HD'", "'Hoan ung'", "'TK cong ty'"):
		dung("co chip %s" % ma, ma + ", '" in s or "[" + ma + ", '" in s)
	dung("chip tra truoc co nhan", "⏩ Trả trước NCC" in s)


@ca("man Ho so TT: dong tra truoc mo sang man phieu chi, khong mo man ho so")
def _dong_tra_truoc_mo_dung_man():
	s = _js("19-ho-so-tt.js")
	dung("co danh dau dong phieu chi", "data-hspc" in s)
	dung("dong phieu chi goi scrPayView", "scrPayView(nm)" in s)
	dung("giau nut xuat excel o chip tra truoc", "hsLoai === 'Tra truoc' ? ''" in s)


@ca("ho_so_tt: danh sach co ghep phieu tra truoc va khong lam chet man khi hong")
def _ghep_co_luoi():
	from vagabond import ho_so_tt as hs

	s = _doc("ho_so_tt.py")
	la("ma loai tra truoc", hs.LOAI_TRA_TRUOC, "Tra truoc")
	dung("co nhan tieng Viet", hs.NHAN_LOAI.get(hs.LOAI_TRA_TRUOC))
	dung("goi gom_phieu", "tt.gom_phieu(" in s)
	dung("boc try de man khong chet theo", "ho_so_tt: ghep phieu tra truoc loi" in s)


@ca("tra truoc: gom_phieu KHONG tu chan quyen, cua ngo moi chan")
def _gom_phieu_khong_tu_chan():
	# Ke toan va giam doc khong nam trong tap lap phieu tra truoc. Neu
	# gom_phieu tu goi _chan() thi ke toan mo man Ho so thanh toan la loi
	# ngay, mat luon ca danh sach ho so that.
	s = _doc("tra_truoc.py")
	i_gom = s.index("def gom_phieu(")
	i_cua = s.index("def ds_phieu(")
	than = s[i_gom:]
	dung("than gom_phieu khong goi _chan", "_chan()" not in than)
	dung("cua ngo ds_phieu co goi _chan", "_chan()" in s[i_cua:i_gom])


@ca("tra truoc: chi lay phieu tro vao NHA CUNG CAP va co neo don mua")
def _loc_dung_pham_vi():
	s = _doc("tra_truoc.py")
	i = s.index("def gom_phieu(")
	than = s[i:i + 4000]
	dung("loc party_type Supplier", '"party_type": "Supplier"' in than)
	dung("loc payment_type Pay", '"payment_type": "Pay"' in than)
	dung("bo phieu da huy", '"docstatus": ["<", 2]' in than)
	dung("bat buoc co neo don mua", "if not don:" in than)


# ------------------------------------------------- Ô rỗng màn Duyệt phiếu chi


@ca("viec can lam: tach o buoc khoi o mau, tre hen khong an mat buoc")
def _tach_buoc_khoi_mau():
	s = _doc("viec_can_lam.py")
	dung("co o buoc rieng", '"buoc": buoc,' in s)
	dung("tt van uu tien tre hen de bay do va len dau",
		'"tt": "tre_hen" if _tre(x.get("han_tra_som_nhat")) else buoc,' in s)
	dung("khong con nhanh long ba tang cu",
		'else ("cho_chi" if x["trang_thai"] == hs.TT_DA_DUYET' not in s.split("def _viec_tra_truoc")[0].split('"tt": "tre_hen" if _tre(x.get("han_tra_som_nhat")) else buoc,')[1])


@ca("man Duyet phieu chi: dem ho so theo BUOC chu khong theo mau")
def _dem_theo_buoc():
	s = _js("04-tao-phieu.js")
	dung("dem theo buoc, bo ban nhap",
		"(x.buoc || x.tt) !== 'ban_nhap'" in s)
	dung("khong con dem bang tt === cho_duyet",
		"x.tt === 'cho_duyet'" not in s)
	dung("dem rieng so qua han", "paySoTre" in s)


@ca("man Duyet phieu chi: nhac ho so ca khi danh sach KHONG rong")
def _nhac_ca_khi_khong_rong():
	s = _js("04-tao-phieu.js")
	dung("co nhanh nhac khi con dong", "paySoHoSo && rows.length" in s)
	dung("noi cho bạn xử lý chu khong noi cho bạn duyệt",
		"đang chờ bạn xử lý" in s)


@ca("man Duyet phieu chi: phieu hoan tien khach khong lot vao hang doi NCC")
def _loc_phieu_khach():
	s = _js("04-tao-phieu.js")
	dung("lay them o party_type", "'party_type'" in s)
	dung("tach phieu tro vao Customer ra", "=== 'Customer'" in s)
	dung("van giu lai de dem chu khong vut", "var lac = docs.filter" in s)
	dung("noi ro con bao nhieu to nam nham", "nằm nhầm trong hàng đợi" in s)


@ca("viec can lam: phieu tra truoc co mat trong danh sach viec cua ke toan")
def _tra_truoc_vao_viec_can_lam():
	s = _doc("viec_can_lam.py")
	dung("co nguon rieng", "def _viec_tra_truoc(vai):" in s)
	dung("duoc goi vao", "ra.extend(_viec_tra_truoc(vai))" in s)
	dung("ke toan thay buoc cua minh", "buoc.append(tt.TT_CHO_FIN)" in s)
	dung("giam doc thay buoc cua minh", "buoc.append(tt.TT_CHO_GD)" in s)


@ca("cua ngo: ds_phieu da duoc ghi vao danh sach ham mo ra ngoai")
def _cua_ngo_co_ten():
	s = _doc(os.path.join("khung", "kiem_thu", "thu_cua_ngo.py"))
	dung("ds_phieu co ten", '"ds_phieu"' in s)


# ================================================ Cùng họ lỗi, các màn khác
#
# Rà soát ngày 03/09/2026 theo lệnh anh Việt: "rà soát lại lỗi của phần APP
# này xem còn xung đột gì nữa ở mọi màn". Ba dạng cùng một họ:
#   A - lập ra được mà danh sách không bày ra được
#   B - con số đếm lọc khác với cái màn hình nó trỏ tới
#   C - tab chia theo vai làm người LẬP mất dấu phiếu của chính mình


@ca("trang chu: the Duyet phieu chi dem dung cai man hinh bay ra")
def _the_phieu_chi_khop_man():
	s = _js("02-trang-chu.js")
	dung("the loc payment_type Pay", "payment_type: 'Pay'" in s)
	dung("the bo phieu tro vao khach", "!== 'Customer'" in s)


@ca("trang chu: the Don con treo dem dung cai man Don con treo bay ra")
def _the_don_treo_khop_man():
	s = _js("02-trang-chu.js")
	dung("co moc 14 ngay nhu man hinh", "mocTreo" in s)
	dung("chi dem don chua vao quay", "vgb_quay: ['in', ['', null]]" in s)
	dung("khong con cat hom nay di",
		"posting_date: ['<', today()], docstatus: 0, custom_pancake_id" not in s)


@ca("kho chung tu: tab Da huy khong keo phieu xuat dung noi bo vao")
def _tab_huy_khong_lan_noi_bo():
	s = _js("03-kho-chung-tu.js")
	dung("loc muc dich xuat de trong", "vgb_muc_dich_xuat: ['in', ['', null]]" in s)


@ca("nhan hang: bon tab khong keo phieu tra hang NCC vao")
def _nhan_hang_bo_phieu_tra():
	s = _js("06-nhap-kho-kiem-ke.js")
	dung("loc is_return 0", "is_return: 0" in s)


@ca("man Duyet phieu chi: nguoi lap co tab xem lai phieu cua chinh minh")
def _co_tab_toi_lap():
	s = _js("04-tao-phieu.js")
	dung("co tab Toi lap", "TAB_TOI" in s and "Tôi lập" in s)
	dung("loc theo nguoi lap", "owner: S.user" in s)
	dung("chi lay phieu con nhap", "docstatus: 0" in s)
	dung("tab tu bien mat khi khong co phieu", "cuaToi.length ? [TAB_TOI] : []" in s)


@ca("nop quy: chip dem theo ca o tim, khong bo qua")
def _nop_quy_chip_theo_o_tim():
	s = _doc("nop_quy.py")
	dung("co ham khop dung chung", "def _khop(d):" in s)
	dung("vong dem co ap o tim", "if q and not _khop(r):" in s)


@ca("hang tang: chip Cho duyet loc ra duoc ca dong de trong")
def _hang_tang_o_trong():
	s = _doc("hang_tang.py")
	dung("loc gom ca o trong", 'loc["vgb_tang_duyet"] = ["in", [TT_CHO, "", None]]' in s)


@ca("de nghi chi: nhan chip dung voi thu no chua")
def _nhan_chip_dung():
	from vagabond import de_nghi_chi as dn

	nhom = {k: (ten, tt) for k, ten, tt in dn.CHIP_TRANG_THAI}
	la("nhom chua phieu bi tra lai duoc goi dung ten", nhom["da_huy"][0], "Bị trả lại")
	dung("khong con goi la Da huy", all(t != "Đã huỷ" for t, _ in nhom.values()))


@ca("xuat kho them: dong doi chieu hien khi hai con so lech nhau")
def _doi_chieu_khi_lech():
	s = _js("45-xuat-kho-them.js")
	dung("dieu kien co so sanh do dai",
		"loc.length !== cfg.ds.length || st.tab" in s)


# =================================================== Bộ thư mẫu gửi soi thật


@ca("thu mau: dung duoc du 14 la khong can Frappe")
def _dung_du_thu_mau():
	from vagabond import thu_khung as tk

	la("du 14 mau", len(tk.MAU_THU), 14)
	chan_co = set(c for _k, _t, c in tk.MAU_THU)
	for c in ("khach", "ncc", "nhan_vien", "noi_bo"):
		dung("co mau dung chan %s" % c, c in chan_co)
	for ma, ten, _c in tk.MAU_THU:
		than = tk._than_mau(ma)
		dung("mau %s co ruot" % ma, len(than) > 80)
		dung("mau %s khong de trong tieu de" % ma, bool(ten.strip()))


@ca("thu mau: khong cham du lieu that, khong gui cho khach")
def _thu_mau_khong_cham_du_lieu():
	s = _doc("thu_khung.py")
	i = s.index("def gui_thu_mau(")
	than = s[i:]
	dung("chan quyen truoc khi gui", "_quyen_gui_mau()" in than)
	dung("bat buoc co dia chi", '"@" not in email' in than)
	dung("tieu de mang chu THU MAU", "[THƯ MẪU]" in than)
	dung("chi gui cho dung mot dia chi", "recipients=[email]" in than)


@ca("thu mau: cua ngo dat o gui_thu, thu_khung van khong keo Frappe len dau")
def _cua_ngo_dat_dung_cho():
	s = _doc("thu_khung.py")
	dau = s.split("def tien(")[0]
	dung("thu_khung khong import frappe o tang mo dun", "\nimport frappe" not in dau)
	dung("thu_khung khong gan whitelist", "@frappe.whitelist()" not in s)
	g = _doc("gui_thu.py")
	dung("gui_thu co cua ngo", "def gui_bo_thu_mau(" in g)
	c = _doc(os.path.join("khung", "kiem_thu", "thu_cua_ngo.py"))
	dung("cua ngo da ghi ten", '"gui_bo_thu_mau"' in c)

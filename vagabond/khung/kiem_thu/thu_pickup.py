"""Ca kiểm cho luồng khách tự ra điểm lấy hàng (pickup).

Anh Việt đặt việc ngày 04/09/2026: ở ô phân công vận đơn phải có thêm ba
điểm "Pickup tại 307/1", "Pickup tại 9TCV", "Pickup tại NVHTN" đứng cạnh
tên shipper. Gắn điểm nào thì quản lý và thu ngân điểm đó thấy đơn, chụp
ảnh, lấy chữ ký khách, hoàn tất và đổi trạng thái; trạng thái đẩy sang
Pancake là đã nhận.

Bốn điều mỗi ca dưới đây canh:

1. Tên điểm KHÔNG được gõ lại ở pickup.py. Mã và địa chỉ lấy từ diem_ban,
   nơi duy nhất khai điểm bán. Gõ lại là dựng lại đúng cái bẫy đã làm mất
   37 hoá đơn hôm 10/08.
2. Ba loại người giao loại trừ nhau. Gắn điểm thì xoá shipper và ngược
   lại, không để một đơn vừa mang tên shipper vừa mang tên điểm.
3. Đơn pickup không đi đường book xe.
4. Đơn pickup dùng ĐÚNG ba bước của shipper, không có đường riêng nào:
   chụp ảnh, khách ký, bấm hoàn tất rồi đẩy Pancake.

Mọi ca chạy trên phép THUẦN và trên văn bản tệp: không cần Frappe, không
cần site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.pickup import (
	TRANG_THAI, chuan_ma, hop_le, loi_ma_la, ngan_cua, nhan_cua, tim, tu_ds,
)

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


PK = _doc("pickup.py")
VD = _doc("van_don.py")
JS = _doc(os.path.join("public", "js", "bep", "12-van-don.js"))
CN = _doc("thu_cua_ngo.py") if False else _doc(os.path.join("khung", "kiem_thu", "thu_cua_ngo.py"))

# Ba diem that dang chay, lay y nguyen tu diem_ban.MAC_DINH.
BA_DIEM = [
	{"ma": "SALES", "ten": "Sales Online", "ten_ngan": "Sales Online",
		"dia_chi": "307/1 Nguyễn Văn Trỗi, Phường 1, Quận Tân Bình"},
	{"ma": "TCV", "ten": "The Vagabond District 1", "ten_ngan": "District 1",
		"dia_chi": "9 Trần Cao Vân, Quận 1"},
	{"ma": "NVHTN", "ten": "Nhà Văn Hóa Thanh Niên", "ten_ngan": "NVHTN",
		"dia_chi": "21 Phạm Ngọc Thạch, Quận 3"},
]


# --------------------------------------------------- Ba nhan anh Viet doc


@ca("ba diem ra dung ba nhan anh Viet dat")
def _ba_nhan():
	ds = tu_ds(BA_DIEM)
	la("du ba diem", len(ds), 3)
	la("nhan diem bep", ds[0]["nhan"], "Pickup tại 307/1")
	la("nhan diem Tran Cao Van", ds[1]["nhan"], "Pickup tại 9TCV")
	la("nhan diem Nha Van Hoa", ds[2]["nhan"], "Pickup tại NVHTN")


@ca("giu nguyen thu tu cua diem_ban, khong tu sap lai")
def _giu_thu_tu():
	ds = tu_ds(BA_DIEM)
	la("thu tu ma", [x["ma"] for x in ds], ["SALES", "TCV", "NVHTN"])


@ca("dia chi lay tu diem_ban chu khong go lai trong pickup.py")
def _dia_chi_tu_diem_ban():
	ds = tu_ds(BA_DIEM)
	la("dia chi 307/1", ds[0]["dia_chi"], "307/1 Nguyễn Văn Trỗi, Phường 1, Quận Tân Bình")
	la("dia chi 9TCV", ds[1]["dia_chi"], "9 Trần Cao Vân, Quận 1")
	# Cai bay that: neu ai do go dia chi vao pickup.py thi sua ben diem_ban
	# se khong an, va hai man hinh se noi hai dia chi khac nhau.
	for manh in ("Trần Cao Vân", "Nguyễn Văn Trỗi", "Phạm Ngọc Thạch"):
		dung("pickup.py khong go lai dia chi %r" % manh, manh not in PK)


@ca("diem moi khong khai nhan ngan thi roi ve ten ngan cua diem_ban")
def _diem_moi():
	them = {"ma": "Q7", "ten": "The Vagabond Quận 7", "ten_ngan": "Quận 7", "dia_chi": "x"}
	ds = tu_ds(BA_DIEM + [them])
	la("diem moi van co nhan", ds[3]["nhan"], "Pickup tại Quận 7")
	# Mo chi nhanh khong phai sua ma nguon roi deploy.
	dung("Q7 khong nam trong pickup.py", "Quận 7" not in PK)


@ca("ma diem duoc chuan hoa, go thuong hay du khoang trang van khop")
def _chuan_ma():
	ds = tu_ds(BA_DIEM)
	la("viet thuong", chuan_ma(" tcv "), "TCV")
	dung("go thuong van hop le", hop_le("tcv", ds))
	dung("du khoang trang van hop le", hop_le(" NVHTN ", ds))
	la("tim ra dung diem", tim("tcv", ds)["ngan"], "9TCV")


@ca("ma la thi bao loi noi ro cac diem dang bat va chon lai o dau")
def _ma_la():
	ds = tu_ds(BA_DIEM)
	dung("ma la khong hop le", not hop_le("QUAN9", ds))
	dung("ma rong khong hop le", not hop_le("", ds))
	loi = loi_ma_la("QUAN9", ds)
	# QT-24: cau bao loi phai noi sai cai gi va lam gi tiep.
	dung("noi ro ma sai", "QUAN9" in loi)
	dung("liet ke diem dang bat", "9TCV" in loi and "NVHTN" in loi)
	dung("chi cho nguoi ta lam gi tiep", "Phân công" in loi)


@ca("dict hong dinh dang thi bo qua, khong lam sap o phan cong")
def _bo_rac():
	ds = tu_ds(BA_DIEM + [None, "rac", {}, {"ma": "   "}])
	la("chi giu ba diem that", len(ds), 3)
	la("ngan cua rac la rong", ngan_cua("khong phai dict"), "")
	la("nhan cua rac la rong", nhan_cua({}), "")


# ----------------------------------------------- Ba loai nguoi giao loai tru


@ca("nguoi cho va noi khach lay KHONG loai tru nhau")
def _khong_loai_tru():
	"""Anh Viet 05/09/2026: banh lam o 307, book xe cho ra 9TCV, khach den
	quay do lay - day la truong hop thuong gap nhat. Ban v424 bat hai thu
	loai tru nhau, sai."""
	i = VD.find("def gan_shipper(")
	than = VD[i:VD.find("def _mail_phan_cong", i)]
	# Chi con DUNG MOT cho xoa diem, la khi nguoi ta bam Bo diem.
	la("chi mot cho xoa diem", than.count('doc.diem_pickup = ""'), 1)
	j = than.find('doc.diem_pickup = ""')
	dung("cho do nam trong nhanh bo_diem", "bo_diem" in than[max(0, j - 120):j])
	# Nhanh gan shipper va nhanh gan app ngoai deu KHONG duoc dong den diem.
	a = than.find("if kenh:")
	b = than.find("elif shipper:")
	c = than.find("elif diem or cint(bo_diem):")
	dung("doc duoc ba nhanh", 0 < a < b < c)
	dung("nhanh app ngoai khong dong den diem", "diem_pickup" not in than[a:b])
	dung("nhanh shipper khong dong den diem", "diem_pickup" not in than[b:c])


@ca("gan diem khong go ten shipper dang cho")
def _gan_diem_giu_shipper():
	i = VD.find("def gan_shipper(")
	than = VD[i:VD.find("def _mail_phan_cong", i)]
	j = than.find("elif diem:")
	k = than.find("# --- Nguoi cho ---")
	dung("nhanh gan diem dung truoc phan nguoi cho", 0 < j < k)
	nhanh = than[j:k]
	dung("chi dat diem", "doc.diem_pickup = pickup.chuan_ma(diem)" in nhanh)
	dung("khong dung den shipper", "doc.shipper" not in nhanh)
	dung("khong dung den chuyen", "doc.chuyen" not in nhanh)


@ca("trang thai suy ra mot cho, khong dat tay o hai noi")
def _tt_mot_cho():
	dung("co ham suy trang thai", "def _tt_theo_gan(doc)" in VD)
	i = VD.find("def _tt_theo_gan(doc)")
	than = VD[i:VD.find("def _noi_giao(doc)", i)]
	dung("con nguoi cho thi Dang giao", '"Đang giao"' in than)
	dung("khong nguoi cho ma con diem thi Cho khach lay", "pickup.TRANG_THAI" in than)
	dung("khong ca hai thi Cho giao", '"Chờ giao"' in than)


@ca("gop chuyen KHONG xoa diem, va nhan ca don dang cho khach lay")
def _gop_chuyen_giu_diem():
	i = VD.find("def gop_chuyen(")
	than = VD[i:VD.find("def doi_soat_cod", i)]
	dung("khong xoa diem nua", 'doc.diem_pickup = ""' not in than)
	dung("nhan don dang cho khach lay", "pickup.TRANG_THAI" in than)


@ca("don pickup VAN book xe duoc")
def _van_book_xe():
	i = VD.find("def book_xe(")
	than = VD[i:VD.find("def aha_dich_vu", i)]
	dung("khong con chan don pickup", "if doc.diem_pickup:" not in than)


@ca("xe cho toi DIEM chu khong toi nha khach, va khong thu ho dong nao")
def _xe_toi_diem():
	"""Cai bay dat tien nhat cua tinh nang nay: ba duong goi xe deu tung lay
	thang doc.dia_chi, tuc dia chi khach. Voi don pickup thi bac tai cho hop
	banh toi nha khach trong khi khach ngoi cho o quay."""
	dung("co ham mot cho tinh noi giao", "def _noi_giao(doc)" in VD)
	i = VD.find("def _noi_giao(doc)")
	than = VD[i:VD.find("KENH_NGOAI = {", i)]
	dung("don co diem thi lay dia chi diem", '"dia_chi": d["dia_chi"]' in than)
	dung("ten nguoi nhan la cua quay", "The Vagabond" in than)
	dung("COD ve khong", '"cod": 0.0' in than)
	# Ngoai ham nay ra, khong duong nao duoc doc thang dia chi khach nua.
	con = VD[:i] + VD[VD.find("KENH_NGOAI = {", i):]
	la("khong con cho nao lay thang dia chi khach", con.count("doc.dia_chi"), 0)


@ca("shipper cho hang ra quay thi CHUA phai khach da nhan")
def _cho_ra_quay():
	"""Truoc day ban shipper bam Da giao luc bo hang xuong quay la don dong
	lai va Pancake bao khach da nhan, trong khi khach con chua toi."""
	i = VD.find("def giao_xong(")
	than = VD[i:VD.find("def giao_loi(", i)]
	j = than.find("if doc.diem_pickup and _la_shipper()")
	dung("co nhanh cho chang noi bo", j > 0)
	nhanh = than[j:than.find('doc.trang_thai = "Đã giao"', j)]
	dung("go nguoi cho ra", "doc.shipper = None" in nhanh)
	dung("ve lai hang cho khach lay", "doc.trang_thai = pickup.TRANG_THAI" in nhanh)
	dung("khong day Pancake", "_day_trang_thai_pancake" not in nhanh)
	dung("bao ro cho man hinh", '"toi_quay": 1' in nhanh)
	# Sales va ke toan van dong duoc don nhu thuong, vi ho la nguoi thay
	# khach den nhan that.
	dung("chi chan dung vai shipper", "not (_la_sales() or _la_ke_toan())" in nhanh)


# ----------------------------------------------- Dung ba buoc cua shipper


@ca("hoan tat don pickup di chung ham giao_xong, khong co duong rieng")
def _chung_giao_xong():
	i = VD.find("def giao_xong(")
	than = VD[i:VD.find("def giao_loi(", i)]
	dung("van day trang thai Pancake", "_day_trang_thai_pancake" in than)
	dung("ghi nguoi trao tai diem", "doc.nguoi_trao = frappe.session.user" in than)
	# Khong duoc de mot ham hoan_tat_pickup rieng: hai duong la hai cach
	# hong khac nhau, va mot duong se quen day Pancake.
	dung("khong co ham hoan tat rieng", "def hoan_tat_pickup" not in VD)


@ca("quan ly cua hang mo duoc man van don")
def _quyen_quan_ly():
	dung("co ham kiem vai quan ly diem", "def _la_quan_ly_diem()" in VD)
	i = VD.find("def _kiem_quyen_xem()")
	than = VD[i:i + 400]
	dung("cong xem co ke vai quan ly", "_la_quan_ly_diem()" in than)


@ca("cua ds_diem_pickup da khai trong danh sach cua ngo")
def _khai_cua_ngo():
	dung("ham co whitelist", "def ds_diem_pickup()" in VD)
	dung("ten nam trong thu_cua_ngo", '"ds_diem_pickup"' in CN)


# ------------------------------------------------------------ Man hinh app


@ca("man van don co tab rieng cho don khach tu lay")
def _tab_pickup():
	i = JS.find("function vdNhomTab()")
	than = JS[i:JS.find("function vdTabTim", i)]
	dung("co tab pickup", "k: 'pickup'" in than)
	dung("nhan tab doc duoc", "Khách tự lấy" in than)
	# Don pickup phai ROI khoi tab Can phan cong, khong thi van roi danh sach
	# dung nhu truoc.
	j = than.find("k: 'cho_gan'")
	k = than.find("k: 'pickup'")
	dung("tab can phan cong dung o tren", 0 <= j < k)
	dung("can phan cong chi tinh don Cho giao", "r.trang_thai === 'Chờ giao' && !r.shipper" in than)


@ca("mo man ra dung ngay tab pickup neu do la viec dau tien con don")
def _tab_mac_dinh():
	i = JS.find("function vdTabMacDinh(")
	than = JS[i:i + 400]
	dung("pickup nam trong thu tu uu tien", "'pickup'" in than)
	# Shipper khong bao gio thay don pickup, nen khong duoc dua vao thu tu
	# cua ho.
	dong = [d for d in than.split("\n") if "vdLaShipper()" in d][0]
	cua_shipper = dong[dong.find("?") + 1:dong.find(":", dong.find("?"))]
	dung("thu tu cua shipper khong co pickup", "'pickup'" not in cua_shipper)


@ca("o phan cong xep ba diem giua shipper va app ngoai")
def _o_phan_cong():
	i = JS.find("function vdOpsGiao(")
	than = JS[i:JS.find("async function vdGanNguoiGiao", i)]
	a = than.find("x.user")
	b = than.find("'diem:'")
	c = than.find("'app:'")
	dung("co lua chon diem", b > 0)
	dung("diem dung sau shipper", a < b)
	dung("diem dung truoc app ngoai", b < c)


@ca("chon diem thi goi may chu voi tham so diem, khong gan nham shipper")
def _goi_may_chu():
	i = JS.find("async function vdGanNguoiGiao(")
	than = JS[i:JS.find("function vdApp(", i)]
	dung("nhan ra ma diem", "diem:" in than)
	dung("goi voi tham so diem", "diem: ma" in than)


@ca("nut hoan tat va chip trang thai co cho don pickup")
def _nut_hoan_tat():
	dung("trang thai moi co mau", "'Chờ khách lấy': '#7c3aed'" in JS)
	dung("trang thai moi co icon", "'Chờ khách lấy': '🏬'" in JS)
	dung("nut hoan tat mo cho don pickup", "d.trang_thai === VD_TT_PICKUP" in JS)
	dung("chu tren nut noi dung viec", "Khách đã lấy, chụp ảnh" in JS)
	# Nut book xe PHAI con, va noi ro cho ra dau.
	dung("khong giau nut book xe", "!d.booking_id && !laPickup" not in JS)
	dung("nut book noi ro cho ra dau", "Book xe chở ra" in JS)
	dung("chu rieng cho ban shipper bo hang xuong quay", "Đã bỏ hàng xuống" in JS)


@ca("man chi tiet noi ro khach ra dau lay, khong de doc nham dia chi khach")
def _khoi_diem():
	dung("co khoi rieng", "KHÁCH TỰ RA LẤY" in JS)
	dung("hien dia chi diem", "vdDiemDiaChi(d.diem_pickup)" in JS)
	dung("hien ai da trao tay", "d.nguoi_trao" in JS)


@ca("chip loc theo tung diem cho nguoi truc quay")
def _chip_diem():
	i = JS.find("function vdNhomKenh(")
	than = JS[i:JS.find("function vdNhomGio(", i)]
	dung("co chip theo diem", "'pk:'" in than)
	dung("chip dung ten ngan", "vdDiemNgan(p)" in than)


@ca("trang thai moi da khai trong doctype, khong thi Frappe tu chi")
def _doctype():
	j = _doc(os.path.join("vagabond", "doctype", "van_don", "van_don.json"))
	dung("co trang thai Cho khach lay", "Chờ khách lấy" in j)
	dung("co truong diem_pickup", '"diem_pickup"' in j)
	dung("co truong nguoi trao", '"nguoi_trao"' in j)
	# Thieu trong TRUONG_DS thi dong tren man khong bay duoc diem, dung cai
	# loi da mac hom 04/09 voi don dieu chuyen.
	dung("diem nam trong danh sach truong", '"diem_pickup", "nguoi_trao"' in VD)


@ca("o phan cong co dong Bo diem, va chi hien khi don dang co diem")
def _dong_bo_diem():
	i = JS.find("function vdOpsGiao(")
	than = JS[i:JS.find("async function vdGanNguoiGiao", i)]
	dung("nhan tham so don de biet co diem chua", "function vdOpsGiao(ds, d)" in than)
	dung("co dong bo diem", "'bodiem'" in than)
	dung("chi hien khi co diem", "d && d.diem_pickup" in than)
	# Dong go nguoi cho phai noi ro la KHONG go diem, khong thi nguoi ta
	# tuong bam vao la mat luon noi khach lay.
	dung("go nguoi cho noi ro giu diem", "giữ nguyên nơi khách lấy" in than)


@ca("bo diem goi may chu dung tham so, khong gan nham shipper rong")
def _goi_bo_diem():
	i = JS.find("async function vdGanNguoiGiao(")
	than = JS[i:JS.find("function vdApp(", i)]
	j = than.find("v === 'bodiem'")
	dung("co nhanh bo diem", j > 0)
	dung("goi voi bo_diem", "bo_diem: 1" in than[j:j + 260])


@ca("khoi diem noi ro don dang duoc cho toi, khach chua nhan")
def _khoi_dang_cho():
	dung("bao dang duoc cho toi quay", "Đang được chở tới quầy này" in JS)
	dung("noi ro khach chua nhan", "khách chưa nhận" in JS)

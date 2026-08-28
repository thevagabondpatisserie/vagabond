"""Danh mục màn hình app Bếp: MỘT nguồn, máy sinh ra địa chỉ cho cả hai bên.

VÌ SAO CÓ TỆP NÀY
-----------------
Anh Việt 23/08/2026: *"click vào bất kỳ menu nào URL cũng đứng im, F5 là bị
văng về trang chủ"*.

App Bếp KHÔNG dùng Vue, cũng không có Vue Router. Nó là JavaScript thuần,
ghép từ các phần trong `public/js/bep/`. Việc đi lại giữa các màn do một
chồng hàm `S.stack` lo, và `go()` có gọi `history.pushState` nhưng luôn
truyền `location.href`, tức là ĐỊA CHỈ KHÔNG ĐỔI. Nhờ vậy nút Back của trình
duyệt lui đúng từng màn, nhưng địa chỉ trên thanh vẫn là `/bep`, nên F5 chỉ
nạp lại `/bep` và về màn chủ.

Muốn F5 đứng nguyên màn thì cần hai vế, thiếu một vế là hỏng:
  1. Máy khách phải ĐỔI địa chỉ khi mở màn (`vgbDatDuong` trong
     02-trang-chu.js).
  2. Máy chủ phải TRẢ VỀ chính app đó khi trình duyệt hỏi địa chỉ mới. Không
     có vế này thì F5 ra trang 404.

VÌ SAO PHẢI MÁY SINH CHỨ KHÔNG GÕ TAY HAI BẢNG (v288, 23/08/2026)
------------------------------------------------------------------
Bản đầu (v284) có HAI bảng gõ tay: `DUONG` bên Python và `VGB_DUONG` bên
JavaScript. Ca kiểm đối chiếu hai bảng, nhưng ca kiểm chỉ bắt được lúc hai
bảng LỆCH nhau, không bắt được lúc cả hai cùng SAI. Và đó đúng là chuyện đã
xảy ra: v284 gán slug `don-da-huy` cho khoá `DTREO`, mà `DTREO` là màn "Đơn
còn treo". Hai bảng khớp nhau tuyệt đối, ca kiểm xanh, nhân viên bấm "đơn đã
huỷ" thì ra "đơn còn treo". Phải sửa lại ở v286.

Nay chỉ còn MỘT nguồn là bảng `MAN` bên dưới, và slug do máy sinh từ chính
TÊN màn hình bằng `slugify`. Đặt sai tên thì địa chỉ sai theo đúng cùng một
kiểu, nên nhìn bảng là thấy, không cần F5 từng màn mới biết.

Bảng bên JavaScript nay do `sinh_duong.py` viết vào giữa hai dấu mốc trong
02-trang-chu.js. Có ca kiểm đối chiếu từng byte, y như cách `dung_app_bep.py`
canh `app_bep.js`.

VÌ SAO LIỆT KÊ TỪNG ĐƯỜNG CHỨ KHÔNG BẮT TẤT
-------------------------------------------
Bắt tất kiểu `/<path:duong>` thì mọi địa chỉ lạ trên site đều rơi vào app
Bếp, kể cả các trang khách như `banh`, `btp`, `kiem-banh`, `tt`, và cả những
trang chưa ai dựng. Đó đúng là loại hook rộng mà quy tắc 6 của repo cấm.
Liệt kê từng đường thì va chạm lộ ra ngay lúc chạy ca kiểm.

THÊM MỘT MÀN MỚI THÌ LÀM GÌ
---------------------------
  1. Thêm một dòng vào `MAN` bên dưới: khoá và TÊN TIẾNG VIỆT của màn.
  2. Chạy `python3 sinh_duong.py` để máy viết lại bảng bên JavaScript.
  3. Bảo đảm `vgbGo` có nhánh cho khoá đó, nếu chưa có thì thêm.
  4. Chạy `python3 dung_app_bep.py` rồi `sh kiem_truoc_deploy.sh`.

Không phải gõ slug, không phải sửa hai chỗ.
"""

import unicodedata

# Cac ky tu tieng Viet khong tach duoc bang NFD.
DOI_RIENG = {"đ": "d", "Đ": "D", "ð": "d", "Ð": "D"}


def khong_dau(s):
	"""Bỏ dấu tiếng Việt. THUẦN.

	Dùng NFD để tách dấu ra khỏi chữ rồi bỏ phần dấu. Riêng chữ đ và Đ thì
	NFD không tách được vì nó là một chữ cái khác chứ không phải o có dấu,
	nên phải đổi tay trước.
	"""
	t = "".join(DOI_RIENG.get(c, c) for c in str(s or ""))
	t = unicodedata.normalize("NFD", t)
	return "".join(c for c in t if not unicodedata.combining(c))


def slugify(ten):
	"""Tên tiếng Việt -> slug không dấu, gạch nối, chữ thường. THUẦN.

	    "Kiểm bánh hàng ngày"  ->  "kiem-banh-hang-ngay"
	    "Hoá đơn mua"          ->  "hoa-don-mua"
	    "Đơn còn treo"         ->  "don-con-treo"

	Mọi ký tự không phải chữ hoặc số đều thành gạch nối, gạch nối liền nhau
	gộp làm một, và cắt sạch gạch nối ở hai đầu. Nhờ vậy dấu chấm, dấu phẩy,
	ngoặc, khoảng trắng kép đều không lọt vào địa chỉ.
	"""
	t = khong_dau(ten).lower()
	ra, truoc_gach = [], True
	for c in t:
		if ("a" <= c <= "z") or ("0" <= c <= "9"):
			ra.append(c)
			truoc_gach = False
		elif not truoc_gach:
			ra.append("-")
			truoc_gach = True
	return "".join(ra).rstrip("-")


# ---------------------------------------------------------------- danh mục
#
# (khoa trong vgbGo, TEN MAN HINH, slug ghi de)
#
# Slug de None thi may tu sinh tu ten. Chi ghi de khi ten tu sinh ra dung
# voi mot slug khac, hoac khi slug cu DA CHAY THAT roi nen khong duoc doi.
# Doi mot slug dang chay la lam chet moi duong dan nhan vien da luu.
#
# CHI khai nhung man mo THANG duoc, khong can du lieu cua man cha. Man chi
# tiet mot phieu thi khong khai: mo thang vao do ma khong co phieu la vo man.
MAN = (
	# --- Bán hàng và đơn khách
	("DTREO", "Đơn còn treo", None),
	("DHUY", "Đơn đã huỷ", None),
	("VD", "Vận đơn", None),
	("CPX", "Chi phí vận đơn", None),
	("DSCOD", "Đối soát COD", None),
	("DS", "Doanh số", None),
	("POS", "Bán tại quầy", None),
	("KH", "Khách hàng", None),
	("KM", "Khuyến mãi", None),
	("HDG", "Hợp đồng", None),
	("KBM", "Kiểm bánh theo mùa", None),

	# --- Thanh toán, công nợ, kế toán
	("APPTT", "Hồ sơ thanh toán", None),
	("PAY", "Thanh toán", None),
	("CN", "Công nợ", None),
	("CNPT", "Công nợ phải trả", None),
	("HT", "Hoàn tiền", None),
	("NQ", "Nộp quỹ", None),
	("HDMUA", "Hoá đơn mua", None),
	("HDBAN", "Hoá đơn bán", None),
	("DCM", "Đối chiếu mua", None),
	("CBTT", "Cảnh báo thanh toán", None),
	("PTDON", "Đơn chứng từ thu", None),
	("NHAPSK", "Nhập sao kê", None),
	("TS", "Tài sản", None),
	("BT", "Bút toán", None),
	("DNC", "Thanh toán nội bộ", None),

	# --- Mua hàng và kho
	("PO", "Đơn mua hàng", None),
	("DUYETYC", "Duyệt yêu cầu", None),
	("NCC", "Nhà cung cấp", None),
	("NCCTAO", "Tạo nhà cung cấp", None),
	("BGIA", "Bảng giá", None),
	("RCV", "Nhập kho", None),
	("NHANDC", "Hàng chuyển về kho tôi", None),
	("XKH", "Xuất huỷ", None),
	("XKD", "Xuất điều chuyển", None),
	("KK", "Kiểm kê", None),
	("STOCK", "Tồn kho", None),
	# Ton kho theo chang, them 28/08/2026. Khac man STOCK: man kia tra loi
	# "kho nay dang co gi", man nay tra loi "hang cua bep dang dung o chang
	# nao". Hai cau khong thay the nhau duoc.
	("TONCHANG", "Tồn kho theo chặng", None),
	("PTCH", "Chuyển phantom", None),

	# --- Sản xuất
	# Ten man that la "Bang bep hom nay". De ten "Bep" thi slug ra dung "bep",
	# ma "bep" chinh la route cua Web Page chua ca app. Trung la app tu nuot
	# chinh minh. Day la lan dau ca kiem trung route can duoc viec.
	("KIT", "Bảng bếp hôm nay", None),
	("MFG", "Sản xuất", None),
	("CTBOM", "Công thức", None),
	# Don tiec va B2B (them 25/08/2026). Lam theo don, khong dinh muc,
	# nen khong nam trong luong Lenh san xuat.
	("TIEC", "Đơn tiệc", None),
	# Huong dan che bien di kem moi cong thuc (them 25/08/2026). Mo tu
	# nut tren tung the o man Danh muc cong thuc, va co dia chi rieng de
	# bep truong luu dau trang tren dien thoai.
	("HDCB", "Hướng dẫn chế biến", None),
	("RND", "Nghiên cứu phát triển", None),

	# --- Báo cáo
	("BCHUB", "Báo cáo", None),

	# --- Cài đặt và quản trị
	("CDDB", "Điểm bán", None),
	("CDKS", "Khoá sổ", None),
	("CDPT", "Phương thức thanh toán", None),
	("CDTK", "Tài khoản kế toán", None),
	("CDSP", "Danh mục sản phẩm", None),
	("CDMI", "Máy in", None),
	("CDMU", "Mẫu in ấn", "mau-in"),
	("CDQQ", "Quyền quầy", None),
	("CDHT", "Hạng khách", None),
	("CDCN", "Cài đặt cuối ngày", None),
	("CDTL", "Trợ lý", None),
	("CDSE", "SePay", None),
	("CDTB", "Thông báo", None),
	("QLND", "Người dùng", None),
	("QLQ", "Phân quyền", None),
	("ACC", "Tài khoản của tôi", None),
	("OTP", "Mã OTP", None),
	("TQV", "Tặng quà khách VIP", None),

	# --- Man chung
	("VCL", "Việc cần làm", None),
)

# Muoi sau man Danh muc di chung mot nhanh `DM:` trong vgbGo. Ten lay dung
# nhu bang VGB_DM ben 02-trang-chu.js.
#
# VI SAO CA HO PHAI CO TIEN TO: ba cai ten o day TRUNG voi ten cua man khac
# trong bang MAN, va trung ten thi trung slug, ma trung slug thi mot man
# lang le nuot mat man kia:
#
#   "Nha cung cap"            DMNCC   dung voi NCC
#   "Phuong thuc thanh toan"  DMPT    dung voi CDPT
#   "Danh muc san pham"       DMSP    dung voi CDSP
#   "Tai khoan ke toan"       DMTK    dung voi CDTK
#   "Cong thuc dinh muc"      DMBOM   gan voi CTBOM
#
# Trung ten khong phai loi go nham: that su co hai man khac nhau cung ten.
# Vi du DMSP la man DUYET danh sach mat hang, con CDSP la man MO ma hang moi.
# Ho `DM:` deu la man tra cuu do khung danh sach chung dung ra, nen tien to
# "tra-cuu" vua tach duoc ten vua noi dung man do lam gi.
DANH_MUC = (
	("DMSP", "Danh mục sản phẩm"),
	("DMNSP", "Nhóm sản phẩm"),
	("DMDVT", "Đơn vị tính"),
	("DMQD", "Quy đổi đơn vị tính"),
	("DMKHO", "Kho hàng"),
	("DMBOM", "Công thức định mức"),
	("DMNCC", "Nhà cung cấp"),
	("DMNNCC", "Nhóm nhà cung cấp"),
	("DMGIA", "Bảng giá mua vào"),
	("DMKH", "Danh mục khách hàng"),
	("DMNKH", "Nhóm khách hàng"),
	("DMPT", "Phương thức thanh toán"),
	("DMNH", "Danh mục ngân hàng"),
	("DMTK", "Tài khoản kế toán"),
	("DMTHUE", "Thuế bán ra"),
	("DMTHUEM", "Thuế mua vào"),
)

# Tien to dat truoc slug cua 16 man Danh muc. Xem chu thich ngay tren.
TIEN_TO_DANH_MUC = "tra-cuu"


# Muoi hai O LON tren trang chu, tuc PHAN HE. Bam vao mot o lon thi ra danh
# sach o nho cua phan he do.
#
# VI SAO CHUNG PHAI CO MAT O DAY (anh Viet 24/08/2026)
# ----------------------------------------------------
# Anh Viet: *"anh bam vao phan he ke toan, url khong co ke-toan"*.
#
# Truoc v292 chi cac O NHO moi di qua `vgbGo`, con o lon thi man trang chu
# tu goi thang `go(function () { scrNhom(nh) })`. Khong qua vgbGo nghia la
# khong qua bang duong dan, nen dia chi dung im. Nay ca hai deu di chung mot
# cua, va khoa cua o lon mang tien to `PH:`.
#
# VI SAO PHAI CO TIEN TO `phan-he` TRONG SLUG
# --------------------------------------------
# Bon trong muoi hai ten phan he TRUNG NGUYEN VAN voi ten mot man trong bang
# MAN, va trung ten thi trung slug, ma trung slug thi mot man lang le nuot
# mat man kia - dung cai bay da phai dat tien to `tra-cuu` cho ho DM:
#
#     "San xuat"   phan he SX  dung voi man MFG
#     "Nhap kho"   phan he NK  dung voi man RCV
#     "Kiem ke"    phan he KK  dung voi man KK
#     "Bao cao"    phan he BC  dung voi man BCHUB
#
# Dat tien to cho CA MUOI HAI chu khong rieng bon cai dung: mot bang nua
# theo nua khong la bang khong ai doc duoc, va them phan he thu muoi ba
# trung ten thi lai phai nho sua tay. Co tien to thi khong bao gio trung,
# va do la mot su that may bao dam chu khong phai nguoi phai nho.
TIEN_TO_PHAN_HE = "phan-he"

# Khoa phan he phai TRUNG KHIT voi truong `k` cua VGB_NHOM ben
# 02-trang-chu.js. Co ca kiem doi chieu hai ben, doc thang tu ma nguon JS.
PHAN_HE = (
	("DH", "Đặt hàng"),
	("SX", "Sản xuất"),
	("NK", "Nhập kho"),
	("XK", "Xuất kho"),
	("KK", "Kiểm kê"),
	("BH", "Bán hàng"),
	("GH", "Giao hàng"),
	("BC", "Báo cáo"),
	("TM", "Thu mua"),
	("KT", "Kế toán"),
	("DM", "Danh mục"),
	("KHAC", "Cài đặt"),
)

# Nhung slug DA CHAY THAT tren site tu v284 den v287. Doi bat ky dong nao o
# day la lam chet duong dan nhan vien da luu va da gui cho nhau. Ca kiem
# `thu_duong_app.py` chot cung bang nay, sua bang thi ca kiem do ngay.
SLUG_DA_CHAY = {
	"don-con-treo": "DTREO",
	"don-da-huy": "DHUY",
	"ho-so-thanh-toan": "APPTT",
	"cong-no-phai-tra": "CNPT",
	"hoa-don-mua": "HDMUA",
	"hoa-don-ban": "HDBAN",
	"doi-chieu-mua": "DCM",
	"don-mua-hang": "PO",
	"duyet-yeu-cau": "DUYETYC",
	"nha-cung-cap": "NCC",
	"bang-gia": "BGIA",
	"nhap-kho": "RCV",
	"kiem-ke": "KK",
	"san-xuat": "MFG",
	"cong-thuc": "CTBOM",
	"ton-kho": "STOCK",
	"doanh-so": "DS",
	"bao-cao": "BCHUB",
	"cong-no": "CN",
	"hoan-tien": "HT",
	"nop-quy": "NQ",
	"khach-hang": "KH",
	"van-don": "VD",
	"khuyen-mai": "KM",
	"hop-dong": "HDG",
	"thanh-toan": "PAY",
}

# Web Page dang co tren site, KHONG duoc dat slug trung. Lay tu ban ghi that
# ngay 23/08/2026, ke ca trang chua xuat ban, vi trang chua xuat ban van giu
# cho duong dan do.
ROUTE_DA_CO = (
	"banh", "bep", "btp", "cuon-ma", "in-tem", "kho-moi", "kho-v2",
	"kiem-banh", "luu-banh-20260806-v3", "ong-trang", "sop-san-xuat",
	"suc-khoe", "tt", "xhd",
	"zz-sao-luu-app-bep-03082026-1600",
	"zz-sao-luu-banh-20260822-truoc-v272",
	"zz-sao-luu-banh-20260822-truoc-v273",
	"zz-sao-luu-bep-04-08",
	"zz-sao-luu-bep-v73-07-08",
)

# Web Page chua chinh app Bep. F5 tai bat ky slug nao deu duoc tra ve trang
# nay, roi may khach doc location.pathname de mo dung man.
TRANG_APP = "bep"


def _cap_duong():
	"""Sinh từng cặp (slug, khoá) từ danh mục. THUẦN.

	Tách riêng để `bang_duong()` và ca kiểm trùng slug dùng chung, và để ca
	kiểm nhìn được TỪNG cặp trước khi chúng bị gộp vào dict, vì gộp vào dict
	là lúc một slug trùng lặng lẽ nuốt mất slug kia.
	"""
	for khoa, ten, ghi_de in MAN:
		yield (ghi_de or slugify(ten)), khoa
	for ma, ten in DANH_MUC:
		yield "%s-%s" % (TIEN_TO_DANH_MUC, slugify(ten)), "DM:" + ma
	for ma, ten in PHAN_HE:
		yield "%s-%s" % (TIEN_TO_PHAN_HE, slugify(ten)), "PH:" + ma


def bang_duong():
	"""Bảng slug -> khoá màn hình. THUẦN, không chạm Frappe."""
	return dict(_cap_duong())


# Giu ten cu de moi cho goi tu truoc khong phai sua.
DUONG = bang_duong()


def luat_dinh_tuyen():
	"""Danh sách cho hook `website_route_rules`. THUẦN, không chạm Frappe."""
	return [{"from_route": "/" + s, "to_route": TRANG_APP} for s in sorted(DUONG)]


# ------------------------------------------------------------ sinh bảng JS

MOC_DAU = "/* === BANG DUONG DAN: MAY SINH RA, DUNG SUA TAY === */"
MOC_CUOI = "/* === HET BANG DUONG DAN === */"


def sinh_js():
	"""Đoạn JavaScript khai bảng đường dẫn, kể cả hai dấu mốc. THUẦN.

	`sinh_duong.py` ghi đoạn này vào 02-trang-chu.js, và ca kiểm đối chiếu
	đoạn đang nằm trong tệp với đoạn hàm này sinh ra. Lệch một byte là ca
	kiểm đỏ, y như cách `dung_app_bep.py --kiem` canh `app_bep.js`.
	"""
	dong = [MOC_DAU]
	dong.append("/* Nguon that: vagabond/duong_app.py, bang MAN va DANH_MUC.")
	dong.append("   Sua ben do roi chay: python3 sinh_duong.py")
	dong.append("   Sua tay o day thi ca kiem thu_duong_app.py do ngay. */")
	dong.append("var VGB_DUONG = {")
	cap = sorted(bang_duong().items())
	for i, (slug, khoa) in enumerate(cap):
		dau_phay = "," if i < len(cap) - 1 else ""
		dong.append("  '%s': '%s'%s" % (slug, khoa, dau_phay))
	dong.append("};")
	dong.append(MOC_CUOI)
	return "\n".join(dong)

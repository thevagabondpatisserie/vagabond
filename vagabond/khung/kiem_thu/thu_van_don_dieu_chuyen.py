"""Ca kiểm cho vận đơn điều chuyển kho nội bộ, làm ngày 04/09/2026.

Anh Việt: *"Phần PĐC và YCĐC khi tạo bên màn Vận Đơn bị thiếu các trường thông
tin, điều chuyển từ kho nào đến kho nào, hàng hoá là gì, nối file phiếu điều
chuyển sang vận đơn để in ấn ra"*.

Trước bản này không hề có đường nối nào giữa phiếu điều chuyển và vận đơn.
Người ta mở màn Vận đơn, bấm dấu cộng, GÕ TAY số phiếu vào ô "Số đơn" và gõ
tên kho vào ô "Khách". Đo trên dữ liệu thật ngày 04/09: 146 vận đơn điều
chuyển, tất cả đều "Chờ giao", không tờ nào có shipper; hai tờ trỏ vào phiếu
đã bị huỷ; ô Khách và ô Địa chỉ cùng mang tên kho NHẬN nên kho XUẤT không nằm
ở đâu cả; bảng hàng rỗng nên tờ in ra trống phần hàng.

Anh Việt chốt 04/09/2026: chỉ phiếu điều chuyển mới sinh vận đơn, yêu cầu điều
chuyển thì không; 146 tờ cũ bỏ qua, chỉ làm cho tương lai.

Mọi ca chạy trên phép THUẦN và trên văn bản tệp: không cần Frappe thật, không
cần site, không cần mạng, không cần thư viện requests.
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


# ------------------------------------------------------ Địa chỉ thật của kho


@ca("dieu chuyen: dia chi khai tren phieu an tren moi phep doan")
def _dia_chi_khai_uu_tien():
	from vagabond import van_don as vd

	la("co khai thi dung ngay", vd.dia_chi_kho("Kho tổng 307 - TV", "12 Lê Lợi, Q1"), "12 Lê Lợi, Q1")
	la("khoang trang thua khong tinh la co khai",
		vd.dia_chi_kho("Kho D1 - TV", "   "), "9 Trần Cao Vân, Quận 1")


@ca("dieu chuyen: doan dia chi theo ten kho, do khong ra thi ve xuong")
def _doan_dia_chi_theo_ten():
	from vagabond import van_don as vd

	la("kho D1", vd.dia_chi_kho("Kho D1 - TV"), "9 Trần Cao Vân, Quận 1")
	la("kho NVHTN", vd.dia_chi_kho("Kho NVHTN - TV"), "21 Phạm Ngọc Thạch, Quận 3")
	la("kho tong ve xuong", vd.dia_chi_kho("Kho tổng 307 - TV"), vd.DC_DIA_CHI_MAC_DINH)
	la("kho Pastry ve xuong", vd.dia_chi_kho("Pastry - Nguyên liệu - TV"), vd.DC_DIA_CHI_MAC_DINH)
	# Khong bao gio duoc tra ve chuoi rong: to in khong co dia chi thi shipper
	# khong biet di dau, ma cai do khong bao gio duoc phep xay ra.
	for x in ("", None, "Kho la hoac"):
		dung("kho la van co dia chi", bool(vd.dia_chi_kho(x)))


@ca("dieu chuyen: ten kho ngan bo duoi cong ty, hai ben JS va may chu giong nhau")
def _ten_kho_ngan():
	from vagabond import van_don as vd

	la("bo duoi TV", vd._ten_kho_ngan("Kho tổng 307 - TV"), "Kho tổng 307")
	la("bo duoi TVD", vd._ten_kho_ngan("Stores - TVD"), "Stores")
	la("khong co duoi thi giu nguyen", vd._ten_kho_ngan("Kho Lab"), "Kho Lab")
	la("rong van an toan", vd._ten_kho_ngan(None), "")
	js = _js("12-van-don.js")
	dung("ben JS co ham cung luat", "function vdKhoNgan(t)" in js)
	dung("JS dung dung hai duoi TVD va TV", "(TVD|TV)$" in js)


# ------------------------------------------------------ Đoán điều kiện bảo quản


@ca("dieu chuyen: doan dung dieu kien bao quan theo tien to ma hang")
def _doan_bao_quan():
	from vagabond import van_don as vd

	la("co hang dong thi ca lo di dong", vd.doan_bao_quan(["NVLT00264", "NVLD00012"]), ("Đông", 45))
	la("co hang mat thi di mat", vd.doan_bao_quan(["NVLM00099", "CCDC00255"]), ("Mát", 120))
	la("toan hang thuong", vd.doan_bao_quan(["NVLT00264", "CCDC00255"]), ("Thường", 0))
	la("lo rong van tra ve duoc", vd.doan_bao_quan([]), ("Thường", 0))
	# Dong an tren mat: mot lo co ca hai thi phai di theo cai KHAT khe hon.
	la("dong an tren mat", vd.doan_bao_quan(["NVLM00099", "NVLD00012"]), ("Đông", 45))


@ca("dieu chuyen: tran thoi gian ngoai lanh khai du ca ba kieu")
def _tran_thoi_gian():
	from vagabond import van_don as vd

	for k in vd.DC_BAO_QUAN:
		dung("co tran cho %s" % k, k in vd.DC_PHUT_NGOAI_LANH)
	dung("hang thuong khong co tran", vd.DC_PHUT_NGOAI_LANH["Thường"] == 0)
	dung("hang dong khat khe hon hang mat",
		vd.DC_PHUT_NGOAI_LANH["Đông"] < vd.DC_PHUT_NGOAI_LANH["Mát"])


# ------------------------------------------------------ Hàng rào lúc lập phiếu


@ca("dieu chuyen: CHI phieu da ghi so va dung chieu moi lap duoc van don")
def _hang_rao_lap_phieu():
	from vagabond import van_don as vd

	class G(dict):
		def get(self, k, m=None):
			return dict.get(self, k, m)

		@property
		def name(self):
			return self["name"]

	tot = G(name="PDC-1", purpose="Material Transfer", docstatus=1,
		from_warehouse="A", to_warehouse="B")
	la("phieu tot thi qua", vd._kho_chan(tot), "")

	xau = G(dict(tot), purpose="Material Issue")
	dung("phieu xuat huy bi chan", "không phải phiếu điều chuyển" in vd._kho_chan(xau))

	nhap = G(dict(tot), docstatus=0)
	dung("phieu chua ghi so bi chan", "chưa ghi sổ" in vd._kho_chan(nhap))
	huy = G(dict(tot), docstatus=2)
	dung("phieu da huy bi chan", "chưa ghi sổ hoặc đã huỷ" in vd._kho_chan(huy))

	thieu = G(dict(tot), to_warehouse=None)
	dung("thieu kho nhan bi chan", "không ghi rõ kho xuất hoặc kho nhận" in vd._kho_chan(thieu))
	trung = G(dict(tot), to_warehouse="A")
	dung("hai kho trung nhau bi chan", "trùng nhau" in vd._kho_chan(trung))


@ca("dieu chuyen: YCDC KHONG duoc sinh van don")
def _ycdc_khong_sinh_van_don():
	# Anh Viet chot 04/09/2026. Yeu cau dieu chuyen la Material Request, chi
	# la loi de nghi, hang chua roi kho. Cua ngo chi nhan Stock Entry.
	s = _doc("van_don.py")
	i = s.index("def tao_van_don_dieu_chuyen(")
	than = s[i:i + 3500]
	dung("chi doc Stock Entry", 'frappe.db.exists("Stock Entry", phieu)' in than)
	dung("khong dong toi Material Request", "Material Request" not in than)
	dung("co ghi ro quyet dinh trong tep", "Yeu cau dieu" in s and "KHONG" in s)


@ca("dieu chuyen: mot phieu chi mot van don, bam hai lan khong ra hai to")
def _mot_phieu_mot_van_don():
	s = _doc("van_don.py")
	dung("co ham do rieng", "def van_don_cua_phieu(" in s)
	i = s.index("def tao_van_don_dieu_chuyen(")
	than = s[i:i + 3500]
	dung("co do van don cu truoc khi lap", "cu = van_don_cua_phieu(phieu)" in than)
	dung("tra ve to cu chu khong nem loi", '"da_co": 1' in than)


@ca("dieu chuyen: do trung theo CA HAI o, bat duoc ca van don go tay cu")
def _do_trung_ca_hai_o():
	# 146 van don lap truoc v411 deu go tay: so phieu nam trong `ma_don`, o
	# `chung_tu_goc` rong. Do bang mot o thi khong thay chung, va bam nut se
	# sinh to thu hai cho cung mot phieu. Do that sau khi deploy v411:
	# trong 30 phieu bay ra cho nguoi ta bam thi 27 phieu DA CO van don cu.
	s = _doc("van_don.py")
	i = s.index("def van_don_cua_phieu(")
	than = s[i:i + 1600]
	dung("do o noi goc", '{"chung_tu_goc": phieu}' in than)
	dung("do ca o so don go tay", '{"ma_don": phieu}' in than)
	dung("bo qua to da huy", 'loc["trang_thai"] = ["!=", "Huỷ"]' in than)
	dung("phieu rong thi tra ve rong ngay", 'if not phieu:' in than)

	j = s.index("def phieu_dieu_chuyen_lap_duoc(")
	than2 = s[j:j + 2600]
	dung("danh sach de bam cung do ca hai o",
		'for o in ("chung_tu_goc", "ma_don"):' in than2)


# ------------------------------------------------------ Chặn giao nhầm


@ca("dieu chuyen: chan gan shipper khi phieu goc da huy")
def _chan_gan_shipper():
	s = _doc("van_don.py")
	i = s.index("def gan_shipper(")
	than = s[i:i + 2600]
	dung("co doc lai phieu goc", 'frappe.db.get_value("Stock Entry", doc.chung_tu_goc, "docstatus")' in than)
	dung("bat ca truong hop phieu bien mat", "ds_goc is None" in than)
	dung("nem loi ro rang", "đã bị huỷ nên không phân công giao được" in than)
	dung("ghi lai trang thai vao van don", 'set_value("Van Don", doc.name, "tt_chung_tu"' in than)


@ca("dieu chuyen: huy phieu kho thi van don tu dong")
def _huy_phieu_thi_dong_van_don():
	s = _doc("van_don.py")
	dung("co ham dong", "def dong_van_don_khi_huy_phieu(" in s)
	i = s.index("def dong_van_don_khi_huy_phieu(")
	than = s[i:]
	dung("chi dong to con song", '"trang_thai": ["in", ["Chờ giao", "Đang giao"]]' in than)
	dung("ghi ly do de sau con truy", "đã bị huỷ nên vận đơn tự đóng" in than)
	dung("khong bao gio nem loi ra ngoai", "except Exception" in than)
	h = _doc("hooks.py")
	dung("hook dat dung doctype Stock Entry", '"vagabond.van_don.dong_van_don_khi_huy_phieu"' in h)
	dung("hook dat o on_cancel", '"on_cancel": "vagabond.van_don.dong_van_don_khi_huy_phieu"' in h)


# ------------------------------------------------------ Màn hình và tờ in


@ca("man kho: co nut lap van don ngay tren phieu dieu chuyen")
def _nut_tren_phieu_kho():
	js = _js("03-kho-chung-tu.js")
	dung("co nut", "vxVanDon" in js)
	dung("goi dung cua ngo", "vagabond.van_don.tao_van_don_dieu_chuyen" in js)
	dung("chi bay khi phieu da ghi so va khong phai phieu huy",
		"d.docstatus === 1 && !laHuy) {\n    nut += '<button class=\"vxb\" id=\"vxVanDon\"" in js)


@ca("man van don: dong danh sach bay CA HAI dau, khong chi noi giao")
def _dong_danh_sach_du_hai_dau():
	js = _js("12-van-don.js")
	dung("co nhanh rieng cho don dieu chuyen", "r.la_dieu_chuyen" in js)
	dung("bay noi lay", "📤 Lấy: " in js)
	dung("bay noi giao", "📥 Giao: " in js)
	dung("huy hieu canh bao phieu goc da huy", "⛔ Phiếu gốc đã huỷ" in js)


@ca("to in: gop phieu dieu chuyen vao chinh to van don")
def _to_in_gop_phieu():
	js = _js("12-van-don.js")
	dung("doi tieu de to in", "Phiếu điều chuyển nội bộ" in js)
	dung("in kho xuat kem dia chi lay", "Kho xuất · nơi lấy hàng" in js)
	dung("in kho nhan kem dia chi giao", "Kho nhận · nơi giao hàng" in js)
	dung("co ma vach so phieu", "d.ma_vach" in js)
	dung("bo khoi COD khoi to dieu chuyen", "if (!laDC) {" in js)
	dung("hai dong ky deu co gio", "Người nhận ký · giờ" in js)


@ca("to in: don dieu chuyen KHONG in gia tien")
def _to_in_khong_in_gia():
	# Hang di trong noi bo. In tien ra chi lam nguoi cam to giay tuong day la
	# don ban, va lo mat gia von noi bo ra ngoai neu to giay di lac.
	js = _js("12-van-don.js")
	dung("cot cuoi doi thanh don vi va o tick", "'Đơn vị · nhận đủ' : 'Thành tiền'" in js)
	s = _doc("van_don.py")
	i = s.index("def tao_van_don_dieu_chuyen(")
	dung("luu gia bang 0", '"gia": 0,' in s[i:i + 3500])


@ca("may chu: keo du cac o dieu chuyen ra danh sach va to in")
def _keo_du_o():
	s = _doc("van_don.py")
	i = s.index("TRUONG_DS = [")
	khoi = s[i:i + 1400]
	for o in ("la_dieu_chuyen", "chung_tu_goc", "tt_chung_tu", "kho_xuat",
			"kho_nhan", "dia_chi_lay", "so_kien", "bao_quan", "phut_ngoai_lanh"):
		dung("TRUONG_DS co o %s" % o, '"%s"' % o in khoi)


@ca("doctype: da khai du cac o moi cua van don dieu chuyen")
def _doctype_du_o():
	p = os.path.join(GOI, "vagabond", "doctype", "van_don", "van_don.json")
	with io.open(p, encoding="utf-8") as f:
		d = json.load(f)
	ten = {x["fieldname"]: x for x in d["fields"]}
	for o in ("la_dieu_chuyen", "chung_tu_goc", "tt_chung_tu", "kho_xuat",
			"kho_nhan", "dia_chi_lay", "nguoi_giao", "sdt_giao", "so_kien",
			"bao_quan", "phut_ngoai_lanh"):
		dung("doctype co o %s" % o, o in ten)
		dung("o %s nam trong field_order" % o, o in d["field_order"])
	la("chung tu goc tro vao Stock Entry", ten["chung_tu_goc"]["options"], "Stock Entry")
	la("kho xuat tro vao Warehouse", ten["kho_xuat"]["options"], "Warehouse")
	la("kho nhan tro vao Warehouse", ten["kho_nhan"]["options"], "Warehouse")
	la("bao quan du ba lua chon", ten["bao_quan"]["options"], "Thường\nMát\nĐông")
	la("so o bang so dong field_order", len(d["fields"]), len(d["field_order"]))


@ca("cua ngo: da ghi ten ba ham moi cua van don dieu chuyen")
def _cua_ngo_du_ten():
	s = _doc(os.path.join("khung", "kiem_thu", "thu_cua_ngo.py"))
	for t in ("tao_van_don_dieu_chuyen", "phieu_dieu_chuyen_lap_duoc", "luu_dieu_chuyen"):
		dung("cua ngo co %s" % t, '"%s"' % t in s)


@ca("sua tay: nguoi lap luon doi duoc thu may doan sai")
def _sua_tay_duoc():
	s = _doc("van_don.py")
	i = s.index("def luu_dieu_chuyen(")
	than = s[i:]
	dung("chan doi to da giao hoac da huy", 'doc.trang_thai in ("Đã giao", "Huỷ")' in than)
	dung("chan gia tri bao quan la", "phải là một trong" in than)
	dung("go tay so phut thi giu so nguoi go", "if phut_ngoai_lanh is None:" in than)
	dung("so kien khong am", "max(0, cint(so_kien))" in than)
	js = _js("12-van-don.js")
	dung("man hinh co nut sua", "data-va=\"suadc\"" in js)
	dung("co ham sua", "async function vdSuaDieuChuyen(d)" in js)


@ca("sua tay: khong dung o xo danh sach, va tran thoi gian hai ben trung nhau")
def _chip_va_tran_trung_nhau():
	from vagabond import van_don as vd

	js = _js("12-van-don.js")
	dung("dung hang chip chu khong phai o xo", "data-dcbq=" in js)
	dung("khong khai o xo trong man sua", "'<select class=\"hin\" id=\"dcBq\"" not in js)
	# Man hinh hua mot dang ma to in ghi mot dang khac la loi kho thay nhat:
	# khong ai bao loi, chi co lo hang hong. Chot cung hai ben.
	import re as _re

	m = _re.search(r"var VD_PHUT_LANH = \{([^}]*)\}", js)
	dung("JS co khai tran thoi gian", bool(m))
	for k, v in vd.DC_PHUT_NGOAI_LANH.items():
		dung("JS khai dung tran cua %s" % k, "'%s': %d" % (k, v) in m.group(1))

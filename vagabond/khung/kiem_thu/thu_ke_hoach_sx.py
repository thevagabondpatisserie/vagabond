# -*- coding: utf-8 -*-
"""Kế hoạch sản xuất trong ngày (anh Việt giao 28/08/2026).

Điều kiện anh Việt đặt là "sử dụng tính năng lập kế hoạch sản xuất trên bản
desk để làm cho app, luôn đồng bộ giữa 2 bản, không đẻ thêm doctype". Nên ca
kiểm ở đây canh đúng ba chỗ dễ trượt khỏi điều kiện đó:

1. Không có doctype mới nào, và mọi phép nổ BOM đều gọi sang Production Plan
   của ERPNext chứ không tự tính. Tự tính một con số là hai bản bắt đầu lệch,
   mà lúc lệch thì không ai biết bên nào đúng.
2. Danh sách YCSX lọc theo `schedule_date` (ngày hẹn giao) chứ không theo
   `transaction_date` (ngày lập). Hàm sẵn có của ERPNext lọc theo ngày lập,
   dùng nguyên nó là phiếu rơi vào kế hoạch sai ngày.
3. Nhịp nửa đêm chạy lại không sinh phiếu thứ hai, và phiếu để dạng NHÁP.
"""

import io
import re
import os

from vagabond import ke_hoach_sx as kh
from vagabond.khung.kiem_thu.nen import ca, dung, la


# Ba lan dirname tu tep nay ra dung thu muc goi `vagabond/`, KHONG phai goc
# repo. Noi them mot doan "vagabond" nua la thanh vagabond/vagabond/ va moi ca
# kiem doc tep deu no.
GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten),
		encoding="utf-8").read()


# ------------------------------------------------------ phép còn phải làm


@ca("còn phải làm bằng cần trừ tồn")
def _():
	la("thiếu 4", kh.con_phai_lam(10, 6), 4.0)
	la("vừa đủ", kh.con_phai_lam(10, 10), 0.0)


@ca("dư hàng KHÔNG ra số âm")
def _():
	# Am mot me la con so vo nghia, ma no se chay thang vao o so luong cua
	# lenh san xuat.
	la("dư", kh.con_phai_lam(10, 25), 0.0)
	la("không tồn nào", kh.con_phai_lam(0, 5), 0.0)


@ca("số rỗng hay None coi như 0, không nổ")
def _():
	la("cần None", kh.con_phai_lam(None, 5), 0.0)
	la("tồn None", kh.con_phai_lam(7, None), 7.0)
	la("chuỗi rác", kh.con_phai_lam("bậy", 3), 0.0)


# ------------------------------------------------------------ chip trạng thái


@ca("chưa có công thức thắng mọi chip khác")
def _():
	# Dong do may khong tinh duoc gi ca, gan chip "du ton" len no la noi doi.
	la("dù đủ tồn", kh.muc_cua(5, 100, 0, co_bom=False), kh.MUC_CHUA_BOM)
	la("dù thiếu", kh.muc_cua(5, 0, 0, co_bom=False), kh.MUC_CHUA_BOM)


@ca("đã có lệnh đủ số thì không giục làm nữa")
def _():
	# Bam tao lenh lan nua la ra hai lenh cho mot me.
	la("lệnh phủ hết", kh.muc_cua(10, 0, 10), kh.MUC_DA_CO_LENH)
	la("lệnh cộng tồn phủ hết", kh.muc_cua(10, 4, 6), kh.MUC_DA_CO_LENH)


@ca("lệnh chưa phủ hết thì báo thiếu một phần")
def _():
	la("mới ra 3 trên 10", kh.muc_cua(10, 0, 3), kh.MUC_MOT_PHAN)


@ca("đủ tồn và thiếu tồn phân biệt đúng")
def _():
	la("đủ", kh.muc_cua(10, 12), kh.MUC_DU)
	la("thiếu", kh.muc_cua(10, 2), kh.MUC_THIEU)


@ca("mọi chip đều có tên tiếng Việt và màu")
def _():
	for m in (kh.MUC_DU, kh.MUC_THIEU, kh.MUC_MOT_PHAN, kh.MUC_DA_CO_LENH,
			kh.MUC_CHUA_BOM):
		dung("tên %s" % m, bool(kh.TEN_MUC.get(m)))
		dung("màu %s" % m, kh.MAU_MUC.get(m) in ("n", "w", "g", "r"))


# ------------------------------------------------------------- gom theo mã


DONG = [
	{"ma": "BAWC00001", "ten": "Bánh A", "dvt": "Cái", "sl": 4, "nguon": "Kho D1 - TV"},
	{"ma": "BAWC00001", "ten": "Bánh A", "dvt": "Cái", "sl": 6, "nguon": "Kho Sales Online - TV"},
	{"ma": "BAWC00002", "ten": "Bánh B", "dvt": "Cái", "sl": 2, "nguon": "Kho D1 - TV"},
]


@ca("cùng một mã ở hai điểm bán thì cộng lại thành một dòng")
def _():
	r = kh.gom_theo_ma(DONG)
	la("số dòng", len(r), 2)
	la("mã A cộng lại", r[0]["sl"], 10.0)


@ca("gom xong vẫn giữ được số của từng điểm bán")
def _():
	# Gom ma danh mat nguon thi luc con so trong la khong ai truy lai duoc.
	r = kh.gom_theo_ma(DONG)
	n = {x["ten"]: x["sl"] for x in r[0]["nguon"]}
	la("D1", n.get("Kho D1 - TV"), 4.0)
	la("Sales Online", n.get("Kho Sales Online - TV"), 6.0)


@ca("dòng thiếu mã bị bỏ qua chứ không tạo mã rỗng")
def _():
	r = kh.gom_theo_ma(DONG + [{"ma": "", "sl": 99}])
	la("vẫn hai dòng", len(r), 2)


# ----------------------------------------------------------- câu tóm tắt


@ca("không có YCSX thì nói rõ kế hoạch trống là đúng")
def _():
	c = kh.cau_tom_tat(0, 0, 0, 0, 0)
	dung("phải trấn an", "không phải máy sót" in c)


@ca("câu tóm tắt đếm đủ ba khối và nhắc số mã thiếu")
def _():
	c = kh.cau_tom_tat(5, 12, 30, 4, 3)
	dung("đủ phiếu", "4 phiếu yêu cầu" in c)
	dung("thành phẩm", "5 thành phẩm" in c)
	dung("bán thành phẩm", "12 bán thành phẩm" in c)
	dung("nguyên liệu", "30 nguyên liệu" in c)
	dung("mã thiếu", "3 mã thiếu" in c)


# ------------------------------- điều kiện anh Việt: không đẻ doctype mới


@ca("KHÔNG khai doctype mới nào, chỉ thêm ô vào Production Plan có sẵn")
def _():
	m = _py("ke_hoach_sx.py")
	la("không tạo doctype", 'doctype": "DocType"' in m, False)
	la("không tạo Custom DocPerm lạ", "new_doc(\"DocType\"" in m, False)
	dung("ô mới gắn lên Production Plan", "Production Plan" in str(kh.TRUONG_MOI))
	la("chỉ một doctype được thêm ô", len(kh.TRUONG_MOI), 1)


@ca("mọi phép nổ BOM gọi sang ERPNext, không tự tính")
def _():
	# Tu tinh mot con so la hai ban bat dau lech, ma luc lech khong ai biet
	# ben nao dung.
	m = _py("ke_hoach_sx.py")
	for ham in ("get_items()", "get_sub_assembly_items()",
			"get_items_for_material_requests", "create_work_order",
			"prepare_data_for_sub_assembly_items", "make_material_request()"):
		dung("phải gọi %s của ERPNext" % ham, ham in m)


@ca("không tự dựng Work Order bằng tay")
def _():
	# Dung tay thi so luong, kho va cach tru phan da co lenh se khac nut cua
	# Desk, hai ban lech nhau ngay tuan sau.
	m = _py("ke_hoach_sx.py")
	la("không new_doc Work Order", 'new_doc("Work Order")' in m, False)


# ------------------------------------- lọc YCSX theo ngày hẹn, không ngày lập


@ca("YCSX lọc theo ngày HẸN GIAO chứ không theo ngày lập phiếu")
def _():
	# get_pending_material_requests cua ERPNext loc theo transaction_date.
	# Dung nguyen no thi phieu lap hom nay hen ngay kia roi vao ke hoach sai
	# ngay. Day la ly do o day tu chon danh sach YCSX.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def ycsx_can_lam")[1].split("\ndef ")[0]
	dung("phải lọc schedule_date", "mri.schedule_date" in doan)
	la("không được lọc theo ngày lập", "mr.transaction_date <=" in doan, False)


@ca("chỉ lấy phần YCSX còn dư, phần đã ra lệnh thì thôi")
def _():
	# Khong tru phan da ra lenh thi bep lam gap doi.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def ycsx_can_lam")[1].split("\ndef ")[0]
	dung("phải trừ ordered_qty", "mri.qty > ifnull(mri.ordered_qty, 0)" in doan)


@ca("bỏ qua phiếu đã dừng hoặc đã huỷ")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def ycsx_can_lam")[1].split("\ndef ")[0]
	dung("phải bỏ Stopped và Cancelled", "'Stopped', 'Cancelled'" in doan)


@ca("đơn quá hạn được gắn dấu để bếp nhìn ra")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def ycsx_can_lam")[1].split("\ndef ")[0]
	dung("phải gắn cờ quá hạn", '"qua_han"' in doan)


# ------------------------------------------------ nhịp nửa đêm và trạng thái


@ca("chạy lại nhịp nửa đêm KHÔNG sinh phiếu thứ hai")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def lap(")[1].split("\ndef ")[0]
	dung("phải hỏi phiếu đã có chưa", "_phieu_cua_ngay(ngay)" in doan)
	dung("có rồi thì trả lại phiếu cũ", '"da_co": 1' in doan)


@ca("lập phiếu chạy thử là mặc định")
def _():
	m = _py("ke_hoach_sx.py")
	dung("mặc định chạy thử", "def lap(ngay=None, chay_that=0" in m)


@ca("phiếu tự sinh để dạng NHÁP, không tự ghi sổ")
def _():
	# Anh Viet chot 28/08/2026: 5h sang bep doc roi tu bam Chot.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def lap(")[1].split("\ndef ")[0]
	dung("chỉ insert", "doc.insert()" in doan)
	la("không được submit", "doc.submit()" in doan, False)


@ca("nhịp nửa đêm lấy đúng NGÀY VỪA SANG, không cộng thêm một ngày")
def _():
	# Chay luc 00:00 nen "ngay mai" theo cach noi cua anh Viet chinh la hom
	# nay theo dong ho may. Cong them mot ngay la bep 5h sang mo ra thay ke
	# hoach cua ngay kia.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tu_lap_nua_dem")[1].split("\ndef ")[0]
	dung("phải dùng nowdate", "lap(nowdate()" in doan)
	la("không được cộng ngày", "ngay_mai()" in doan, False)


@ca("nhịp nửa đêm hỏng thì ghi Error Log, không kéo đổ cả bộ lập lịch")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tu_lap_nua_dem")[1].split("\ndef ")[0]
	dung("phải bọc try", "except Exception" in doan)
	dung("phải ghi log", "log_error" in doan)


@ca("hai nhịp đã nối vào hooks.py")
def _():
	m = _py("hooks.py")
	dung("nhịp 0h lập phiếu", '"0 0 * * *": ["vagabond.ke_hoach_sx.tu_lap_nua_dem"]' in m)
	dung("nhịp 5h nhắc bếp", "vagabond.ke_hoach_sx.nhac_bep_sang" in m)


# ------------------------------------------------------ tạo lệnh từng dòng


@ca("phiếu còn nháp thì máy TỰ ghi sổ, không bắt bếp bấm chốt tổng")
def _():
	# Anh Viet 29/08/2026 bo nut chot tong: bep khong chot ca phieu mot
	# luot duoc, ma chot xong cung khong biet phieu nam dau. Buoc ghi so
	# lui xuong server, chay ngam o lan ra lenh dau tien.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tao_lenh(")[1].split("def _goc(")[0]
	dung("gọi bước ghi sổ ngầm", "_chot_ngam(ten)" in doan)
	dung("báo lại cho bếp biết phiếu vừa ghi sổ", "cũng vừa được ghi sổ" in doan)
	ngam = m.split("def _chot_ngam(")[1].split("\ndef ")[0]
	dung("phiếu đã huỷ thì dừng", "đã huỷ" in ngam)
	dung("phiếu đã ghi sổ thì thôi", "return 0" in ngam)


@ca("chia số lượng: gõ đúng số máy cần thì mỗi dòng nhận đúng phần của nó")
def _():
	phan, doi = kh.chia_so_luong([10, 20, 5], 35)
	la("chia đủ", phan, [10, 20, 5])
	la("không dôi", doi, 0.0)


@ca("chia số lượng: gõ ÍT hơn thì rót lần lượt, dòng sau chờ lệnh lần tới")
def _():
	phan, doi = kh.chia_so_luong([10, 20, 5], 12)
	la("dòng đầu đủ, dòng hai được phần còn lại", phan, [10, 2, 0.0])
	la("không dôi", doi, 0.0)


@ca("chia số lượng: gõ NHIỀU hơn thì phần dôi tách riêng, không nhét vào phiếu nào")
def _():
	# Nhet phan doi vao mot phieu yeu cau bat ky la lam sai so cua diem
	# ban do, va phieu ay tu dong som trong khi hang chua giao du.
	phan, doi = kh.chia_so_luong([10, 20], 40)
	la("mỗi dòng vẫn đúng phần của nó", phan, [10, 20])
	la("phần dôi để riêng", doi, 10.0)


@ca("lệnh cho phần dôi ra bị CẮT mọi mối nối về phiếu yêu cầu")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def _tao_mot_lenh(")[1].split("\n\n@frappe")[0]
	dung("có cờ rời phiếu", "roi_phieu" in doan)
	dung("cắt mối nối phiếu yêu cầu", 'None if roi_phieu else d.material_request' in doan)
	dung("cắt cả mối nối dòng kế hoạch", 'None if roi_phieu else d.name' in doan)


@ca("chọn bếp lấy ứng viên đầu tiên có giá trị")
def _():
	la("bỏ qua ô rỗng", kh.chon_bep("", None, "Pastry"), "pastry")
	la("ứng viên đầu thắng", kh.chon_bep("baker", "pastry"), "baker")
	la("không có gì thì trả rỗng", kh.chon_bep("", None, "  "), "")


@ca("tạo lệnh trừ phần đã ra lệnh, không ra hai lệnh cho một mẻ")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tao_lenh")[1].split("\n@frappe")[0]
	dung("thành phẩm trừ ordered_qty", "flt(d.planned_qty) - flt(d.ordered_qty)" in doan)
	dung("bán thành phẩm cũng trừ", "flt(d.qty) - flt(d.ordered_qty)" in doan)


@ca("kho mặc định phải sửa TẠI CHỖ, không truyền bản sao")
def _():
	# set_default_warehouses sua tai cho. Truyen frappe._dict(mon) la mot ban
	# sao moi, sua xong roi vut di, kho mac dinh khong bao gio vao lenh.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tao_lenh")[1].split("\n@frappe")[0]
	dung("truyền đúng đối tượng", "set_default_warehouses(mon, kho_mac_dinh)" in doan)
	la("không bọc bản sao", "set_default_warehouses(frappe._dict(mon)" in doan, False)


# ------------------------------------------- xin chuyển NVL từ kho tổng


@ca("phiếu xin chuyển nguyên liệu lấy hàng từ Kho tổng 307")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xin_chuyen_nvl")[1].split("\n@frappe")[0]
	dung("phải là chuyển kho", '"Material Transfer"' in doan)
	dung("nguồn là kho gốc", "ksx.KHO_GOC" in doan)


@ca("phiếu xin chuyển sinh ra ở dạng nháp, chờ người giữ kho xem")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xin_chuyen_nvl")[1].split("\n@frappe")[0]
	dung("lọc docstatus 0", '"docstatus": 0' in doan)
	la("không tự ghi sổ", ".submit()" in doan, False)


# ------------------------------------------------ giữ chỗ: KHÔNG tự bật


@ca("KHÔNG tự bật công tắc giữ chỗ của cả hệ kho")
def _():
	# enable_stock_reservation la cong tac chung: bat len thi don ban cung
	# giu cho theo. Doi mot cong tac co do phai la quyet dinh cua anh Viet.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tinh_hinh_giu_cho")[1]
	la("không được ghi cài đặt", "set_value(\"Stock Settings\"" in doan, False)
	la("không set_single", "db.set_single_value" in doan, False)
	dung("phải nói rõ hệ quả khi bật", "công tắc" in doan)


# --------------------------------------------------------- phía màn hình


@ca("nút mới có đúng tên và ghi chú anh Việt giao")
def _():
	m = _js("02-trang-chu.js")
	dung("tên nút", "'Lập kế hoạch sản xuất'" in m)
	dung("ghi chú nút",
		"'Tính toán nguyên vật liệu, bán thành phẩm, thành phẩm sản xuất trong ngày'" in m)
	dung("có nhánh mở màn", "if (k === 'KHSX') return go(scrKeHoachSX);" in m)
	dung("nằm trong phân hệ Sản xuất", "'MFG', 'KHSX'" in m)
	dung("có địa chỉ riêng", "'lap-ke-hoach-san-xuat': 'KHSX'" in m)


@ca("màn hình không tự tính lại con số nào của ERPNext")
def _():
	m = _js("38-ke-hoach-sx.js")
	# Bon cot deu doc thang tu may chu. Tinh o may khach thi mo hai dien
	# thoai ra co the thay hai con so khac nhau.
	for o in ("x.can", "x.ton_dau", "x.ton_nay", "x.con_lam"):
		dung("phải đọc %s từ máy chủ" % o, o in m)


@ca("nút tạo lệnh hiện cả khi phiếu còn nháp, chỉ cần còn phải làm")
def _():
	m = _js("38-ke-hoach-sx.js")
	doan = m.split("function khsxThe")[1].split("\nasync function")[0]
	dung("phải kiểm còn phải làm", "x.con_lam > 0" in doan)
	la("không còn đòi phiếu đã chốt", "khsx.d.da_chot" in doan, False)
	dung("có ô tick chọn nhiều món", "data-tick=" in doan)


@ca("màn kế hoạch KHÔNG còn nút chốt tổng")
def _():
	m = _js("38-ke-hoach-sx.js")
	la("không còn nút chốt", "khsxChot" in m, False)
	dung("có nút ra lệnh hàng loạt", "khsxLenhLo" in m)
	dung("có đường mở danh sách lệnh đã tạo", "scrMfgList" in m)


@ca("số cân đong hiển thị bằng kl(), không dùng num() để bếp khỏi đọc nhầm")
def _():
	# Ngay 29/08/2026 bep doc "242,486" thanh 242 nghin gram. So dung, cach
	# viet bay: dau phay la dau thap phan theo loi Viet Nam.
	nen = _js("00-nen.js")
	dung("có hàm kl", "function kl(v, dvt)" in nen)
	dung("nói rõ vì sao không dùng num", "doc nham" in nen)
	m = _js("38-ke-hoach-sx.js")
	doan = m.split("function khsxCot(")[1].split("\nfunction ")[0]
	la("không còn num() trong bảng số", "num(" in doan, False)
	dung("dùng kl kèm đơn vị", "kl(x.can, x.dvt)" in doan)


@ca("kho nhập thành phẩm hiện ra trên thẻ và đổi được")
def _():
	# Anh Viet 29/08/2026: "lo co nhung mon ca 2 bep deu dung thi sao".
	m = _js("38-ke-hoach-sx.js")
	dung("thẻ hiện kho nhập", "x.kho_dich" in m)
	dung("đổi được kho ngay trên thẻ", "data-doikho=" in m)
	dung("ô nhập số Cần nằm ngay trên thẻ", "data-can=" in m)
	p = _py("ke_hoach_sx.py")
	dung("máy chủ trả danh sách kho", '"cac_kho": _cac_kho_chon()' in p)
	dung("tạo lệnh nhận kho bếp chọn", "def tao_lenh(ten, khoa, loai=\"btp\", so_luong=None, kho=None)" in p)


@ca("bán thành phẩm xổ ra được danh sách nguyên liệu của nó")
def _():
	m = _js("38-ke-hoach-sx.js")
	dung("có nút xổ", "data-xo=" in m)
	dung("đọc bảng nvl con", "x.nvl" in m)


@ca("ba tab và các chip lọc đều có mặt")
def _():
	m = _js("38-ke-hoach-sx.js")
	for t in ("'tp', '🎂 Thành phẩm'", "'btp', '🥣 Bán thành phẩm'",
			"'nvl', '🌾 Nguyên liệu'"):
		dung("tab %s" % t, t in m)
	dung("chip bếp", "KHSX_BEP" in m)
	dung("chip tình trạng", "KHSX_MUC" in m)
	dung("chip Phải làm đứng đầu", "['thieu', '🔴 Phải làm']" in m)


@ca("mẫu in A4 gắn đúng Production Plan, không đẻ doctype riêng")
def _():
	m = _py("mau_in/__init__.py")
	dung("đã đăng ký mẫu", '"Vagabond - Kế hoạch sản xuất"' in m)
	dung("gắn lên Production Plan", '("ke_hoach_san_xuat.html", "Production Plan")' in m)


# ------------------- hai loi bat duoc khi chay thu tren site that 28/08


@ca("bảng nguyên liệu truyền LIST CÁC DICT, không phải list chuỗi")
def _():
	# get_warehouse_list cua ERPNext goi row.get("warehouse") tren tung phan
	# tu. Truyen chuoi thi no nem AttributeError, va vi _nap_nvl bot loi nen
	# bang nguyen lieu rong tron ma khong ai biet. Chay thu ngay 28/08 tra ve
	# 58 thanh pham, 79 ban thanh pham, 0 nguyen lieu - dung cai bay nay.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def _nap_nvl")[1].split("\n@frappe")[0]
	dung("phải bọc thành dict", '{"warehouse": k["kho"]}' in doan)
	la("không truyền chuỗi trần", 'kho = [k["kho"] for k' in doan, False)


@ca("đơn quá hạn chỉ gom trong CỬA SỔ, không quét cả tháng")
def _():
	# Do tren site 28/08: 233 phieu YCSX deu Pending, phieu cu nhat tu 28/07.
	# Gom het thi ke hoach ngay mai co 230 phieu trong khi thuc te chi con
	# vai phieu chua lam.
	m = _py("ke_hoach_sx.py")
	dung("có hằng cửa sổ", "SO_NGAY_QUA_HAN" in m)
	la("cửa sổ phải nhỏ", kh.SO_NGAY_QUA_HAN <= 7, True)
	doan = m.split("def ycsx_can_lam")[1].split("\ndef ")[0]
	dung("phải có chặn dưới", "mri.schedule_date >= %(som_nhat)s" in doan)
	dung("vẫn có chặn trên", "mri.schedule_date <= %(ngay)s" in doan)


@ca("không gom quá hạn thì chỉ lấy đúng ngày đó")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def ycsx_can_lam")[1].split("\ndef ")[0]
	dung("tắt gom thì mốc sớm nhất bằng chính ngày",
		"som_nhat = add_days(ngay, -so_ngay) if cint(gom_qua_han) else ngay" in doan)


@ca("phần tồn đọng ngoài cửa sổ được liệt kê ra, không giấu đi")
def _():
	m = _py("ke_hoach_sx.py")
	dung("có hàm liệt kê", "def ton_dong(" in m)
	doan = m.split("def ton_dong")[1].split("\n@frappe")[0]
	dung("phải nói rõ vì sao tồn đọng", "không ra lệnh sản xuất nối về phiếu" in doan)


@ca("hàm liệt kê tồn đọng CHỈ ĐỌC, không tự đóng phiếu quá khứ")
def _():
	# Quy tac cua tiem: phat hien sai sot trong du lieu cu thi liet ke cho
	# anh Viet, khong tu sua.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def ton_dong")[1].split("\n@frappe")[0]
	la("không ghi", "set_value" in doan, False)
	la("không commit", "db.commit" in doan, False)
	la("không đóng phiếu", "update_status" in doan, False)
	dung("nói rõ là không tự đóng", "tự đóng phiếu nào" in doan)


# ------------- loi thu ba: combine_items cua ERPNext hong voi nguon YCSX


@ca("KHÔNG bật gộp món khi nguồn là phiếu yêu cầu sản xuất")
def _():
	# Hai co hong, doc trong production_plan.add_items cua ERPNext:
	# mot la no nhet ten phieu yeu cau vao o Link tro sang Don ban, lam
	# phieu khong luu duoc; hai la no gan so luong da gop cho TUNG dong ma
	# khong xoa bot dong, thanh ra bep lam gap ba.
	m = _py("ke_hoach_sx.py")
	dung("phải tắt gộp món", "doc.combine_items = 0" in m)
	la("không được bật", "doc.combine_items = 1" in m, False)


@ca("vẫn gộp bán thành phẩm và nguyên liệu, vì đó mới là số bếp đi lấy hàng")
def _():
	m = _py("ke_hoach_sx.py")
	dung("gộp cấp dưới vẫn bật", "doc.combine_sub_items = 1" in m)


@ca("bảng tham chiếu đơn bán được dọn rỗng trước khi lưu")
def _():
	# Hang rao thu hai: mot dong thua trong bang do la ca phieu khong luu
	# duoc, va cau tu choi khong noi gi ve nguyen nhan.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def _dung_phieu")[1].split("\ndef ")[0]
	dung("phải dọn rỗng", 'doc.set("prod_plan_references", [])' in doan)


@ca("ghi chú giải thích đủ CẢ HAI cỗ hỏng, không chỉ cái nhìn thấy")
def _():
	# Loi thu hai am tham hon nhieu: phieu van luu duoc, chi la so gap ba.
	# Nguoi doc sau phai biet ca hai truoc khi dinh bat lai o gop mon.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def _dung_phieu")[1].split('"""')[1]
	dung("nói lỗi không lưu được", "Không tìm thấy Dòng #1" in doan)
	dung("nói lỗi số gấp ba", "Bếp làm gấp ba" in doan)


# ---------- hai cho chua dat, thay khi doc phieu that MFG-PP-2026-00001


@ca("thành phẩm gom theo mã, một mã một thẻ")
def _():
	# ERPNext de moi dong phieu yeu cau thanh mot dong rieng. Do tren phieu
	# that ngay 29/08/2026: 110 dong cho 38 ma, mot ma banh hien sau lan.
	# Bep mo ra khong biet phai lam bao nhieu.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xem(")[1].split("\n@frappe")[0]
	dung("phải gom theo mã", "gom_tp" in doan)
	dung("cộng dồn số cần", 'o["can"] += flt(x.get("planned_qty"))' in doan)


@ca("gom xong vẫn giữ danh sách phiếu yêu cầu nguồn")
def _():
	# Gom ma danh mat nguon thi luc con so trong la khong ai truy lai duoc.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xem(")[1].split("\n@frappe")[0]
	dung("phải giữ nguồn", '"nguon": []' in doan)
	dung("mỗi nguồn có tên phiếu", '"ycsx": x.get("material_request")' in doan)
	dung("mỗi nguồn có số lượng riêng", '"sl": flt(x.get("planned_qty"))' in doan)


@ca("một thẻ gom ra NHIỀU lệnh, mỗi lệnh neo về đúng phiếu yêu cầu của nó")
def _():
	# Gop thanh mot lenh to thi cac phieu yeu cau treo mai o Pending, dung
	# cai dong 233 phieu ton dong dang co tren he.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tao_lenh(")[1].split("def _goc(")[0]
	dung("phải tách khoá theo dấu phẩy", 'split(",")' in doan)
	dung("phải gọi từng dòng", "_tao_mot_lenh(ten, k, loai_n" in doan)
	dung("nói rõ vì sao không gộp", "neo về đúng phiếu yêu cầu" in doan)


@ca("xin chuyển nguyên liệu bỏ qua mã đã tắt, và liệt kê ra")
def _():
	# Ngay 29/08/2026 bam nut thi Frappe chan ca phieu voi cau "San pham
	# BTPB00046 da tat", bep khong co phieu nao. Ma da tat ma con nam trong
	# cong thuc la chuyen cua danh muc, khong phai chuyen man hinh nay tu
	# sua - nen bo qua roi liet ke.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xin_chuyen_nvl(")[1].split("\ndef _kho_nhan_nvl(")[0]
	dung("có lọc mã đã tắt", '"disabled": 1' in doan)
	dung("liệt kê mã bỏ qua", "Bỏ qua %d mã đã tắt" in doan)
	dung("không tự mở lại mã", "db_set" not in doan)


@ca("xin chuyển nguyên liệu chặn phiếu có kho nhận trùng kho gửi")
def _():
	# Ho so mon dang tro kho mac dinh ve Kho tong 307 nen ERPNext dien kho
	# nhan cung la Kho tong: phieu chuyen tu 307 sang chinh 307.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xin_chuyen_nvl(")[1].split("\ndef _kho_nhan_nvl(")[0]
	dung("có phép so hai kho", "d.warehouse == d.from_warehouse" in doan)
	dung("nói rõ cách gỡ", "Chọn bếp ở chip" in doan)


@ca("không câu thông báo nào của kế hoạch còn nêu tên riêng")
def _():
	# Anh Viet 29/08/2026: "lo Kien nghi thi sao". Moi thong bao chi neu
	# ten bo phan.
	for tep in ("ke_hoach_sx.py", "kho_san_xuat.py"):
		m = _py(tep)
		la("%s không nêu tên riêng" % tep, "anh Kiên" in m, False)
	for tep in ("38-ke-hoach-sx.js", "06-nhap-kho-kiem-ke.js"):
		m = _js(tep)
		la("%s không nêu tên riêng" % tep, "anh Kiên" in m, False)


@ca("lệnh thành phẩm KHÔNG nhập vào kho điểm bán")
def _():
	# Ngay 29/08/2026 lenh banh Greengold nhap thang vao Kho Sales Online,
	# la kho ban hang. O `warehouse` cua dong ke hoach la kho DIEM BAN dat,
	# khong phai kho bep nhap hang lam ra.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def _tao_mot_lenh(")[1].split("\n\n@frappe")[0]
	la("không seed kho điểm bán vào ô kho nhập",
		'"fg_warehouse": d.warehouse' in doan, False)
	dung("nói rõ vì sao", "kho DIEM BAN" in doan)
	dung("đặt cả ba kho theo luật", "ksx.kho_cua_lenh(chang, bep)" in doan)


@ca("bếp của thành phẩm suy từ bán thành phẩm con, không đoán theo kho")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xem(")[1].split("\n@frappe")[0]
	dung("có bảng bếp đọc một lượt", "_bep_cua_nhieu(cac_ma)" in doan)
	dung("suy ngược từ món con lên món cha", "bep_khai[cha] = bep_khai[con]" in doan)
	dung("giữ riêng kho giao cho điểm bán", 'd["kho_giao"]' in doan)


@ca("mọi dòng đều kèm ảnh món, đọc từ máy chủ")
def _():
	# Anh Viet 29/08/2026: "cai nay phai lam o backend, anh mon luon di kem
	# ten mon".
	p = _py("ke_hoach_sx.py")
	dung("máy chủ đọc ảnh một lượt", "def _anh_cua(cac_ma)" in p)
	dung("gắn ảnh vào từng dòng", '"anh": anh.get(ma, "")' in p)
	nen = _js("00-nen.js")
	dung("có khung ảnh dùng chung", "function anhMon(url)" in nen)
	for tep in ("38-ke-hoach-sx.js", "05-san-xuat.js"):
		dung("%s dùng khung ảnh" % tep, "anhMon(" in _js(tep))


@ca("huỷ phiếu kế hoạch bị chặn khi đã đẻ ra lệnh sản xuất")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def huy_phieu(")[1].split("\n@frappe")[0]
	dung("có đếm lệnh con", '"production_plan": ten' in doan)
	dung("nói rõ phải huỷ lệnh trước", "Huỷ các lệnh đó trước" in doan)
	dung("phiếu nháp thì xoá hẳn", "doc.delete()" in doan)


@ca("huỷ lệnh sản xuất bị chặn khi đã làm ra hàng")
def _():
	# Huy lenh da lam ra hang la de lai mot khoan ton khong co goc.
	m = _py("ke_hoach_sx.py")
	doan = m.split("def huy_lenh(")[1].split("\n@frappe")[0]
	dung("chặn khi đã làm ra hàng", "flt(doc.produced_qty) > 0" in doan)
	dung("chặn khi đã chuyển nguyên liệu", "material_transferred_for_manufacturing" in doan)
	dung("trả số về cho phiếu kế hoạch", "update_ordered_status()" in doan)


@ca("sửa số lệnh chỉ cho khi lệnh còn nháp")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def sua_so_lenh(")[1].split("\n\n")[0] + m.split("def sua_so_lenh(")[1]
	dung("chặn lệnh đã ghi sổ", "doc.docstatus != 0" in doan)
	dung("chỉ đường thay thế", "Huỷ lệnh rồi ra lệnh mới" in doan)


@ca("trang danh sách lệnh sản xuất KHÔNG còn thẻ chọn kho chung")
def _():
	# Anh Viet 29/08/2026: moi lenh da chon kho rieng roi, de them mot o
	# chon kho chung o trang danh sach la mau thuan.
	m = _js("05-san-xuat.js")
	doan = m.split("async function scrMfgList()")[1].split("\nasync function scrMfgNew()")[0]
	la("không gọi thẻ kho ở trang danh sách", "mfgWhCard()" in doan, False)
	dung("hai màn kia vẫn còn thẻ kho", m.count("mfgWhCard()") >= 3)


@ca("màn lệnh sản xuất có nút huỷ và nút sửa số")
def _():
	m = _js("05-san-xuat.js")
	dung("có nút huỷ lệnh", "huy_lenh" in m)
	dung("có nút sửa số", "sua_so_lenh" in m)
	dung("số lượng hiển thị làm tròn", "kl(w.qty, w.stock_uom)" in m)


@ca("có màn danh mục phiếu kế hoạch, mở và huỷ được")
def _():
	m = _js("38-ke-hoach-sx.js")
	dung("có màn danh mục", "function scrKhsxDsPhieu()" in m)
	dung("gọi được huỷ phiếu", "ke_hoach_sx.huy_phieu" in m)
	dung("có đường mở từ màn kế hoạch", "data-dsp=" in m)


@ca("ô tick là input thật, tròn, không bóp méo khi tên món dài")
def _():
	# Anh Viet review giao dien 30/08/2026: nut tick cu "nhin rat tho,
	# lech truc doc so voi hinh anh va text, dang lam vo layout".
	nen = _js("00-nen.js")
	doan = nen.split(".tik{")[1].split("\n.khsx-o")[0]
	dung("bỏ hình mặc định của trình duyệt", "appearance:none" in doan)
	dung("tròn", "border-radius:50%" in doan)
	dung("không co giãn theo chữ", "flex:0 0 24px" in doan)
	dung("khi tích thì đổi màu", ":checked" in doan)
	dung("dấu tick vẽ bằng SVG nhúng", "data:image/svg+xml" in doan)
	j = _js("38-ke-hoach-sx.js")
	dung("dùng input thật", 'type="checkbox" class="tik"' in j)
	la("không còn vẽ ô tick bằng chữ", "'☑'" in j, False)


@ca("hàng thẻ món dùng đúng lớp .li của hệ thống thiết kế")
def _():
	# Ban v351 boc them mot lop flex tay roi dat align-items:flex-start,
	# thanh ra tick va anh khong thang hang voi ten mon. .li von da
	# display:flex, align-items:center, gap:12px san roi.
	nen = _js("00-nen.js")
	doan = nen.split(".li{")[1].split("\n")[0]
	dung(".li canh giữa theo trục dọc", "align-items:center" in doan)
	j = _js("38-ke-hoach-sx.js")
	doan2 = j.split("function khsxThe(")[1].split("\nasync function")[0]
	# Bo chu thich truoc khi soi: cau van giai thich VI SAO bo
	# align-items:flex-start co quyen nhac lai chinh chuoi do.
	doan2 = re.sub(r"/\*.*?\*/", "", doan2, flags=re.S)
	la("không tự đặt lại align-items", "align-items:flex-start" in doan2, False)
	la("không ép .li thành block", 'class="li" style="display:block"' in doan2, False)
	dung("phần xổ ra nằm ngoài hàng", 'class="khsx-than"' in doan2)


@ca("tên món dài không đẩy được ảnh hay ô tick ra ngoài")
def _():
	nen = _js("00-nen.js")
	dung("khối chữ co lại được", ".li .lt{flex:1;min-width:0}" in nen)
	dung("ảnh giữ nguyên bề ngang", "flex:0 0 40px" in nen or "flex:0 0 46px" in nen)


@ca("bấm vào đâu trên hàng cũng xổ ra được, trừ các nút bên trong")
def _():
	j = _js("38-ke-hoach-sx.js")
	doan = j.split("function khsxGan(")[1].split("\n    };")[0]
	# Thu tu xet co chu y: nut ben trong phai duoc xet TRUOC ca hang.
	dung("xét ô tick trước", doan.index("data-tick") < doan.index("data-xo"))
	dung("xét nút đổi kho trước", doan.index("data-doikho") < doan.index("data-xo"))
	dung("xét nút tạo lệnh trước", doan.index("data-lenh") < doan.index("data-xo"))


@ca("nhân công thức: cần bao nhiêu nguyên liệu cho số mẻ muốn làm")
def _():
	# Cong thuc khai lam ra 10 banh ton 500g bot. Lam 25 banh thi ton 1250g.
	la("nhân đúng tỉ lệ", kh.nhan_cong_thuc(500, 10, 25), 1250.0)
	la("làm đúng một mẻ công thức", kh.nhan_cong_thuc(500, 10, 10), 500.0)


@ca("công thức khai làm ra 0 sản phẩm thì trả 0, KHÔNG chia cho 0")
def _():
	# Mot man hinh bep khong duoc phep no vi mot dong danh muc khai thieu.
	la("không nổ", kh.nhan_cong_thuc(500, 0, 25), 0.0)
	la("số âm cũng không nổ", kh.nhan_cong_thuc(500, -1, 25), 0.0)


@ca("mọi thẻ món đều xổ ra được nguyên liệu, kể cả thành phẩm")
def _():
	# Anh Viet 30/08/2026: "click vao dong banh muon tao lenh thi se xo ra
	# danh sach NVL de xem truoc roi quay lai tao lenh sau".
	m = _py("ke_hoach_sx.py")
	dung("đọc thành phần công thức một lượt", "def _thanh_phan_bom(cac_bom)" in m)
	doan = m.split("def xem(")[1].split("\n@frappe")[0]
	dung("gắn nguyên liệu cho thành phẩm", 'd["nvl"] = _thanh_phan(o["bom"], o["can"])' in doan)
	dung("bán thành phẩm không neo được thì đọc công thức",
		'd["nvl"] = _thanh_phan(x.get("bom_no")' in doan)
	j = _js("38-ke-hoach-sx.js")
	dung("thẻ nào cũng xổ ra được", "Xem nguyên liệu và ra lệnh" in j)


@ca("ô Tồn đầu KHÔNG cho sửa, chỉ Tồn giờ mới sửa")
def _():
	# Ton dau la chuyen da xay ra luc 0h. Sua no la chen but toan lui ngay
	# vao ngay da chot so, lam lech gia von cua ngay do.
	j = _js("38-ke-hoach-sx.js")
	doan = j.split("function khsxCot(")[1].split("\nfunction ")[0]
	dung("có ô gõ tồn giờ", "data-ton=" in doan)
	la("không có ô gõ tồn đầu", "data-tondau" in doan, False)
	dung("tồn đầu vẫn chỉ in ra", "kl(x.ton_dau, x.dvt)" in doan)
	dung("nói rõ vì sao không cho sửa", "lui ngay" in doan or "lùi ngày" in doan)


@ca("đặt lại tồn đi qua phiếu kiểm kê thật, không sửa lụi sổ kho")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def dat_ton(")[1].split("\ndef _gia_von(")[0]
	dung("dựng phiếu Stock Reconciliation", '"doctype": "Stock Reconciliation"' in doan)
	dung("ghi sổ luôn", "doc.submit()" in doan)
	dung("chỉ kho của bếp", "kho not in _cac_kho_chon()" in doan)
	dung("không lùi ngày", "nowdate()" in doan)
	dung("ghi lại người nhập", "frappe.session.user" in doan)
	la("không đụng thẳng bảng Bin", "db_set" in doan, False)


@ca("món chưa từng có giá vốn thì DỪNG, không bịa giá")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def dat_ton(")[1].split("\ndef _gia_von(")[0]
	dung("có kiểm giá vốn", "not gia" in doan)
	dung("chỉ đường cho người dùng", "Nhập kho món này một lần" in doan)


@ca("neo nguyên liệu về bán thành phẩm theo MÓN và CÔNG THỨC của BTP")
def _():
	# Dong NVL ghi `main_item_code` la ma THANH PHAM. Phai tim dong BTP cua
	# dung mon do, roi xem cong thuc BTP co chua ma nguyen lieu khong.
	btp = [
		{"name": "b1", "parent_item_code": "BANH01", "bom_no": "BOM-RUOT"},
		{"name": "b2", "parent_item_code": "BANH01", "bom_no": "BOM-VO"},
		{"name": "b3", "parent_item_code": "BANH02", "bom_no": "BOM-KEM"},
	]
	nvl = [
		{"item_code": "BOT", "main_item_code": "BANH01"},
		{"item_code": "DUONG", "main_item_code": "BANH01"},
		{"item_code": "SUA", "main_item_code": "BANH02"},
	]
	ma_cua_bom = {
		"BOM-RUOT": {"BOT"},
		"BOM-VO": {"DUONG"},
		"BOM-KEM": {"SUA"},
	}
	ra = kh.neo_nvl_theo_btp(nvl, btp, ma_cua_bom)
	la("bột về ruột", [x["item_code"] for x in ra.get("b1", [])], ["BOT"])
	la("đường về vỏ", [x["item_code"] for x in ra.get("b2", [])], ["DUONG"])
	la("sữa về kem", [x["item_code"] for x in ra.get("b3", [])], ["SUA"])


@ca("neo KHÔNG dùng cặp (main_item_code, from_bom) như bản v346 hỏng")
def _():
	# Do tren site 29/08/2026: 0 tren 47 dong neo duoc, vi ca hai o do deu
	# noi ve THANH PHAM, khong bao gio trung bom_no cua ban thanh pham.
	btp = [{"name": "b1", "parent_item_code": "BANH01",
		"production_item": "RUOT01", "bom_no": "BOM-RUOT01"}]
	nvl = [{"item_code": "BOT", "main_item_code": "BANH01",
		"from_bom": "BOM-BANH01"}]
	ra = kh.neo_nvl_theo_btp(nvl, btp, {"BOM-RUOT01": {"BOT"}})
	la("vẫn neo được dù from_bom là công thức thành phẩm",
		[x["item_code"] for x in ra.get("b1", [])], ["BOT"])


@ca("nguyên liệu không nằm trong công thức BTP nào thì KHÔNG neo bừa")
def _():
	btp = [{"name": "b1", "parent_item_code": "BANH01", "bom_no": "BOM-RUOT"}]
	nvl = [{"item_code": "HOP_GIAY", "main_item_code": "BANH01"}]
	ra = kh.neo_nvl_theo_btp(nvl, btp, {"BOM-RUOT": {"BOT"}})
	la("không dòng nào", len(ra), 0)


@ca("ô sub_assembly_item_reference của ERPNext vẫn được ưu tiên khi đã có")
def _():
	btp = [{"name": "b1", "parent_item_code": "BANH01", "bom_no": "BOM-RUOT"}]
	nvl = [{"item_code": "BOT", "main_item_code": "BANH01",
		"sub_assembly_item_reference": "b9"}]
	ra = kh.neo_nvl_theo_btp(nvl, btp, {"BOM-RUOT": {"BOT"}})
	la("theo ô của ERPNext", sorted(ra.keys()), ["b9"])


@ca("một nguyên liệu trong hai công thức BTP của cùng món thì neo cả hai")
def _():
	btp = [
		{"name": "b1", "parent_item_code": "BANH01", "bom_no": "BOM-RUOT"},
		{"name": "b2", "parent_item_code": "BANH01", "bom_no": "BOM-VO"},
	]
	nvl = [{"item_code": "BOT", "main_item_code": "BANH01"}]
	ra = kh.neo_nvl_theo_btp(nvl, btp, {"BOM-RUOT": {"BOT"}, "BOM-VO": {"BOT"}})
	la("xổ ra ở cả hai", sorted(ra.keys()), ["b1", "b2"])


@ca("phép neo là PHÉP THUẦN, không chạm Frappe")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def neo_nvl_theo_btp(")[1].split("\ndef ")[0]
	la("không gọi frappe", "frappe." in doan, False)


@ca("phép neo nguyên liệu CHỈ ĐỌC, không ghi gì xuống phiếu")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def xem(")[1].split("\n@frappe")[0]
	la("không db_set", "db_set" in doan, False)
	la("không commit", "db.commit" in doan, False)


@ca("thẻ thành phẩm xổ ra được danh sách phiếu yêu cầu nguồn")
def _():
	m = _js("38-ke-hoach-sx.js")
	dung("có nhánh xổ nguồn", "x.nguon || []" in m)
	dung("hiện tên phiếu", "n.ycsx" in m)
	dung("nói rõ gom mấy phiếu", "x.so_nguon > 1" in m)

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


@ca("chưa chốt phiếu thì không cho tạo lệnh, và nói rõ phải làm gì")
def _():
	m = _py("ke_hoach_sx.py")
	doan = m.split("def tao_lenh")[1].split("\n@frappe")[0]
	dung("phải chặn phiếu nháp", "doc.docstatus != 1" in doan)
	dung("phải chỉ cách làm", "Bấm Chốt kế hoạch trước" in doan)


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


@ca("nút tạo lệnh chỉ hiện khi phiếu đã chốt và còn phải làm")
def _():
	m = _js("38-ke-hoach-sx.js")
	doan = m.split("function khsxThe")[1].split("\nasync function")[0]
	dung("phải kiểm đã chốt", "khsx.d.da_chot" in doan)
	dung("phải kiểm còn phải làm", "x.con_lam > 0" in doan)


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

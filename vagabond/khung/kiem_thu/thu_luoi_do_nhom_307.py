"""Ca kiểm THUẦN cho lưới đỡ theo nhóm món và báo cáo cổng bật cờ (#307).

Giữ bốn điều anh Việt chốt 14/09/2026 chiều: chọn tài khoản theo nhóm gốc,
nhóm KHÔNG leo cha khi tìm tài khoản, giữ giá trị khai tay trên nhóm, báo
cáo rỗng và không rỗng. Không cần site.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import luoi_do_nhom as ldn
from vagabond.vagabond.report.mon_theo_ton_chua_co_tai_khoan import (
	mon_theo_ton_chua_co_tai_khoan as bc,
)

# Cây nhóm giả, tên KHÔNG lấy làm bằng chứng về site thật.
CHA = {
	"All Item Groups": "",
	"Mua vào": "All Item Groups", "Nguyên vật liệu Thô": "Mua vào", "Bao bì": "Mua vào",
	"Bột": "Nguyên vật liệu Thô",
	"Bán ra": "All Item Groups", "Bánh lẻ": "Bán ra",
	"Sản xuất": "All Item Groups",
	"Bán thành phẩm Bánh": "Sản xuất", "Ruột bánh": "Bán thành phẩm Bánh",
	"Thành phẩm Bánh": "Sản xuất", "Bánh nguyên": "Thành phẩm Bánh",
	"Dịch vụ": "All Item Groups", "Ship": "Dịch vụ",
}
TK = {"152": "152 - Nguyên liệu, vật liệu - TV", "1551": "1551 - Thành phẩm - TV"}
BTP1 = "1552 - BTP - TV"


@ca("#307 lưới đỡ: đường lên gốc, gốc nghiệp vụ và nhánh ngay dưới gốc")
def _goc():
	la("đường lên", ldn.duong_len_goc("Bột", CHA), ["Bột", "Nguyên vật liệu Thô", "Mua vào", "All Item Groups"])
	la("gốc Mua vào", ldn.nhom_goc_va_nhanh("Bột", CHA), ("mua vào", "Nguyên vật liệu Thô"))
	la("con trực tiếp: nhánh là chính nó", ldn.nhom_goc_va_nhanh("Bao bì", CHA), ("mua vào", "Bao bì"))
	la("nhánh BTP", ldn.nhom_goc_va_nhanh("Ruột bánh", CHA), ("sản xuất", "Bán thành phẩm Bánh"))
	la("ngoài ba gốc", ldn.nhom_goc_va_nhanh("Ship", CHA), (None, None))
	la("chính nhóm gốc", ldn.nhom_goc_va_nhanh("Sản xuất", CHA), ("sản xuất", None))
	vong = {"A": "B", "B": "A"}
	la("dữ liệu vòng không treo", ldn.duong_len_goc("A", vong), ["A", "B"])


@ca("#307 lưới đỡ: tài khoản theo gốc, nhánh BTP lấy ô cấp 1, không đoán khi thiếu")
def _tk():
	la("Mua vào 152", ldn.tai_khoan_du_kien("Bột", CHA, TK, BTP1)[0], TK["152"])
	la("Bán ra 1551", ldn.tai_khoan_du_kien("Bánh lẻ", CHA, TK, BTP1)[0], TK["1551"])
	la("Sản xuất thành phẩm 1551", ldn.tai_khoan_du_kien("Bánh nguyên", CHA, TK, BTP1)[0], TK["1551"])
	la("Sản xuất BTP cấp 1", ldn.tai_khoan_du_kien("Ruột bánh", CHA, TK, BTP1)[0], BTP1)
	tk, ly = ldn.tai_khoan_du_kien("Ruột bánh", CHA, TK, "")
	la("ô cấp 1 trống thì không gán", tk, None)
	dung("nói tên ô", "tk_ton_btp_cap1" in ly)
	tk, ly = ldn.tai_khoan_du_kien("Bột", CHA, {"1551": "x"}, BTP1)
	la("site không có 152 duy nhất thì không gán", tk, None)
	dung("nói số hiệu", "152" in ly)
	la("ngoài ba gốc", ldn.tai_khoan_du_kien("Ship", CHA, TK, BTP1)[0], None)
	la("gốc Sản xuất không gán cho chính gốc", ldn.tai_khoan_du_kien("Sản xuất", CHA, TK, BTP1)[0], None)
	la("không phân biệt hoa thường", ldn.nhom_goc_va_nhanh("X", {"X": "  MUA   VÀO "})[0], "mua vào")


@ca("#307 lưới đỡ: số hiệu chỉ nhận khi có đúng một tài khoản chi tiết còn dùng")
def _duy_nhat():
	cac = [dict(name="152 - NVL - TV", account_number="152", is_group=0, disabled=0),
		dict(name="1551 - TP - TV", account_number="1551", is_group=0, disabled=0),
		dict(name="1551 - TP cũ - TV", account_number="1551", is_group=0, disabled=1),
		dict(name="1552 - BTP - TV", account_number="1552", is_group=1, disabled=0),
		dict(name="15521 - a", account_number="15521", is_group=0, disabled=0),
		dict(name="15521 - b", account_number="15521", is_group=0, disabled=0)]
	d = ldn.tai_khoan_duy_nhat(cac)
	la("152", d.get("152"), "152 - NVL - TV")
	la("1551 bỏ tài khoản tắt", d.get("1551"), "1551 - TP - TV")
	la("nhóm không tính", d.get("1552"), None)
	la("hai tài khoản cùng số thì không chọn", d.get("15521"), None)


@ca("#307 lưới đỡ: giữ khai tay, idempotent, bỏ qua nhóm không có món theo tồn")
def _bang():
	co_ton = {"Bột": 12, "Bao bì": 0, "Bánh lẻ": 3, "Ruột bánh": 5, "Bánh nguyên": 7, "Ship": 1}
	hien_co = {"Bánh lẻ": "1561 - Hàng hoá - TV", "Bánh nguyên": TK["1551"]}
	bang = ldn.bang_du_kien(co_ton, CHA, hien_co, TK, BTP1)
	theo_nhom = {r["nhom"]: r for r in bang}
	dung("nhóm 0 món bị bỏ", "Bao bì" not in theo_nhom)
	la("Bột gán 152", (theo_nhom["Bột"]["hanh_dong"], theo_nhom["Bột"]["tai_khoan"]), (ldn.GAN, TK["152"]))
	la("khai tay giữ", theo_nhom["Bánh lẻ"]["hanh_dong"], ldn.GIU)
	la("khai tay không bị đè", theo_nhom["Bánh lẻ"]["tai_khoan"], "1561 - Hàng hoá - TV")
	la("đã đúng thì bỏ qua", theo_nhom["Bánh nguyên"]["hanh_dong"], ldn.BO_QUA)
	la("BTP gán cấp 1", theo_nhom["Ruột bánh"]["tai_khoan"], BTP1)
	la("ngoài gốc bỏ qua", theo_nhom["Ship"]["hanh_dong"], ldn.BO_QUA)
	# Chạy lần hai với kết quả lần một đã ghi: không còn dòng GAN nào.
	sau = dict(hien_co, **{r["nhom"]: r["tai_khoan"] for r in bang if r["hanh_dong"] == ldn.GAN})
	lan2 = ldn.bang_du_kien(co_ton, CHA, sau, TK, BTP1)
	la("idempotent", [r["nhom"] for r in lan2 if r["hanh_dong"] == ldn.GAN], [])
	md = ldn.bang_markdown(bang)
	dung("markdown có tiêu đề và dòng", md.startswith("| Nhóm lá") and "| Bột | 12 |" in md)


@ca("#307 lưới đỡ: nhóm cha có tài khoản KHÔNG đỡ được nhóm con (lõi không leo cha)")
def _khong_leo_cha():
	# Chỉ nhóm cha "Nguyên vật liệu Thô" có tài khoản; món ở nhóm lá "Bột" vẫn
	# bị báo thiếu, đúng get_item_group_defaults của lõi de591661.
	mon = [dict(name="NVLT-1", item_name="Bột mì", item_group="Bột", brand=None, stock_uom="Gram")]
	ra = bc.loc_chua_co(mon, set(), {"Nguyên vật liệu Thô"}, set(), {"NVLT-1": 5000})
	la("vẫn thiếu", [r["item_code"] for r in ra], ["NVLT-1"])
	la("kèm tồn", ra[0]["ton"], 5000.0)
	ra = bc.loc_chua_co(mon, set(), {"Bột"}, set(), {})
	la("đúng nhóm lá thì đủ", ra, [])
	# Lưới đỡ cũng gán cho nhóm lá, không gán cho nhóm trung gian không có món.
	bang = ldn.bang_du_kien({"Bột": 1}, CHA, {"Nguyên vật liệu Thô": TK["152"]}, TK, BTP1)
	la("gán cho lá dù cha đã có", (bang[0]["nhom"], bang[0]["hanh_dong"]), ("Bột", ldn.GAN))


@ca("#307 báo cáo cổng: rỗng khi ba nấc đủ, không rỗng khi thiếu, sắp theo nhóm")
def _bao_cao():
	mon = [
		dict(name="BTPB-1", item_name="Ruột", item_group="Ruột bánh", brand=None, stock_uom="Gram"),
		dict(name="NVLT-2", item_name="Đường", item_group="Bột", brand="Biên Hoà", stock_uom="Gram"),
		dict(name="BAWC-1", item_name="Bánh", item_group="Bánh lẻ", brand=None, stock_uom="Cái"),
	]
	ra = bc.loc_chua_co(mon, {"BTPB-1"}, {"Bánh lẻ"}, {"Biên Hoà"}, {})
	la("đủ ba nấc thì rỗng", ra, [])
	ra = bc.loc_chua_co(mon, {"BTPB-1"}, set(), {"Biên Hoà"}, {"BAWC-1": 2})
	la("thiếu một món", [r["item_code"] for r in ra], ["BAWC-1"])
	ra = bc.loc_chua_co(mon, set(), set(), set(), {"NVLT-2": 100})
	la("sắp theo nhóm rồi mã", [r["item_code"] for r in ra], ["BAWC-1", "NVLT-2", "BTPB-1"])
	la("món chưa có Bin thì tồn 0", [r["ton"] for r in ra if r["item_code"] == "BAWC-1"], [0.0])
	dung("cột có tồn và nhóm", {c["fieldname"] for c in bc.COT} >= {"item_code", "item_group", "ton", "brand"})


@ca("#307 lưới đỡ: patch có trong patches.txt và trước dòng dong_bo_cau_truc v493")
def _patch():
	import io
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	with io.open(os.path.join(goc, "patches.txt"), encoding="utf-8") as f:
		s = f.read()
	dung("có dòng patch", "vagabond.patches.luoi_do_nhom_307" in s)
	dung("đứng trước dong_bo_cau_truc #v493",
		s.index("vagabond.patches.luoi_do_nhom_307") < s.index("dong_bo_cau_truc #v493"))
	with io.open(os.path.join(goc, "truong_tu_them.py"), encoding="utf-8") as f:
		t = f.read()
	dung("ô gương được dựng sau kho_san_xuat",
		t.index("kho_san_xuat.TRUONG_MOI") < t.index("tai_khoan_btp.dung()"))


@ca("#307 phân biệt 152, 153 và nhóm không quản tồn theo bảng đã duyệt")
def _nhom_mua_da_duyet():
	for nhom, so in (("Nguyên vật liệu Thô", "152"), ("Bao bì", "152"),
		("Công cụ Dụng cụ", "153"), ("Văn phòng phẩm", "153"),
		("Tài sản Cố định", None), ("Dịch vụ", None), ("Demo", None)):
		cha = {nhom: "Mua vào"}
		la(nhom, ldn.tai_khoan_du_kien(nhom, cha, {"152": "TK152", "153": "TK153"}, None)[0],
			"TK" + so if so else None)
	la("Nhân bán thành phẩm dùng cấu hình BTP", ldn.tai_khoan_du_kien("Nhân bán thành phẩm",
		{"Nhân bán thành phẩm": "Sản xuất"}, TK, BTP1)[0], BTP1)


@ca('#307 món tài sản dịch vụ: có SLE giữ nguyên, chưa có SLE mới bỏ tồn')
def _giu_lich_su_sle():
	from unittest.mock import patch
	with patch.object(ldn, 'mon_khong_quan_ton', return_value=[
		{'name': 'MOI', 'co_sle': False}, {'name': 'CU', 'co_sle': True}]), \
		patch.object(ldn.frappe.db, 'set_value') as ghi, \
		patch.object(ldn.frappe, 'clear_cache', create=True):
		ldn.bo_theo_ton_chua_phat_sinh()
		la('chỉ món mới được đổi', ghi.call_args_list[0].args, ('Item', 'MOI', 'is_stock_item', 0))
		la('món có lịch sử không bị sửa', ghi.call_count, 1)


@ca('#307 nhóm: đổi cấu hình cũ chỉ cập nhật giá trị máy, giữ khai tay')
def _doi_tai_khoan_nhom():
	la('nhóm theo máy đổi', ldn.quyet_nhom('CU', 'MOI', '', 'CU')['hanh_dong'], ldn.GAN)
	la('nhóm khai tay giữ', ldn.quyet_nhom('TAY', 'MOI', '', 'CU')['hanh_dong'], ldn.GIU)


@ca('#307 patch không ghi hoàn tất khi nạp nhóm còn lỗi')
def _patch_loi():
	from unittest.mock import patch
	from vagabond.patches import luoi_do_nhom_307 as p
	def bao(cau):
		raise ValueError(cau)
	with patch.object(ldn, 'bo_theo_ton_chua_phat_sinh', return_value=[]), \
		patch.object(ldn, 'ap_dung', return_value={'dem': {'loi': 1}, 'bang': []}), \
		patch.object(p.frappe, 'throw', side_effect=bao):
		loi = ''
		try:
			p.execute()
		except ValueError as e:
			loi = str(e)
		dung('dừng migrate có câu hướng dẫn', 'migrate' in loi)

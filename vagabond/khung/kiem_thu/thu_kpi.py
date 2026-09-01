# -*- coding: utf-8 -*-
"""Kiem thu: phan he KPI va hoa hong.

Anh Viet chot bay dieu ngay 01/09/2026 va bao lam ban demo ngay. Bo ca kiem
nay chot lai TUNG DIEU trong bay dieu do, de lan sau ai sua mot con so thi
biet minh dang sua cai gi.

HAI CHO TRONG DIEU 3 CON VUONG, DA BAO ANH VIET, VA MAY VAN TINH DUNG NHU
ANH VIET

Chuyen thu nhat: san 150 trieu nhung moc dau tien 350 trieu. Ban 200 trieu la
tren san ma chua toi moc, ra 0 dong. Neu dung y vay thi san THAT la 350
trieu, con so 150 trieu khong co tac dung gi.

Chuyen thu hai: moc 3 viet la "2% tren TOAN BO phan doanh thu vuot 400
trieu", khac kieu voi hai moc duoi. No tao mot bac nhay ngay tai 600 trieu.
Ban 599 trieu duoc 3.235.000, ban 601 trieu duoc 4.020.000.

May tinh DUNG NHU ANH VIET viet, vi do la quyet dinh cua anh. Nhung bang cau
hinh tu do va hien canh bao o moi diem nhay. Bo ca kiem duoi day chot ca hai
chuyen: cong thuc ra dung so, VA phep do bac nhay chi dung cho.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import kpi

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))
CF = kpi.CAU_HINH_MAC_DINH


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def _hh(trieu):
	return kpi.hoa_hong_tho(trieu * 1000000, CF["bac"], CF["san"])


# ------------------------------------------------- dieu 3: bac hoa hong

@ca("KPI: hoa hồng tính đúng như anh Việt chốt điều 3")
def _bac():
	# Duoi san thi khong dong nao.
	la("100 triệu", _hh(100), 0)
	la("dưới sàn 149 triệu", _hh(149), 0)
	# Tren san nhung chua toi moc dau: van 0. Day chinh la khoang trong da
	# bao anh Viet - giu nguyen vi anh chua doi y.
	la("200 triệu, trên sàn mà chưa tới mốc", _hh(200), 0)
	la("349 triệu", _hh(349), 0)
	la("đúng mốc 1 là 350 triệu", _hh(350), 0)
	# Moc 1: 1% tren phan nam trong bac 350-450.
	la("400 triệu", _hh(400), 500000)
	la("450 triệu", _hh(450), 1000000)
	# Moc 2: cong don 1,5% tren phan 450-600.
	la("500 triệu", _hh(500), 1750000)
	la("599 triệu", _hh(599), 3235000)
	la("600 triệu", _hh(600), 3250000)
	# Moc 3: 2% tren TOAN BO phan vuot 400 trieu, thay cho hai bac duoi.
	la("601 triệu", _hh(601), 4020000)
	la("700 triệu", _hh(700), 6000000)
	la("1 tỷ", _hh(1000), 12000000)


@ca("KPI: máy tự dò ra bậc nhảy và khoảng trống trong bảng bậc")
def _do_bac_nhay():
	nhay = kpi.diem_nhay_bac(CF["bac"], CF["san"])
	la("đúng một chỗ nhảy", len(nhay), 1)
	la("nhảy tại mốc 601 triệu", nhay[0]["tai"], 601000000.0)
	la("nhảy 770 nghìn", nhay[0]["nhay"], 770000.0)

	loi = kpi.kiem_bac(CF["bac"], CF["san"])
	dung("có báo khoảng trống giữa sàn và mốc đầu",
	     any("sàn thật sự" in x for x in loi))
	dung("có báo chỗ nhảy vọt", any("nhảy vọt" in x for x in loi))

	# Bang bac tron thi khong bao gi ca. Neu bao ca khi bang sach thi canh
	# bao thanh tieng on, va tieng on thi khong ai doc.
	tron = [
		{"tu": 300000000, "den": 500000000, "ty_le": 1.0, "kieu": "phan_vuot"},
		{"tu": 500000000, "den": None, "ty_le": 1.5, "kieu": "phan_vuot"},
	]
	la("bảng trơn thì không cảnh báo gì", kpi.kiem_bac(tron, 300000000), [])
	la("bảng trơn thì không có chỗ nhảy", kpi.diem_nhay_bac(tron, 300000000), [])


@ca("KPI: trần áp SAU khi nhân hệ số xếp loại, không phải trước")
def _tran():
	# Ap tran truoc roi moi nhan he so thi nguoi xuat sac van vuot tran,
	# tuc la tran khong con la tran nua.
	tien, tho = kpi.hoa_hong(1000000000, CF["bac"], CF["san"], 1.25, CF["tran"])
	la("thô của 1 tỷ nhân hệ số 1,25", tho, 15000000)
	la("chạm đúng trần 15 triệu", tien, 15000000)

	tien2, tho2 = kpi.hoa_hong(2000000000, CF["bac"], CF["san"], 1.25, CF["tran"])
	la("2 tỷ thì thô vượt xa trần", tho2, 40000000)
	la("nhưng trả ra vẫn đúng trần", tien2, 15000000)

	tien3, tho3 = kpi.hoa_hong(500000000, CF["bac"], CF["san"], 1.0, CF["tran"])
	la("dưới trần thì trả nguyên", tien3, tho3)
	la("và bằng đúng số thô", tien3, 1750000)

	# Chua dat thi he so 0, khong co hoa hong du doanh thu cao. Day la san
	# chat luong o muc 4 ban thiet ke: khong co san nay thi ban bang moi gia.
	tien4, _t = kpi.hoa_hong(1000000000, CF["bac"], CF["san"], 0.0, CF["tran"])
	la("chưa đạt thì không hoa hồng dù doanh thu 1 tỷ", tien4, 0)


@ca("KPI: trần 15 triệu và sàn 150 triệu đúng con số anh Việt chốt")
def _con_so():
	la("trần một người một kỳ", CF["tran"], 15000000)
	la("sàn", CF["san"], 150000000)
	la("chu kỳ là tháng", CF["chu_ky"], "thang")
	la("ba mốc", len(CF["bac"]), 3)
	la("mốc 1 bắt đầu 350 triệu", CF["bac"][0]["tu"], 350000000)
	la("mốc 2 bắt đầu 450 triệu", CF["bac"][1]["tu"], 450000000)
	la("mốc 3 bắt đầu 600 triệu", CF["bac"][2]["tu"], 600000000)
	la("mốc 3 tính từ 400 triệu", CF["bac"][2].get("moc"), 400000000)
	# Dieu 4: hop dong B2B va voucher doi tac boc rieng.
	la("bóc riêng hợp đồng B2B", CF["loai_tru_hop_dong"], 1)
	dung("có danh sách nguồn loại trừ", len(CF["loai_tru_nguon"]) > 0)


# --------------------------------------------------- dieu 5: trong so

@ca("KPI: trọng số từng bộ cộng lại đúng 100")
def _trong_so():
	for k, bo in CF["bo"].items():
		la("tổng trọng số bộ %s" % k, kpi.tong_trong_so(bo), 100)


@ca("KPI: trọng số đúng bản anh Việt điều chỉnh ở điều 5")
def _dieu_5():
	def ts(bo, k):
		for t in CF["bo"][bo]["tieu_chi"]:
			if t["k"] == k:
				return t["trong_so"]
		return None

	# Bep: banh entremet yeu cau do hoan thien khat khe, nguyen lieu cao cap
	# khong duoc phi.
	la("bếp: hao hụt nguyên liệu", ts("bep", "hao_hut"), 30)
	la("bếp: hàng hỏng và lỗi ngoại quan", ts("bep", "hang_loi"), 20)
	# Sales: tap trung chat luong cham soc khach chu khong bao so luong don.
	la("sales: khách thành viên quay lại", ts("sales", "khach_lai"), 20)
	la("sales: số đơn hoàn thành", ts("sales", "so_don"), 5)
	# Hai bo co hoa hong, ba bo con lai khong. Bep va ke toan an theo diem
	# chu khong an theo doanh thu.
	co = sorted(k for k, v in CF["bo"].items() if v.get("co_hoa_hong"))
	la("chỉ sales và cửa hàng có hoa hồng", co, ["cua_hang", "sales"])


# ------------------------------------------------------------ điểm số

@ca("KPI: điểm một tiêu chí, cả chiều thuận lẫn chiều nghịch")
def _diem():
	la("đạt đúng mục tiêu", kpi.diem_mot_tieu_chi(100, 100), 100.0)
	la("đạt một nửa", kpi.diem_mot_tieu_chi(50, 100), 50.0)
	# Chan tren 120: khong chan thi mot thang may man keo ca nam, va nguoi
	# ta co dong co don don vao mot ky.
	la("vượt xa vẫn chặn ở 120", kpi.diem_mot_tieu_chi(500, 100), 120.0)
	# Chieu nghich: cang thap cang tot.
	la("nghịch, đạt đúng mục tiêu", kpi.diem_mot_tieu_chi(3, 3, True), 100.0)
	la("nghịch, tốt hơn mục tiêu", kpi.diem_mot_tieu_chi(1.5, 3, True), 120.0)
	la("nghịch, tệ gấp đôi", kpi.diem_mot_tieu_chi(6, 3, True), 50.0)
	la("nghịch, bằng 0 là hoàn hảo", kpi.diem_mot_tieu_chi(0, 3, True), 120.0)
	# Chua khai muc tieu thi tra 0 chu KHONG doan bua 100. Doan 100 la cho
	# khong mot tieu chi chua ai dat chuan.
	la("chưa khai mục tiêu", kpi.diem_mot_tieu_chi(999, 0), 0.0)


@ca("KPI: điểm tổng cộng theo trọng số, và xếp loại")
def _tong():
	dong = [
		{"diem": 100, "trong_so": 50},
		{"diem": 60, "trong_so": 50},
	]
	la("hai tiêu chí bằng trọng số", kpi.diem_tong(dong), 80.0)
	la("bảng rỗng", kpi.diem_tong([]), 0.0)
	# Tong trong so lo khai khac 100 thi van chia dung ty le that, khong tra
	# ra mot con so vo nghia.
	la("trọng số lỡ khai 40+40", kpi.diem_tong([
		{"diem": 100, "trong_so": 40}, {"diem": 50, "trong_so": 40}]), 75.0)

	la("xuất sắc", kpi.xep_loai(100), ("Xuất sắc", 1.25))
	la("tốt", kpi.xep_loai(85), ("Tốt", 1.10))
	la("đạt", kpi.xep_loai(70), ("Đạt", 1.00))
	la("chưa đạt", kpi.xep_loai(69.9), ("Chưa đạt", 0.0))


# ----------------------------------------------- dieu 6: ai duyet buoc 2

@ca("KPI: ai bấm được bước quản lý, đúng điều 6 anh Việt chốt")
def _duyet_2():
	gd = {"Giám đốc"}
	ql = {"Quản lý cửa hàng"}

	duoc, _v = kpi.duyet_buoc_quan_ly(ql, True, True, 0)
	dung("quản lý trực tiếp bấm được", duoc)
	duoc, vs = kpi.duyet_buoc_quan_ly(ql, False, True, 0)
	dung("quản lý của người KHÁC thì không", not duoc)
	dung("và nói rõ vì sao", "quản lý trực tiếp" in vs)
	# Giam doc cham cap quan ly, nen luon bam duoc.
	duoc, _v = kpi.duyet_buoc_quan_ly(gd, False, True, 0)
	dung("giám đốc luôn bấm được", duoc)

	# Fallback: quan ly nghi thi quyen tu MO LEN cho giam doc.
	dung("quản lý nghỉ thì tới lượt giám đốc", kpi.qua_han_quan_ly(0, False))
	dung("giữ phiếu quá hạn cũng vậy", kpi.qua_han_quan_ly(kpi.NGAY_CHO_QUAN_LY + 1, True))
	dung("còn trong hạn thì chưa", not kpi.qua_han_quan_ly(1, True))
	# Mo THEM chu khong CUOP: quan ly di lam lai van bam duoc.
	duoc, _v = kpi.duyet_buoc_quan_ly(ql, True, True, kpi.NGAY_CHO_QUAN_LY + 5)
	dung("quản lý về vẫn bấm được dù đã quá hạn", duoc)


# ------------------------------------------------------- cấu hình gộp

@ca("KPI: cấu hình lưu đè lên bản gốc theo từng khoá, không thay cả cụm")
def _gop():
	g = kpi.gop_cau_hinh({"tran": 20000000})
	la("khoá đã sửa thì lấy bản sửa", g["tran"], 20000000)
	la("khoá chưa sửa thì lấy bản gốc", g["san"], 150000000)
	dung("bộ tiêu chí vẫn còn đủ", len(g["bo"]) == len(CF["bo"]))
	# Them mot tieu chi moi vao ban goc thi site da luu cau hinh cu VAN nhan
	# duoc tieu chi do, khong phai khai lai tu dau.
	g2 = kpi.gop_cau_hinh({"bo": {"sales": {"ten": "Sales đổi tên"}}})
	la("tên bộ lấy bản sửa", g2["bo"]["sales"]["ten"], "Sales đổi tên")
	dung("tiêu chí của bộ đó vẫn còn", len(g2["bo"]["sales"]["tieu_chi"]) > 0)
	dung("các bộ khác không bị đụng", "bep" in g2["bo"])
	la("chuỗi hỏng thì rơi về bản gốc", kpi.gop_cau_hinh("{khong phai json")["tran"], 15000000)


# -------------------------------------------- ba nguyen tac goc va cua ngo

@ca("KPI: ba nguyên tắc gốc phải nằm trong mã nguồn, không chỉ trong tài liệu")
def _nguyen_tac():
	m = _doc("vagabond", "kpi.py")
	# Nguyen tac 1: may do duoc thi nguoi KHONG sua duoc.
	i = m.find("def cham(")
	than = m[i:m.find("\ndef _gan_don(", i)]
	dung("máy đo được thì người không sửa", 'if dong.nguon != TAY:' in than)
	# Nguyen tac 2: giam doc bam la dong bang.
	j = m.find("def duyet(")
	tj = m[j:m.find("\n@frappe.whitelist()", j)]
	dung("giám đốc duyệt là đóng băng", "doc.dong_bang = 1" in tj)
	dung("phiếu đã đóng băng thì không chấm lại", 'frappe.throw("Phiếu đã chốt, không chấm lại được.")' in m)
	dung("phiếu đã đóng băng thì không trả lại", "đã chốt và đóng băng, không trả lại được" in m)
	# Nguyen tac 3: gan tay ghi vao PHIEU, khong sua hoa don.
	dung("gán tay lưu vào phiếu", "doc.don_gan_tay = json.dumps(" in m)
	dung("không sửa hoá đơn khi gán tay",
	     'set_value("Sales Invoice"' not in m and "Sales Invoice\", ma" not in m)


@ca("KPI: một đơn chỉ được gán cho một người trong cùng kỳ")
def _gan_trung():
	m = _doc("vagabond", "kpi.py")
	i = m.find("def _gan_don(")
	than = m[i:m.find("\n@frappe.whitelist()", i)]
	dung("có dò đơn đã gán cho người khác", "_don_da_gan(doc.ky, tru_phieu=doc.name)" in than)
	dung("và chặn lại", "Một đơn chỉ được tính " in than)


@ca("KPI: không ai tự duyệt phiếu của chính mình")
def _tu_duyet():
	m = _doc("vagabond", "kpi.py")
	dung("có hàng rào tự duyệt", "Không ai tự duyệt phiếu KPI của chính mình." in m)


@ca("KPI: đẩy chi đi qua đúng cổng Đề nghị chi, không tự dựng phiếu")
def _day_chi():
	m = _doc("vagabond", "kpi.py")
	i = m.find("def day_chi(")
	than = m[i:m.find("\n# ---", i)]
	dung("gọi cổng de_nghi_chi.tao", "de_nghi_chi.tao(" in than)
	dung("chỉ phiếu đã duyệt mới đẩy", "Chỉ phiếu đã giám đốc duyệt" in than)
	dung("không đẩy hai lần", "đã đẩy sang" in than)
	# Dieu 7: tien hoa hong tach khoi luong cung, nen phieu chi rieng.
	dung("phiếu chi riêng mang tên kỳ và người", '"Hoa hồng hiệu suất kỳ %s cho %s"' in than)


@ca("KPI: màn hình không tự tính điểm hay tính hoa hồng")
def _man_khong_tinh():
	js = _doc("vagabond", "public", "js", "bep", "44-kpi.js")
	for x in ("scrKPI", "scrKPICt", "scrKPICau", "scrKPIToi"):
		dung("có màn " + x, "function " + x + "(" in js)
	# Man KHONG duoc tu nhan ty le hay tu cong trong so. Tinh o hai noi thi
	# som muon hai noi ra hai con so, ma con so nay di thang vao luong.
	dung("không tự nhân tỷ lệ hoa hồng", "ty_le / 100" not in js)
	dung("không tự cộng trọng số", "trong_so *" not in js)
	dung("người được chấm nói lại được", "vagabond.kpi.y_kien" in js)
	dung("ô thử tính có tô đỏ chỗ nhảy", "doNhay" in js)

	# Anh Viet chot 01/09/2026: san, tran va ba moc phai doi duoc theo tung
	# thoi diem. Khoi sua chi hien cho giam doc, va phai goi cua ngo luu chu
	# khong tu ghi cau hinh o dau khac.
	dung("có khối sửa số", "if (kq.sua_duoc) {" in js)
	dung("khối sửa gọi đúng cửa ngõ lưu", "vagabond.kpi.luu_cai_dat" in js)
	dung("ô để trống trả null chứ không trả 0", "if (v === '') return null;" in js)
	dung("mốc cuối để trống nghĩa là trở lên",
	     "bac[i].tu === null || bac[i].ty_le === null" in js)


@ca("KPI: nút trên trang chủ chỉ mở cho quản lý, kế toán, giám đốc")
def _nut():
	js = _doc("vagabond", "public", "js", "bep", "02-trang-chu.js")
	kh = _doc("vagabond", "public", "js", "bep", "01-khung-app.js")
	dung("có hàm chặn vai", "function coQuyenHRM(" in kh)
	dung("khối Nhân sự dựng có điều kiện", "if (coQuyenHRM()) {" in js)
	# O "KPI cua toi" phai nam NGOAI dieu kien do: ai cung xem duoc diem cua
	# chinh minh.
	i = js.find("if (coQuyenHRM()) {")
	j = js.find("html += '<div class=\"sec\">KPI của tôi</div>")
	dung("ô KPI của tôi nằm ngoài điều kiện vai", j > i and js.find("}", i) < j)
	for k in ("'KPI'", "'KPICD'", "'KPITOI'"):
		dung("vgbGo có nhánh " + k, "if (k === " + k + ")" in js)
	dung("bảng đường dẫn có kpi", "'kpi': 'KPI'," in js)


@ca("KPI: cửa ngõ mở đúng danh sách, hàm nội bộ phải kín")
def _cua_ngo():
	m = _doc("vagabond", "kpi.py")
	# tinh_lai sua diem va tien tren phieu. Mo ra ngoai la cho goi mot phep
	# tinh lai tu trinh duyet, ke ca tren phieu da dong bang.
	i = m.find("def tinh_lai(")
	dung("tinh_lai KHÔNG mở ra ngoài",
	     "@frappe.whitelist()" not in m[max(0, i - 120):i])
	j = m.find("def so_lieu_tu_dong(")
	dung("so_lieu_tu_dong KHÔNG mở ra ngoài",
	     "@frappe.whitelist()" not in m[max(0, j - 120):j])

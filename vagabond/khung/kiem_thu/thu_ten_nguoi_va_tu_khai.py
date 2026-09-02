# -*- coding: utf-8 -*-
"""Kiem thu bon viec anh Viet chot ngay 02/09/2026.

Anh Viet mo man Duyet don hang tang tren dien thoai va gui hai anh chup:

  1. O "Nguoi duyet" ghi `thevagabond.marketing@gmai...` bi cat cut. Anh
     chot: *"Tat ca cac cho hien ten nguoi thao tac phai la hien ten chu
     khong hien email (trong ca app, erp desktop, email gui di,...) phai
     sua o backend de lam mac dinh ve sau."*
  2. Khoi chi tiet bi ep thanh mot cot hep, chu xuong dong tung chu mot.
     Anh chot: *"sua loi hien thi, no dang bi ep dong"*.
  3. *"cho anh them 1 dong mapping tu dong so hoa don da xuat cho don nay
     de anh tra cuu cho nhanh"*.
  4. *"Ten nguoi ban tren tat ca cac man hoa don va tren mau in"*, cong
     them *"ten nguoi huy, sua, nguoi cap OTP"* de quy trach nhiem.
  5. Nut *"Tao phieu duyet KPI va commission"* trong nut KPI cua toi, cho
     nhung ky may chua co so lieu.

BA CHO DE HONG LAI MA CA KIEM NAY CHOT LAI

Thu nhat, phep doi ma tai khoan thanh ten nguoi truoc day co BON ban chep
qua chep lai o bon tep. Hai ban trong cung mot tep `ho_so_tt.py`, va ban
thu hai CHE MAT ban thu nhat suot tu 13/08: Python lay dinh nghia sau cung,
nen ban tot (co tra cuu ho so nhan su) chua bao gio duoc chay. Ca kiem chot
chi con MOT ban that.

Thu hai, `show_title_field_in_link` la thu bien "hien ten" thanh mac dinh
that cho ca ERPNext ban may tinh. Thieu dong do thi moi o Link tro toi User
lai hien dia chi thu, va lan sau ai them o moi cung sai tiep.

Thu ba, phieu tu khai la nguoi TU KHAI TIEN CUA CHINH MINH. Ba hang rao
(chi khai cho minh, ky phai da het thang, bat buoc co bang ke) phai con
nguyen. Bo mot cai la mo duong cho mot con so khong ai doi chieu duoc.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import kpi
from vagabond import ten_nguoi as tn

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


# ------------------------------------------------- 1. doi ten thay cho thu

@ca("Tên người: tài khoản máy đọc ra chữ người hiểu được")
def _may():
	la("quản trị", tn.ten("Administrator"), "Hệ thống")
	la("khách vãng lai", tn.ten("Guest"), "Khách vãng lai")
	la("rỗng vẫn là rỗng", tn.ten(""), "")
	la("None cũng là rỗng", tn.ten(None), "")


@ca("Tên người: không có họ tên thì lấy khúc trước dấu @, không lấy cả địa chỉ")
def _tho():
	# Day la cho anh Viet khoanh do: ca dia chi thu tran o roi bi cat cut.
	# Nua dia chi con doc duoc, ca dia chi thi khong.
	la("bỏ phần sau @", tn._tho("thevagabond.marketing@gmail.com"),
	   "thevagabond.marketing")
	la("không có @ thì giữ nguyên", tn._tho("uyen"), "uyen")
	la("rỗng", tn._tho(""), "")
	dung("không bao giờ trả về cả địa chỉ thư",
	     "@" not in tn._tho("ai.do@gmail.com"))


@ca("Tên người: CHỈ CÒN MỘT bản đổi tên trong cả mã nguồn")
def _mot_ban():
	"""Ban thu hai trong ho_so_tt.py che mat ban thu nhat suot tu 13/08."""
	hs = _doc("vagabond", "ho_so_tt.py")
	la("hồ sơ thanh toán chỉ còn một bản", hs.count("def _ten_nguoi("), 1)
	dung("và bản đó gọi về lớp chung", "ten_nguoi.ten(email)" in hs)

	kp = _doc("vagabond", "kpi.py")
	la("KPI chỉ còn một bản", kp.count("def _ten_nguoi("), 1)
	dung("và cũng gọi về lớp chung", "_tn.ten(u)" in kp)

	tep = _doc("vagabond", "ten_nguoi.py")
	dung("lớp chung có phép đổi một cái", "def ten(ma):" in tep)
	dung("lớp chung có phép đổi cả danh sách", "def nhieu(ds):" in tep)
	dung("lớp chung có phép bơm thêm ô tên", "def gan(d, *o):" in tep)


@ca("Tên người: bơm ô tên mà KHÔNG xoá ô mã")
def _gan_khong_xoa():
	"""Ma tai khoan la KHOA de so quyen, de loc, de tra nguoc. Ghi de la mat."""
	tep = _doc("vagabond", "ten_nguoi.py")
	dung("ô mới là <ô>_ten", 'r[k + "_ten"]' in tep)
	dung("cố ý không ghi đè ô cũ", "CỐ Ý không ghi đè" in tep)


@ca("Tên người: bật hiện tên cho mọi ô Link trỏ tới User trên bản máy tính")
def _desk():
	"""Day moi la phan 'mac dinh ve sau'. Thieu no thi o moi them sau nay
	lai hien dia chi thu, va khong ai nho de sua tay tung cho."""
	tep = _doc("vagabond", "ten_nguoi.py")
	# Neo vao THAN ham `dung()` chu khong vao ca tep: chuoi nay cung nam
	# trong loi giai thich o dau tep, neo vao ca tep thi xoa mat dong goi
	# that ca kiem van xanh.
	i = tep.find("def dung():")
	dung("có hàm dựng", i > 0)
	than = tep[i:]
	dung("có bật cờ hiện tiêu đề", '"show_title_field_in_link", 1, "Check"' in than)
	dung("và khai luôn ô tiêu đề là họ tên",
	     '"title_field", "full_name", "Data"' in than)
	dung("đặt trên chính doctype chứ không trên một ô", "for_doctype=True" in than)
	tt = _doc("vagabond", "truong_tu_them.py")
	dung("được gọi mỗi lần migrate", "ten_nguoi.dung()" in tt)


# ------------------------------- 2 va 3. man duyet don tang

@ca("Đơn tặng: khối chi tiết nằm ngoài hàng bấm nên không bị ép dòng")
def _ep_dong():
	"""Truoc 02/09 khoi chi tiet nam trong cot chu cua hang, tuc la bi ep
	giua bieu tuong ben trai va cot tien ben phai. Tren dien thoai cot do
	con chung ba muoi ky tu nen chu xuong dong tung chu mot."""
	js = _doc("vagabond", "public", "js", "bep", "41-duyet-don-tang.js")
	# Neo vao THU TU: khoi chi tiet phai xuat hien SAU khi hang bam da
	# dong lai, chu khong nam trong cot chu cua hang.
	dung("khối chi tiết nằm ngoài hàng bấm",
	     "Khoi chi tiet nam NGOAI hang bam" in js)
	i_dong = js.find("h(r.creation || '') + '</div></div></div>'")
	i_than = js.find("(mo ? dtgThan(r, kq) : '')")
	dung("và thật sự đứng sau hàng bấm", i_dong > 0 and i_than > i_dong)
	dung("nhãn không co lại", "flex:0 0 auto;min-width:112px" in js)
	dung("giá trị được cả phần còn lại và xuống dòng theo từ",
	     "flex:1;min-width:0;word-break:break-word" in js)


@ca("Đơn tặng: có dòng số hoá đơn điện tử đã xuất")
def _so_hoa_don():
	py = _doc("vagabond", "hang_tang.py")
	dung("danh sách đọc số hoá đơn", '"custom_hddt_so", "custom_hddt_trang_thai",' in py)
	dung("chi tiết cũng đọc", '"custom_hddt_sobaomat"' in py)
	js = _doc("vagabond", "public", "js", "bep", "41-duyet-don-tang.js")
	dung("màn có dòng số hoá đơn", "'Số hoá đơn đã xuất'" in js)
	# Chua xuat thi phai NOI THANG la chua xuat. De o trong thi nguoi doc
	# tu doan, ma doan sai o cho nay la doi chieu nham to hoa don.
	dung("chưa xuất thì nói thẳng", "'Chưa xuất hoá đơn điện tử'" in js)


@ca("Đơn tặng: hiện tên người lập và người duyệt, không hiện địa chỉ thư")
def _tang_ten():
	py = _doc("vagabond", "hang_tang.py")
	dung("danh sách đổi tên một lượt",
	     'ten_nguoi.gan(dong, "owner", "vgb_tang_nguoi_duyet")' in py)
	dung("chi tiết cũng đổi",
	     'ten_nguoi.gan(d, "owner", "vgb_tang_nguoi_duyet")' in py)
	js = _doc("vagabond", "public", "js", "bep", "41-duyet-don-tang.js")
	dung("màn ưu tiên ô tên", "ct.owner_ten || ct.owner" in js)
	dung("người duyệt cũng vậy",
	     "ct.vgb_tang_nguoi_duyet_ten || r.vgb_tang_nguoi_duyet" in js)


# ------------------------------- 4. quy trach nhiem tren hoa don

@ca("Hoá đơn: một cửa duy nhất trả về ai đã bán, sửa, huỷ, cấp mã điểm")
def _ai_lam_gi():
	py = _doc("vagabond", "ban_hang.py")
	dung("có cửa ai_lam_gi", "def ai_lam_gi(name=None):" in py)
	dung("trả tên người bán", '"nguoi_ban": _tn.ten(si.owner)' in py)
	dung("người cấp mã dùng điểm đọc từ sổ điểm",
	     '"loai": "Dung diem tru vao don"' in py)
	# Chi DOC, khong sua gi tren hoa don: goi luc nao cung an toan.
	i = py.find("def ai_lam_gi(")
	j = py.find("\n@frappe.whitelist()", i + 10)
	than = py[i:j if j > 0 else len(py)]
	dung("không ghi gì lên hoá đơn", "set_value" not in than)
	dung("không lưu gì", ".save(" not in than)

	js = _doc("vagabond", "public", "js", "bep", "10-bill-quay.js")
	dung("có khối dùng chung", "async function hdAiLamGi(name)" in js)
	dung("hỏng thì trả rỗng chứ không chặn màn", "catch (e) { return ''; }" in js)
	ds = _doc("vagabond", "public", "js", "bep", "08-doanh-so-sales.js")
	dung("màn Chi tiết đơn có dùng", "await hdAiLamGi(d.name)" in ds)
	dung("màn Hoá đơn quầy cũng dùng", "await hdAiLamGi(d.name)" in js)


@ca("Hoá đơn: người bán hiện trên danh sách và trên bản in")
def _nguoi_ban():
	kt = _doc("vagabond", "ke_toan.py")
	dung("danh sách đọc thêm người lập", '\t\t\t"owner",\n' in kt)
	dung("và đổi thành tên một lượt", '_tn.gan(ra, "owner", "vgb_huy_boi")' in kt)
	js = _doc("vagabond", "public", "js", "bep", "16-mua-hang.js")
	dung("dòng danh sách hiện người bán", "Người bán: <b>" in js)
	dung("và ưu tiên ô tên chứ không phải ô mã", "d.owner_ten || d.owner" in js)

	bq = _doc("vagabond", "public", "js", "bep", "10-bill-quay.js")
	dung("bản in có dòng người bán", "'<div class=\"d\"><span>Người bán: '" in bq)
	# Tai quay nguoi ban va thu ngan thuong la mot nguoi. In hai dong cung
	# mot cai ten tren to hoa don giay la thua.
	dung("chỉ in khi khác thu ngân", "d.nguoi_ban !== d.thu_ngan" in bq)
	py = _doc("vagabond", "ban_hang.py")
	dung("máy chủ trả người bán cho bản in", '"nguoi_ban": _tn.ten(si.owner or "")' in py)


# ------------------------------- 5. phieu tu khai commission

@ca("Tự khai: chặn kỳ chưa tới và kỳ chưa hết tháng")
def _ky_tu_khai():
	"""Khai hoa hong cho thang chua het la khai mot con so chua ai doi
	chieu duoc."""
	ky, loi = kpi.kiem_ky_tu_khai(8, 2026, 2026, 9)
	la("kỳ tháng trước nhận được", ky, "2026-08")
	la("và không có lời từ chối", loi, "")

	ky, loi = kpi.kiem_ky_tu_khai(9, 2026, 2026, 9)
	la("kỳ đang chạy bị chặn", ky, "")
	dung("nói rõ lý do", "chưa hết tháng" in loi)

	ky, loi = kpi.kiem_ky_tu_khai(11, 2026, 2026, 9)
	la("kỳ chưa tới bị chặn", ky, "")

	ky, loi = kpi.kiem_ky_tu_khai(5, 2022, 2026, 9)
	la("kỳ quá cũ bị chặn", ky, "")

	ky, loi = kpi.kiem_ky_tu_khai(13, 2026, 2026, 9)
	la("tháng 13 bị chặn", ky, "")
	ky, loi = kpi.kiem_ky_tu_khai(0, 2026, 2026, 9)
	la("tháng 0 bị chặn", ky, "")
	ky, loi = kpi.kiem_ky_tu_khai("tám", 2026, 2026, 9)
	la("gõ chữ vào ô số bị chặn", ky, "")

	# Thang 12 nam truoc, mo dau nam moi. Bien de tinh sai nhat.
	ky, loi = kpi.kiem_ky_tu_khai(12, 2025, 2026, 1)
	la("tháng 12 năm trước nhận được", ky, "2025-12")


@ca("Tự khai: chặn số tiền vô lý")
def _tien_tu_khai():
	v, loi = kpi.kiem_tien_tu_khai(4500000)
	la("số bình thường nhận được", v, 4500000.0)
	la("không có lời từ chối", loi, "")

	v, loi = kpi.kiem_tien_tu_khai(0)
	dung("số 0 bị chặn", bool(loi))
	v, loi = kpi.kiem_tien_tu_khai(-1000)
	dung("số âm bị chặn", bool(loi))
	v, loi = kpi.kiem_tien_tu_khai("bốn triệu")
	dung("chữ bị chặn", bool(loi))

	v, loi = kpi.kiem_tien_tu_khai(500000000)
	dung("số quá lớn bị chặn", bool(loi))
	# Dau phay ngan cach nghin la thu nguoi ta hay dan tu Excel sang.
	v, loi = kpi.kiem_tien_tu_khai("4,500,000")
	la("dán từ Excel vẫn đọc được", v, 4500000.0)


@ca("Tự khai: ba hàng rào của phiếu người tự khai tiền của chính mình")
def _hang_rao():
	py = _doc("vagabond", "kpi.py")
	i = py.find("def tu_khai(")
	dung("có cửa tự khai", i > 0)
	j = py.find("\ndef _hai_dau_ky(", i)
	than = py[i:j if j > 0 else len(py)]

	# 1. Chi khai cho CHINH MINH.
	dung("chỉ khai cho chính mình", "toi = frappe.session.user" in than)
	dung("không nhận tham số người khác", "nguoi=" not in than.split("\n")[0])

	# 2. Ky nao may da dung phieu thi KHONG khai de len.
	dung("không khai đè phiếu máy dựng",
	     'if cu and not cint(cu.get("tu_khai")):' in than)
	dung("phiếu đã chốt thì không sửa", 'cint(cu.get("dong_bang"))' in than)

	# 3. Bang ke la BAT BUOC, chan o CA may chu chu khong chi o man hinh.
	dung("bắt buộc có bảng kê", "Phải đính kèm bảng kê chi tiết" in than)
	dung("và gắn tệp vào phiếu sau khi lưu", "tep_dinh_kem.gan_vao(" in than)

	# Vao thang buoc ke toan, va van khong duoc tu duyet phieu cua minh.
	dung("vào thẳng bước kế toán", "doc.trang_thai = TT_KE_TOAN" in than)
	dung("đánh dấu là phiếu tự khai", "doc.tu_khai = 1" in than)

	kh = _doc("vagabond", "kpi.py")
	i2 = kh.find("def duoc_bam(")
	j2 = kh.find("\n@frappe.whitelist()", i2)
	dung("không ai tự duyệt phiếu của chính mình",
	     "Không ai tự duyệt phiếu KPI của chính mình." in kh[i2:j2])


@ca("Tự khai: kho phiếu có đủ ba ô mới và màn có nút")
def _kho_va_man():
	import json

	p = os.path.join(GOI, "vagabond", "vagabond", "doctype",
	                 "vagabond_kpi_phieu", "vagabond_kpi_phieu.json")
	d = json.load(io.open(p, encoding="utf-8"))
	ten_o = [f["fieldname"] for f in d["fields"]]
	for o in ("tu_khai", "ly_do_tu_khai", "tep_dinh_kem"):
		dung("kho có ô %s" % o, o in ten_o)
	dung("thứ tự ô cũng khai đủ",
	     all(o in (d.get("field_order") or []) for o in
	         ("tu_khai", "ly_do_tu_khai", "tep_dinh_kem")))

	js = _doc("vagabond", "public", "js", "bep", "44-kpi.js")
	dung("có nút tạo phiếu", "Tạo phiếu duyệt KPI và commission" in js)
	# Nut phai co o CA HAI nhanh: ky chua co phieu moi la ky can nhat.
	la("nút dựng ở cả hai nhánh", js.count("kpiKhoiTuKhai()"), 3)
	dung("có màn tự khai", "async function scrKPITuKhai()" in js)
	dung("màn chặn thiếu bảng kê trước khi gọi máy chủ",
	     "if (!tep.length) {" in js)
	dung("mở form là bỏ tệp của lần trước", "tdkXoaHet();" in js)
	dung("kế toán nhìn ra ngay đây là số tự khai", "if (d.tu_khai) {" in js)


@ca("Tự khai: cửa ngõ khai đúng danh sách")
def _cua_ngo_tu_khai():
	cn = _doc("vagabond", "khung", "kiem_thu", "thu_cua_ngo.py")
	dung("tu_khai nằm trong danh sách cửa ngõ KPI", '"tu_khai",' in cn)
	py = _doc("vagabond", "kpi.py")
	i = py.find("def tu_khai(")
	dung("và thật sự có whitelist", "@frappe.whitelist()" in py[max(0, i - 120):i])

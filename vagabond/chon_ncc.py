# -*- coding: utf-8 -*-
"""Phep THUAN cho o chon nha cung cap va cau tra loi "vi sao thieu hoa don".

Issue #196, 05/09/2026. Chi Dung va anh Viet keu man Lap ho so thanh toan
roi: nam nut chon luong, va danh sach nha cung cap bay het ra thanh mot bang
chip dai.

Y chi Dung: *"Neu chon ncc ma co hoa don nao thi list ra. Neu list ra ma
thieu co nghia la chua hach toan"*.

Cau do KHONG dung voi cach he dang chay, va day la ly do co tep nay.
`ho_so_tt.hoa_don_cho_tra()` loc `docstatus=1`, `outstanding > 0`, con loc
theo ngay (man hinh truyen 365) va con loai tiep nhung to dang nam trong ho
so khac. Nen mot to khong hien ra co the vi bon ly do khac nhau, chi mot
trong so do la "chua ghi so". Neu bay man hinh moi nguoi go tay lai mot
khoan ma he DA co to hoa don nhap, thi den buoc giam doc duyet may sinh
them mot hoa don mua nua - thanh hoa don trung tren so.

Vi vay: liet ke dung ly do, va to con nhap thi dan sang xem de ghi so chu
KHONG moi go lai. Anh Viet chot huong nay 05/09/2026.

Tep nay khong dung thu vien cua khung Frappe: moi quyet dinh o day kiem thu
duoc ma khong can site.
"""

# ------------------------------------------------------------------ lý do

LD_NHAP = "nhap"
LD_HUY = "huy"
LD_DA_TRA = "da_tra"
LD_HO_SO_KHAC = "ho_so_khac"
LD_NGOAI_KY = "ngoai_ky"

# Thứ tự xét, và cũng là thứ tự bày ra màn hình. Xếp theo mức độ người đọc
# cần làm gì tiếp: tờ còn nháp là việc của kế toán, tờ đang nằm trong hồ sơ
# khác là việc đi tìm hồ sơ đó, hai cái còn lại chỉ để giải thích.
THU_TU_LY_DO = (LD_NHAP, LD_HO_SO_KHAC, LD_NGOAI_KY, LD_DA_TRA, LD_HUY)


def vi_sao_thieu(hd, moc_ngay, ho_so_giu=None):
	"""Vì sao một hoá đơn mua KHÔNG hiện ra ở bảng tick.

	`hd` là dict một hoá đơn: `name`, `docstatus`, `outstanding`,
	`posting_date` (chuỗi ngày ISO).
	`moc_ngay` là chuỗi ngày ISO, tờ có `posting_date` nhỏ hơn mốc này thì
	nằm ngoài khoảng đang lọc.
	`ho_so_giu` là dict tên hoá đơn tới mã hồ sơ đang giữ nó.

	Trả về mã lý do, hoặc None nếu tờ đó ĐANG chọn được. Trả None mới là
	câu trả lời quan trọng nhất: nó nói rằng tờ này lẽ ra phải thấy, thiếu
	là do chỗ khác chứ không phải do luật lọc.
	"""
	ds = int(hd.get("docstatus") or 0)
	if ds == 0:
		return LD_NHAP
	if ds == 2:
		return LD_HUY
	if float(hd.get("outstanding") or 0) <= 0:
		return LD_DA_TRA
	if (ho_so_giu or {}).get(hd.get("name")):
		return LD_HO_SO_KHAC
	ng = str(hd.get("posting_date") or "")
	if moc_ngay and ng and ng < str(moc_ngay):
		return LD_NGOAI_KY
	return None


def gom_ly_do(ds_hd, moc_ngay, ho_so_giu=None):
	"""Gom cả bảng hoá đơn của một nhà cung cấp thành từng nhóm lý do.

	Trả về (nhom, chon_duoc) với `nhom` là dict mã lý do tới danh sách tờ,
	và `chon_duoc` là các tờ đang hiện ra bình thường.
	"""
	nhom, chon_duoc = {}, []
	for hd in ds_hd or []:
		ld = vi_sao_thieu(hd, moc_ngay, ho_so_giu)
		if ld is None:
			chon_duoc.append(hd)
		else:
			nhom.setdefault(ld, []).append(hd)
	return nhom, chon_duoc


# ------------------------------------------------------------------ chip

def chip_ncc(o):
	"""Các chip gắn cạnh tên một nhà cung cấp trong ô chọn.

	`o` là dict đã gom sẵn: `lap_duoc_so`, `lap_duoc_tien`, `qua_han_tien`,
	`no_ghi_so`, `so_hd_no`, `nhap_so`.

	Trả về danh sách dict `{ma, so, tien, kieu}`. Chữ nghĩa để bên màn hình
	lo, ở đây chỉ quyết định CHIP NÀO hiện và mang con số nào - đó mới là
	phần dễ sai và đáng kiểm thử.

	Hai luật cứng:
	- Tiền của hoá đơn còn nháp KHÔNG bao giờ cộng vào nợ đã ghi sổ. Chip
	  nháp đứng riêng, mang nhãn riêng.
	- Nợ đã ghi sổ mà lớn hơn phần lập được thì phải nói ra phần chênh, kẻo
	  người dùng thấy chip nợ rồi mở ra bảng trống.
	"""
	ra = []
	lap_so = int(o.get("lap_duoc_so") or 0)
	lap_tien = float(o.get("lap_duoc_tien") or 0)
	qua_han = float(o.get("qua_han_tien") or 0)
	no = float(o.get("no_ghi_so") or 0)
	nhap_so = int(o.get("nhap_so") or 0)
	if lap_so:
		ra.append({"ma": "lap_duoc", "so": lap_so, "tien": lap_tien, "kieu": "chinh"})
	if qua_han > 0:
		ra.append({"ma": "qua_han", "so": 0, "tien": qua_han, "kieu": "canh"})
	chenh = no - lap_tien
	if chenh > 0.5:
		ra.append({"ma": "khong_lap_duoc", "so": 0, "tien": chenh, "kieu": "phu"})
	if nhap_so:
		ra.append({"ma": "nhap", "so": nhap_so, "tien": float(o.get("nhap_tien") or 0),
			"kieu": "nhap"})
	return ra


def xep_ncc(ds):
	"""Thứ tự bày nhà cung cấp trong ô chọn.

	Bốn nhóm, theo đúng thứ tự người lập cần: nhà đang có tờ lập được (quá
	hạn lên trên), nhà còn nợ mà chưa lập được tờ nào, nhà chỉ có hoá đơn
	nháp, và cuối cùng là nhà không có gì trong cả ba tập đó.

	Nhóm cuối có mặt vì ô chọn nạp cả danh mục nhà cung cấp: Codex nêu trên
	PR #198 rằng nhà chỉ còn hoá đơn đã trả hay đã huỷ thì trước đó không
	tìm ra, nên cũng không mở được màn "Vì sao thiếu" để đọc chính hai lý
	do đó.

	Cùng nhóm thì xếp theo tên để lần nào mở ra cũng đứng đúng chỗ cũ.
	"""
	def nhom(o):
		if int(o.get("lap_duoc_so") or 0):
			return 0
		if float(o.get("no_ghi_so") or 0) > 0:
			return 1
		if int(o.get("nhap_so") or 0):
			return 2
		return 3

	def khoa(o):
		return (
			nhom(o),
			-float(o.get("qua_han_tien") or 0),
			-float(o.get("lap_duoc_tien") or 0),
			str(o.get("ten") or o.get("ncc") or "").lower(),
		)
	return sorted(ds or [], key=khoa)


def loc_ncc(ds, tu_khoa):
	"""Lọc theo từ khoá, khớp cả mã lẫn tên, không phân biệt hoa thường."""
	q = str(tu_khoa or "").strip().lower()
	if not q:
		return list(ds or [])
	return [o for o in (ds or [])
		if q in (str(o.get("ten") or "") + " " + str(o.get("ncc") or "")).lower()]

# ---------------------------------------------------------------------------
# GIOI HAN SO DONG CHO O CHON TAI KHOAN SO CAI
# ---------------------------------------------------------------------------
#
# Tach ra thanh phep THUAN de co the GOI THAT trong ca kiem, chu khong chi do
# chuoi trong ma nguon. Codex neu tren PR #207: ca kiem do chuoi khong chung
# minh duoc gia tri dau vao chay ra sao.
#
# Lich su cua cho nay:
#   Ban dau: `int(gioi_han or 40)`. Truyen 0 van ra 40, nen KHONG BAO GIO lay
#   het danh muc duoc. Goi dung, nhan ve 40 dong, tuong la ca danh muc.
#   Ban va lan mot: tach 0 ra rieng, nhung so AM lai lang le thanh "lay het",
#   con chu khong phai so thi nem ValueError tho ra man hinh.
#
# Nay khai ro tung truong hop, va dau vao xau thi NEM LOI CO CHU chu khong
# doan bua: doan bua o cho gioi han la kieu hong im lang nhat.

HAN_TK_MAC_DINH = 40


class GioiHanXau(ValueError):
	"""Số dòng tối đa không đọc được. Người gọi đổi thành lời nhắn cho người dùng."""


def gioi_han_tk(gioi_han):
	"""Số dòng tối đa cho danh mục tài khoản. THUẦN.

	  không truyền, None, chuỗi rỗng hay toàn khoảng trắng  ->  40 như cũ
	  0 hoặc "0"                                            ->  0, tức LẤY HẾT
	  số dương                                              ->  chính nó
	  số âm, chữ không phải số                              ->  ném GioiHanXau

	Số âm KHÔNG được coi là lấy hết. Trước đây nó lặng lẽ thành lấy hết, mà
	một con số âm gửi lên thì gần như chắc chắn là chỗ gọi đang tính sai chứ
	không phải người ta muốn cả danh mục.
	"""
	if gioi_han is None:
		return HAN_TK_MAC_DINH
	t = str(gioi_han).strip()
	if t == "":
		return HAN_TK_MAC_DINH
	try:
		han = int(t)
	except (TypeError, ValueError):
		# So thuc tron ("3.0") van nhan: JSON khong phan biet so nguyen voi
		# so thuc, nen chan cho nay la chan nham chinh nguoi goi that tha.
		try:
			so = float(t)
		except (TypeError, ValueError):
			raise GioiHanXau(t)
		if so != int(so):
			raise GioiHanXau(t)
		han = int(so)
	if han < 0:
		raise GioiHanXau(t)
	return han

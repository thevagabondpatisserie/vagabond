"""Kiem thu: moi hinh thu nho tep dinh kem deu phai go duoc (v293).

Anh Viet 24/08/2026: *"Them nut Xoa file (Dau X): Triet de tren TAT CA cac
man hinh co chuc nang dinh kem file (Hoan ung, Thanh toan, Hoan tien...),
moi thumbnail cua file dinh kem bat buoc phai co mot nut 'X' o goc. Khi user
click vao, he thong se go bo file do khoi phieu (ho tro cho truong hop dinh
kem nham)."*

Truoc do moi man tu ve lay mot kieu, va ba man khong go duoc gi ca. Da gom
vao mot ham dung chung `oTep` trong 00-nen.js va dung no o moi man.

Ca kiem duoi day chot HAI dieu:
  1. Ham dung chung con do, va no van sinh ra nut X khi duoc yeu cau.
  2. Man nao ve tep dinh kem thi phai di qua ham do, khong tu ve lay mot
     kieu nua. Day la cho de tuot nhat: man moi copy mot khoi HTML tu man
     cu la lai mat nut X ma khong ai thay.

Ba cua go ben may chu cung duoc chot ten o day: mat mot cua la nut X tren
man bam vao khong lam gi ca.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")

# Man nao ve tep dinh kem thi phai goi oTep.
MAN_CO_DINH_KEM = (
	"19-ho-so-tt.js",       # Hoan ung, Chi tu TK cong ty, xem ho so
	"11-khach-ca-hop-dong.js",  # Phieu hoan tien: uy nhiem chi
	"29-don-huy.js",        # Don huy: anh bang chung
	"30-tra-truoc.js",      # Tra truoc: chung tu
)


def _doc(ten, thu_muc=BEP):
	p = os.path.join(thu_muc, ten)
	if not os.path.exists(p):
		return ""
	return io.open(p, encoding="utf-8").read()


@ca("có hàm ô tệp dùng chung, và nó sinh được nút X")
def _():
	nen = _doc("00-nen.js")
	dung("có hàm oTep", "function oTep(" in nen)
	# Nut X chi ve khi co truyen `go`: phieu da chot thi chi xem, khong go.
	dung("nút X gắn với tham số go", 'o.go ? \'<span class="xo" \'' in nen)
	dung("có lớp CSS cho nút X", ".otp .xo{" in nen)


@ca("mọi màn có đính kèm đều vẽ qua ô dùng chung")
def _():
	thieu = [t for t in MAN_CO_DINH_KEM if "oTep(" not in _doc(t)]
	la("không màn nào tự vẽ ô đính kèm riêng", thieu, [])


@ca("ba cửa gỡ tệp bên máy chủ đều còn")
def _():
	# Nut X tren man bam vao ma may chu khong co cua thi khong go duoc gi.
	hs = _doc("ho_so_tt.py", GOI)
	ht = _doc("hoan_tien.py", GOI)
	la("đủ ba cửa gỡ",
	   ["def go_tep(" in hs, "def go_tep_hoa_don(" in hs, "def go_unc(" in ht],
	   [True, True, True])


@ca("cửa gỡ nào cũng chỉ bỏ liên kết, không xoá tệp")
def _():
	# QT-20: khong xoa vat ly chung tu nao. Ca ba cua phai dat con tro ve
	# None chu khong duoc goi delete.
	hs = _doc("ho_so_tt.py", GOI)
	ht = _doc("hoan_tien.py", GOI)
	for ten, than in (("ho_so_tt", hs), ("hoan_tien", ht)):
		for ham in ("go_tep(", "go_tep_hoa_don(", "go_unc("):
			if ("def " + ham) not in than:
				continue
			khuc = than.split("def " + ham)[1].split("\n@frappe.whitelist()")[0]
			dung("%s.%s không xoá tệp" % (ten, ham.rstrip("(")),
				 "delete_doc" not in khuc and ".delete()" not in khuc)
			dung("%s.%s chỉ bỏ liên kết" % (ten, ham.rstrip("(")),
				 '"attached_to_doctype": None' in khuc)


@ca("cửa gỡ uỷ nhiệm chi chặn phiếu đã kết thúc")
def _():
	# Phieu da ghi so thi to UNC la chung tu cua but toan da nam trong so.
	khuc = _doc("hoan_tien.py", GOI).split("def go_unc(")[1].split("\n@frappe.whitelist()")[0]
	dung("có chặn trạng thái Hoan thanh", '"Hoan thanh"' in khuc)


@ca("cửa gỡ bản thể hiện chặn hồ sơ đã qua bước duyệt chi")
def _():
	khuc = _doc("ho_so_tt.py", GOI).split("def go_tep_hoa_don(")[1].split("\n@frappe.whitelist()")[0]
	dung("có kiểm trạng thái hồ sơ", "TT_GO_DUOC_TEP" in khuc)
	# Danh sach trang thai go duoc KHONG duoc chua "da thanh toan".
	hs = _doc("ho_so_tt.py", GOI)
	dong = [d for d in hs.split("\n") if d.startswith("TT_GO_DUOC_TEP")]
	la("chỉ một chỗ khai danh sách trạng thái gỡ được", len(dong), 1)
	dung("không cho gỡ khi đã thanh toán", "TT_DA_TRA" not in dong[0])


@ca("màn Chi từ TK công ty đính kèm theo TỪNG DÒNG, không còn ô tổng")
def _():
	# Anh Viet 24/08/2026: *"Khong dung mot o dinh kem tong o cuoi phieu
	# nua. Di chuyen chuc nang dinh kem vao TUNG DONG HANG."*
	js = _doc("19-ho-so-tt.js")
	dung("hai màn dùng chung một bảng", "function huVeBang(" in js)
	dung("bảng đó có cột chứng từ", "huOTep(x, i)" in js)
	# Ba dau vet cua o dinh kem tong cu: bien huTep, nut huGanTep, chip
	# danh muc go cung HU_CHUNG_TU.
	for dau_vet in ("huGanTep", "data-hutx", "var HU_CHUNG_TU = ["):
		dung("không còn dấu vết ô đính kèm tổng: %s" % dau_vet, dau_vet not in js)


@ca("gõ chữ trên dòng không vẽ lại màn")
def _():
	# Ve lai la o mat tieu diem, ban phim dien thoai tut xuong, con tro nhay
	# ve dau o. Uyen gap dung canh do o man duyet mua hang ngay 21/08/2026.
	js = _doc("19-ho-so-tt.js")
	khuc = js.split("b.addEventListener('input'")[1].split("b.addEventListener('click'")[0]
	dung("nhánh gõ chữ không gọi go()", "go(" not in khuc)
	dung("nhưng có cập nhật tổng tiền", "huCapNhatTong()" in khuc)

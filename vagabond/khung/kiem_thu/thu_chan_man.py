# -*- coding: utf-8 -*-
"""Nút ở CHÂN MÀN phải bấm được, và đơn huỷ phải tự về hệ.

Sự cố 31/08/2026, anh Việt bắt được
------------------------------------
Đơn 92583 của chị Minh Ngọc huỷ bên Pancake ngày 26/08, khách đã chuyển
1.340.000 đ. Đơn không bao giờ về app để làm hoàn tiền. Anh Việt hỏi "em
thêm nút đồng bộ thủ công cho màn này được không".

Nút ĐÃ CÓ. Nó chỉ chưa bao giờ bấm được.

`frame()` dựng ba khối anh em: thanh tiêu đề `.vh`, thân màn `#vgbBody`, và
chân màn `.vf`. Hàm trả về THÂN MÀN. Màn Đơn đã huỷ đặt lắng nghe uỷ quyền
lên đúng cái thân đó, nên bấm vào nút ở chân màn thì sự kiện không bao giờ
tới tay nó. Không lỗi, không nhấp nháy, bấm như bấm vào tường.

Cộng thêm: mô đun đó cũng không có nhịp tự động nào. Hai cái hỏng chồng lên
nhau nên lần đồng bộ cuối cùng là 21/08/2026, mười ngày liền không một đơn
huỷ nào về hệ trong khi tiền khách nằm ở mình.

Bộ ca này chốt cả hai đầu, và chốt cho MỌI màn chứ không riêng màn đó.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

BEP = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"public", "js", "bep",
)


def _doc(ten):
	return io.open(os.path.join(BEP, ten), encoding="utf-8").read()


def _cac_phan():
	return sorted(f for f in os.listdir(BEP) if re.match(r"^\d\d-.+\.js$", f))


def _cat_bieu_thuc(mn, i, dung_o):
	"""Cắt một biểu thức JavaScript từ vị trí i. THUẦN.

	Cắt bằng số ký tự cố định thì đoạn cắt tràn sang HTML của phần khác và
	bắt nhầm mọi thuộc tính `data-` trong màn. Nên phải bám dấu nháy và độ
	sâu ngoặc, dừng ở đúng ký tự kết thúc câu lệnh khi độ sâu bằng không.
	"""
	sau, nhay, thoat = 0, "", False
	j = i
	while j < len(mn):
		c = mn[j]
		if nhay:
			if thoat:
				thoat = False
			elif c == "\\":
				thoat = True
			elif c == nhay:
				nhay = ""
		elif c in "'\"`":
			nhay = c
		elif c in "([{":
			sau += 1
		elif c in ")]}":
			if sau == 0 and c in dung_o:
				break
			sau -= 1
		elif sau == 0 and c in dung_o:
			break
		j += 1
	return mn[i:j]


def _chan_man(mn):
	"""Các chuỗi HTML thật sự được dùng làm chân màn của một phần. THUẦN."""
	ra = []
	for m in re.finditer(r"^\s*(?:var\s+)?(?:foot|ft|footer)\s*\+?=\s*", mn, re.M):
		ra.append(_cat_bieu_thuc(mn, m.end(), ";"))
	# Chân màn viết thẳng vào lời gọi frame cũng phải soi.
	for m in re.finditer(r"footer:\s*", mn):
		ra.append(_cat_bieu_thuc(mn, m.end(), ",}"))
	return ra


@ca("chân màn: frame dựng chân màn NGOÀI thân màn, và trả về thân màn")
def _():
	c = _doc("01-khung-app.js")
	# Day la SU THAT cua khung, khong phai loi. Ca kiem nay chot lai su that
	# do de ca kiem duoi co cho dua.
	dung("chân màn là khối .vf riêng", "(opt.footer ? '<div class=\"vf\">'" in c)
	dung("frame trả về thân màn", "return moiOb;" in c)
	dung("thân màn là vgbBody", "getElementById('vgbBody')" in c)


@ca("chân màn: màn nào để nút data- ở chân thì phải nghe trên root")
def _():
	# Nghe tren than man thi nut o chan man khong bao gio bam duoc. Bat bang
	# may chu khong bang mat: mat da bo lot chuyen nay tu ngay dung man Don
	# da huy toi 31/08/2026.
	for ten in _cac_phan():
		mn = _doc(ten)
		thuoc = set()
		for doan in _chan_man(mn):
			thuoc.update(re.findall(r"data-([a-z0-9_-]+)\s*=", doan))
		if not thuoc:
			continue
		# Ba cach dat lang nghe hop le, deu voi toi duoc chan man:
		#   nghe tren root, nghe THANG tren khoi .vf, hoac quet ca trang roi
		#   gan onclick tung nut.
		nghe_root = "root.addEventListener('click'" in mn or "root.onclick" in mn
		nghe_chan = "querySelector('.vf')" in mn
		for t in sorted(thuoc):
			quet_ca_trang = ("document.querySelectorAll('[data-%s]" % t) in mn
			dung(
				"%s: nút [data-%s] ở chân màn phải bấm được" % (ten, t),
				nghe_root or nghe_chan or quet_ca_trang,
			)


@ca("chân màn: màn Đơn đã huỷ nghe trên root chứ không phải trên thân màn")
def _():
	c = _doc("29-don-huy.js")
	dung("nghe trên root", "root.addEventListener('click', dhBam)" in c)
	dung("không còn nghe trên thân màn", "b.addEventListener('click', dhBam)" not in c)
	# Hai nut o chan man van con day du, khong phai go bot cai nao.
	dung("còn nút đồng bộ", 'data-dhb="dongbo"' in c)
	dung("còn nút xuất Excel", 'data-dhb="excel"' in c)
	dung("không dùng dấu em dash", "—" not in c and "–" not in c)


@ca("đơn huỷ: có nhịp tự động, không chờ ai bấm nút")
def _():
	from vagabond import don_huy as dh

	dung("có hàm nhịp tự động", hasattr(dh, "dong_bo_tu_dong"))
	dung("cửa sổ nhịp tự động ngắn hơn cửa sổ bấm tay",
		dh.NGAY_TU_DONG < dh.NGAY_GIU)
	dung("cửa sổ nhịp tự động vẫn đủ dài để bù vài lần hỏng",
		dh.NGAY_TU_DONG >= 2)


@ca("đơn huỷ: nhịp tự động đã khai trong hooks và không bao giờ ném ra ngoài")
def _():
	import inspect

	from vagabond import don_huy as dh

	# BEP la .../vagabond/public/js/bep, lui ba nac ve .../vagabond
	goc_app = os.path.dirname(os.path.dirname(os.path.dirname(BEP)))
	hooks = io.open(os.path.join(goc_app, "hooks.py"), encoding="utf-8").read()
	dung("hooks có khai nhịp", "vagabond.don_huy.dong_bo_tu_dong" in hooks)
	c = inspect.getsource(dh.dong_bo_tu_dong)
	# Nem ra ngoai la keo chet ca slot, cac nhip khac trong slot do cung
	# khong chay. Bai hoc chung cua moi nhip nen slot.
	dung("có bọc try", "try:" in c)
	dung("hỏng thì ghi nhật ký", "frappe.log_error" in c)
	dung("gọi đúng cửa sổ ngắn", "so_ngay=NGAY_TU_DONG" in c)


@ca("đơn huỷ: nhịp chạy dưới Administrator thì không vấp hàng rào vai")
def _():
	import inspect

	from vagabond import don_huy as dh

	c = inspect.getsource(dh.dong_bo)
	dung("có mở đường cho Administrator", 'frappe.session.user != "Administrator"' in c)
	dung("người bấm nút vẫn bị kiểm quyền", "_quyen()" in c)

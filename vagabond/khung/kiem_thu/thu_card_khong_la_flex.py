"""Kiem thu: .card phai la khoi thuong, khong duoc de la flex container.

Trieu chung anh Viet bao 24/08/2026: chu dam bi xuong dong, an het be ngang
tren mot vai man. Bon quy tac CSS ai cung nghi ngay toi (.kq b, .nbs b,
.nbc b, .vxr .t b) deu KHONG dinh gi toi cac man do. Di tim o do la di lac.

Nguyen nhan that
----------------
Bootstrap di kem Frappe dat tren toan bo trang:

    .card { display: flex; flex-direction: column; }

Ma ung dung dung class="card" o 544 cho. Con truc tiep cua mot flex
container bi trinh duyet BLOCKIFY: gia tri `display` TINH TOAN cua no bi
doi thanh `block`, bat ke minh khai gi. Nen moi <b> nam thang trong .card
deu thanh mot flex item chiem tron mot dong.

Do tren site that ngay 24/08/2026, tren chinh app.thevagabondpatisserie.com:

    .card                      -> display: flex, flex-direction: column
    <b> trong .card            -> display: block, rong 141px (tron the)
    <b> khi .card la block     -> display: inline, rong 33px (vua chu)

Va da thu ca cach sua sai:

    .card > b { display: inline !important }   -> VAN tinh ra block, 78px

Blockify thang moi khai bao tren chinh the con, ke ca !important. Cho nen
cach duy nhat la dung de .card lam flex container nua.

Vi sao doi .card thanh block la an toan
---------------------------------------
Ung dung chua bao gio dua vao viec .card la flex. Quy tac .card cua rieng
ung dung trong 00-nen.js chi dat background, bo goc, le va bong. Cho nao
that su can flex hay grid thi khai bang INLINE STYLE, ma inline style
thang quy tac lop, nen 17 cho do khong suy suyen.

Hai phien truoc da gap dung cai bay nay va moi nguoi tu boc mot lop div
rieng de tranh (xem ham kmHangChip trong 13-khuyen-mai.js, va cho dung no
trong 18-doi-chieu-may-in.js). Nay chan mot lan cho tat ca.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")

# The inline hay bi blockify nhat khi nam thang trong flex container.
THE_INLINE = ("b", "i", "span", "em", "strong")


def _doc(ten):
	p = os.path.join(BEP, ten)
	if not os.path.exists(p):
		return ""
	return io.open(p, encoding="utf-8").read()


def _moi_tep():
	if not os.path.isdir(BEP):
		return []
	return sorted(t for t in os.listdir(BEP) if t.endswith(".js"))


@ca(".card khai display:block, chặn blockify từ gốc")
def _():
	nen = _doc("00-nen.js")
	quy_tac = [d for d in nen.split("\n") if d.startswith(".card{")]
	la("có đúng một quy tắc .card của ứng dụng", len(quy_tac), 1)
	dung("quy tắc đó khai display:block", "display:block" in quy_tac[0])


@ca("lý do vì sao khai display:block còn ghi lại ngay cạnh")
def _():
	# Khong co doan giai thich thi phien sau se thay display:block vo duyen
	# va xoa di, roi loi quay lai ma khong ai hieu vi sao.
	nen = _doc("00-nen.js")
	dung("có nhắc Bootstrap của Frappe", "Bootstrap cua Frappe" in nen)
	dung("có nhắc chữ blockify", "BLOCKIFY" in nen or "blockify" in nen.lower())


@ca("không màn nào đặt thẻ inline nằm thẳng trong card đã khai flex hoặc grid")
def _():
	"""Cho .card la block roi thi phan lon hết dinh. NHUNG 17 cho tu khai
	inline style display:flex hoac grid thi VAN la flex container, va the
	inline nam thang trong do van bi blockify nhu cu.

	Ca kiem nay chan cho tuong lai: them mot card flex moi ma nhet <b>
	thang vao la ca kiem do ngay, thay vi doi ai do nhin thay tren man.
	"""
	mau = re.compile(
		r'class=\\?"card\\?"\s+style=\\?"([^"\\]*)\\?"[^>]*>\s*'
		r"(?:'\s*\+\s*'|\s)*<(" + "|".join(THE_INLINE) + r")[ >]"
	)
	xau = []
	for t in _moi_tep():
		s = _doc(t)
		for m in mau.finditer(s):
			if re.search(r"display\s*:\s*(inline-)?(flex|grid)", m.group(1)):
				xau.append("%s dòng %d: <%s>" % (t, s[: m.start()].count("\n") + 1, m.group(2)))
	la("không chỗ nào còn dính", xau, [])


@ca("hai chỗ đã tự bọc div để né bẫy vẫn giữ nguyên cách bọc")
def _():
	# Sua .card KHONG lam hai cho nay thua ra: chung boc chip trong mot div
	# flex-direction:row co chu dich, khac han viec .card tu la flex cot.
	km = _doc("13-khuyen-mai.js")
	dung("còn hàm bọc chip", "function kmHangChip(" in km)
	dung("hàm đó bọc bằng div flex hàng ngang", "flex-direction:row" in km)
	dung("màn đối chiếu máy in vẫn gọi hàm bọc", "kmHangChip(" in _doc("18-doi-chieu-may-in.js"))


@ca("bốn quy tắc b cũ vẫn còn nguyên, không bị sửa nhầm")
def _():
	# Bon quy tac nay CO CHU DICH lam chu dam thanh khoi, o dung bon cho
	# cua chung. Lan sua nay khong duoc dung toi. Chot lai de khoi ai
	# tuong chung la thu phamroi xoa.
	nen = _doc("00-nen.js")
	tc = _doc("02-trang-chu.js")
	for k in (".kq b{", ".nbs b{", ".nbc b{"):
		dung("còn quy tắc %s" % k.strip("{"), k in nen)
	dung("còn quy tắc .vxr .t b", ".vxr .t b{" in tc)

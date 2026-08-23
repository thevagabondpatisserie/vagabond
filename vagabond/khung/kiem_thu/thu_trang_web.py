"""Kiểm thử cơ chế đưa Web Page vào git (v288, 23/08/2026).

Anh Việt chốt: *"Không để code Web Page nằm kẹt trong Database"*, và deploy
phải *"khoá chặt rủi ro mất code do có người vô tình sửa tay trực tiếp trên
giao diện Desk"*.

Cơ chế đó ghi đè cơ sở dữ liệu mỗi lần Migrate, nên nó NGUY HIỂM đúng bằng
mức nó hữu ích: đẩy nhầm một bản cũ xuống là mất trang khách đặt bánh. Vì vậy
các ca ở đây soi kỹ ba chốt an toàn, và tự thử lại từng chốt bằng cách dựng
lại đúng tình huống hỏng.
"""

import io
import json
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__)))))
THU_MUC = os.path.join(GOC, "vagabond", "trang")


@ca("trang web: mọi trang khai trong TRANG đều có đủ tệp trong repo")
def _():
	"""Khai một trang mà quên bỏ tệp vào là deploy im lặng không làm gì.

	`dong_bo` xếp trang đó vào "chua_co" rồi đi tiếp, nên không ai biết trang
	của mình chưa hề được git quản. Ca này bắt trước khi lên site.
	"""
	from vagabond import trang

	thieu = []
	for route in sorted(trang.TRANG):
		if not os.path.exists(os.path.join(THU_MUC, "%s.json" % route)):
			thieu.append("%s.json" % route)
		if not os.path.exists(os.path.join(THU_MUC, "%s.html" % route)):
			thieu.append("%s.html" % route)
	dung("không trang nào thiếu tệp: " + (", ".join(thieu) or "đủ"), not thieu)
	dung("có đủ mười ba trang", len(trang.TRANG) == 13)


@ca("trang web: tệp json không được mang trường định danh của bản ghi")
def _():
	"""`name` và `route` là danh tính. Đẩy chúng xuống là biến thành trang khác.

	Tệp json vẫn được phép GHI hai trường đó để người đọc biết trang nào là
	trang nào, nhưng `doc_mot` phải lọc chúng ra trước khi đẩy.
	"""
	from vagabond import trang

	for route in sorted(trang.TRANG):
		moi = trang.doc_mot(route)
		for o in ("name", "route", "doctype", "modified", "owner"):
			dung("%s: không đẩy trường %s xuống" % (route, o), o not in moi)


@ca("trang web: đọc số APPVER đúng như Server Script đang chạy trên site")
def _():
	"""Đọc lệch một con số là hai cơ chế đánh nhau ngay giữa lúc migrate.

	Server Script "Chan ghi de APPVER - Web Page" tìm chữ APPVER rồi gom các
	chữ số liền sau. Hàm bên này phải làm y hệt.
	"""
	from vagabond.trang import so_appver

	la("dạng thường gặp", so_appver("// APPVER = '79'. MA APP THAT..."), 79)
	la("không dấu nháy", so_appver("var APPVER = 288;"), 288)
	la("số nằm cách vài chữ", so_appver("APPVER hien tai la 123 nhe"), 123)
	la("không có APPVER", so_appver("var x = 5;"), -1)
	la("chuỗi rỗng", so_appver(""), -1)
	la("có chữ APPVER nhưng không có số", so_appver("// APPVER chua dat"), -1)


@ca("trang web: CHỐT AN TOÀN không được hạ số APPVER")
def _():
	from vagabond.trang import duoc_day

	duoc, _ = duoc_day("APPVER=288", "APPVER=287")
	dung("tăng số thì cho qua", duoc)
	duoc, _ = duoc_day("APPVER=288", "APPVER=288")
	dung("bằng nhau thì cho qua, đây là trường hợp bình thường nhất", duoc)
	duoc, vi_sao = duoc_day("APPVER=287", "APPVER=288")
	dung("HẠ số thì CHẶN", not duoc)
	dung("và nói rõ vì sao", "287" in vi_sao and "288" in vi_sao)
	duoc, vi_sao = duoc_day("khong co so nao", "APPVER=288")
	dung("repo không có APPVER mà site có thì CHẶN", not duoc)
	duoc, _ = duoc_day("khong co so nao", "cung khong co")
	dung("hai bên đều không có APPVER thì cho qua", duoc)


@ca("trang web: CHỐT AN TOÀN lọc rác tiện ích chặn quảng cáo")
def _():
	"""Ngày 06/08/2026 hai thẻ script của AdGuard bị lưu thẳng vào trang khách.

	Khách vào trang phải tải hai đường dẫn chết. Lọc bằng tay thì có ngày
	quên, nên lọc ở đây và có ca kiểm canh.
	"""
	from vagabond.trang import loc_rac

	ban = ('<div>a</div><script src="//local.adguard.org?ts=1"></script>'
		'<p>b</p><script src="//local.adguard.org?ts=2"></script>')
	sach = loc_rac(ban)
	dung("đã bỏ hết thẻ adguard", "adguard" not in sach)
	la("giữ nguyên phần còn lại", sach, "<div>a</div><p>b</p>")
	la("nội dung sạch thì không đụng vào", loc_rac("<div>a</div>"), "<div>a</div>")
	la("rỗng vào rỗng ra", loc_rac(""), "")
	la("None vào rỗng ra", loc_rac(None), "")


@ca("trang web: bản trong repo hiện KHÔNG chứa rác và không gọi ra ngoài")
def _():
	"""Soi thẳng các tệp đang nằm trong repo, không soi hàm.

	Hàm lọc đúng mà tệp trong repo đã bẩn sẵn thì vẫn đẩy rác xuống site.
	"""
	from vagabond import trang

	ban = []
	for route in sorted(trang.TRANG):
		for duoi in ("html", "js", "css"):
			d = os.path.join(THU_MUC, "%s.%s" % (route, duoi))
			if not os.path.exists(d):
				continue
			src = io.open(d, encoding="utf-8").read()
			if "local.adguard.org" in src:
				ban.append("%s.%s: adguard" % (route, duoi))
	dung("không tệp nào chứa rác: " + ("; ".join(ban) or "sạch"), not ban)


@ca("trang web: tệp json đọc được và mang đúng route của nó")
def _():
	from vagabond import trang

	sai = []
	for route in sorted(trang.TRANG):
		d = os.path.join(THU_MUC, "%s.json" % route)
		try:
			doc = json.load(io.open(d, encoding="utf-8"))
		except Exception as e:
			sai.append("%s: %s" % (route, e))
			continue
		if doc.get("route") != route:
			sai.append("%s: json ghi route=%r" % (route, doc.get("route")))
	dung("mọi tệp json đều đúng: " + ("; ".join(sai) or "sạch"), not sai)


@ca("trang web: HÀNG RÀO có thật sự cắn không")
def _():
	"""Dựng lại đúng ba tình huống hỏng, phải thấy hàng rào đỏ.

	Ngày 23/08 đã có một ca kiểm so vị trí chuỗi mà không bắt được lỗi thật,
	nên từ nay hàng rào nào cũng phải tự chứng minh nó đỏ khi lỗi quay lại.
	"""
	from vagabond.trang import duoc_day, loc_rac, so_appver

	# 1. Dung lai canh phien khac da day v300 len site con repo con v288.
	duoc, _ = duoc_day("var APPVER = '288';", "var APPVER = '300';")
	dung("phiên khác đã lên v300 mà repo còn v288 thì bị chặn", not duoc)

	# 2. Dung lai canh ai do dan nguyen ma app tro lai trang bep, lam mat
	#    doan nap. Bản trong repo khong con APPVER nua.
	duoc, _ = duoc_day("<html>ma app dan tay</html>", "var APPVER = '288';")
	dung("bản repo mất đoạn nạp app thì bị chặn", not duoc)

	# 3. Dung lai the adguard, phai bi loc.
	dung("thẻ adguard dựng lại thì bị lọc",
		"adguard" not in loc_rac('<script src="//local.adguard.org"></script>'))

	# 4. Ham doc so phai that su doc, khong tra ve -1 cho moi thu roi lam
	#    chot an toan xanh gia.
	dung("hàm đọc số không trả -1 cho mọi thứ", so_appver("APPVER 288") == 288)

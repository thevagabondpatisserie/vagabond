"""Tồn đọng web order sau v533 (anh Việt 28/09/2026): mở được đặt bàn mà
không cần lập thêm nhóm Lark, và chân trang không in liên kết Zalo hỏng.

Vì sao có bộ ca này: site thật ngày 28/09 đọc Settings thấy web_zalo là
"zalo.me/." nên chân trang in một liên kết tương đối hỏng; và ô webhook đặt
bàn trống nên yêu cầu đặt bàn không nhắn cho ai, dù nhóm Sales đơn web đã
có. Hai chỗ đó là dữ liệu, nhưng code phải chịu được dữ liệu như vậy.
"""

from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_su_co_290 import nap
from vagabond.don_web import chuan_zalo


@ca("v534 Zalo chân trang: nhận đường dẫn đúng, tự thêm https, loại 'zalo.me/.' rồi suy từ số điện thoại")
def _zalo():
	la("đường dẫn đúng giữ nguyên", chuan_zalo("https://zalo.me/0931224334", "0931 224 334"), "https://zalo.me/0931224334")
	la("thiếu https thì thêm", chuan_zalo("zalo.me/thevagabond", "0931 224 334"), "https://zalo.me/thevagabond")
	la("zalo.link cũng nhận", chuan_zalo("https://zalo.link/abc123", ""), "https://zalo.link/abc123")
	la("'zalo.me/.' trên site thật thì suy từ số", chuan_zalo("zalo.me/.", "0931 224 334"), "https://zalo.me/0931224334")
	la("trống thì suy từ số", chuan_zalo("", "0931 224 334"), "https://zalo.me/0931224334")
	la("không có gì thì không hiện", chuan_zalo("zalo.me/.", ""), "")
	la("tên miền lạ không nhận", chuan_zalo("https://evil.example/zalo.me/abc", ""), "")
	la("javascript không nhận", chuan_zalo("javascript:alert(1)", ""), "")


@ca("v534 đặt bàn: ô webhook riêng trống thì dùng nhóm Sales đơn web, cả hai trống mới im")
def _webhook():
	for rieng, chung, mong in [("https://fixture.invalid/foh", "https://fixture.invalid/sales", "https://fixture.invalid/foh"),
	                           ("", "https://fixture.invalid/sales", "https://fixture.invalid/sales"),
	                           ("  ", "", ""), (None, None, "")]:
		gia = {"webhook_dat_ban": rieng, "webhook_don_web": chung}
		g = dict(frappe=NS(db=NS(get_single_value=lambda dt, t, gia=gia: gia[t])))
		la("riêng=%r chung=%r" % (rieng, chung), nap("dat_ban.py", "_webhook_dat_ban", g)(), mong)


@ca("v534 đặt bàn: hook và worker đều đọc URL qua MỘT nguồn _webhook_dat_ban")
def _mot_nguon():
	import io, os
	goc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
	with io.open(os.path.join(goc, "vagabond", "dat_ban.py"), encoding="utf-8") as f:
		s = f.read()
	dung("không còn chỗ nào tự đọc webhook_dat_ban", "get_single_value('Vagabond Settings', 'webhook_dat_ban')" not in s)
	la("hook và worker gọi nguồn chung (1 def + 2 chỗ gọi)", s.count("_webhook_dat_ban()"), 3)

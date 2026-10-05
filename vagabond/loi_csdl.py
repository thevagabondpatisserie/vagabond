"""Nhận ra lỗi cơ sở dữ liệu làm chết CẢ giao dịch. Phép thuần, không chạm Frappe.

Codex #428 vòng 12 (kênh Zalo) rồi Codex #444 vòng 5 (thư báo trong on_submit
phiếu thu): deadlock, chờ khoá quá hạn, mất kết nối thì MariaDB đã tự lùi hết,
kể cả savepoint. Nuốt lỗi đó là chứng từ báo thành công trong khi bút toán đã
mất. Một nguồn cho mọi chỗ cần phân biệt (AGENTS điều 18).
"""

LOI_CHET_GIAO_DICH = ("QueryDeadlockError", "QueryTimeoutError")
MA_CHET_GIAO_DICH = (1205, 1213, 2006, 2013)


def chet_giao_dich(e):
	"""THUẦN: True nếu lỗi cơ sở dữ liệu làm hỏng cả giao dịch (deadlock, chờ khoá quá
	hạn, mất kết nối). Khi đó savepoint đã mất, phải để lỗi đi lên cho chứng từ dừng."""
	if type(e).__name__ in LOI_CHET_GIAO_DICH:
		return True
	a = getattr(e, "args", ()) or ()
	return bool(a) and isinstance(a[0], int) and a[0] in MA_CHET_GIAO_DICH

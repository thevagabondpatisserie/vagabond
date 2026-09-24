"""v525: o tick "Di 242" tren ho so mon, tick san ma CCDC chua co so kho. Nhom
"CCDC dung ngay" cua v524 NGUNG dung nhung KHONG xoa (Codex #365 v3, QT-20).
Doc vagabond/ccdc_dung_ngay.py.

Khong boc try (Codex #364 v2): loi phai lam hong migrate.
"""


def execute():
	from vagabond import ccdc_dung_ngay

	return ccdc_dung_ngay.dung()

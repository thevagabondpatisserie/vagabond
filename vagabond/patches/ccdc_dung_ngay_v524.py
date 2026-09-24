"""v524: dung nhom "CCDC dung ngay" va mac dinh 242. Doc vagabond/ccdc_dung_ngay.py.

Patch rieng, KHONG boc try: Codex #364 v2. Boc try trong dong_bo_cau_truc thi
loi dung nhom chi vao Error Log, patch van ghi la xong, ban moi len site ma
thieu nhom hoac thieu mac dinh 242, hoa don khong vao 242. Loi phai lam hong
lan migrate de deploy khong bao xong khi tinh nang chua dung du.
"""


def execute():
	from vagabond import ccdc_dung_ngay

	return ccdc_dung_ngay.dung()

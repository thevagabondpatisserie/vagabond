"""Mot khoan chi nam trong bang ke cua phieu de nghi chi.

Anh Viet 19/08/2026: *"Hien tai he thong dang la 1 phieu = 1 khoan chi. Viec
nay qua mat thoi gian. Em hay cau truc lai theo dang Master-Detail (1 phieu =
Nhieu khoan chi)."*

Bang nay khong tu tinh gi ca. Moi phep cong deu lam o `de_nghi_chi.py` phia
may chu, vi so tien tren phieu la thu quyet dinh phieu co phai len giam doc
duyet hay khong (QT-19).
"""

from frappe.model.document import Document


class VagabondDeNghiChiDong(Document):
	pass

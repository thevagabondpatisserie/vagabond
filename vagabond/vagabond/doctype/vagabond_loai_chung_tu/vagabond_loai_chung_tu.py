"""Danh muc loai chung tu dinh kem cho tung khoan chi.

Anh Viet 19/08/2026: *"Loai chung tu dinh kem (Dropdown tu Danh muc)"* va
*"Neu va chi neu user chon 'Hoa don VAT', he thong moi hien thi them cac
truong: So hoa don, Ngay hoa don, Ma so thue nguoi ban."*

Vi sao co co `la_hoa_don_vat` chu khong so chuoi voi chu "Hoa don VAT"
-----------------------------------------------------------------------
So chuoi thi hom nao co nguoi sua ten dong do trong Danh muc thanh "Hoa don
GTGT" hay chi doi dau hoi thanh dau nga, ba truong hoa don im lang bien mat.
Khong bao loi gi ca, va phieu van gui di duoc ma thieu so hoa don - tuc la
mat ca bang ke mua vao ma khong ai biet.

Nen mo cai co ra thanh mot truong that. Doi ten thoai mai, khong gay.

`bat_buoc_tep` cung vay: co dong chung tu ma thieu tep dinh kem thi khong
giai trinh duoc, nhung co dong thi khong. De o day chu khong viet cung trong
ma, vi danh muc nay ke toan tu them boi duoc.
"""

from frappe.model.document import Document


class VagabondLoaiChungTu(Document):
	pass

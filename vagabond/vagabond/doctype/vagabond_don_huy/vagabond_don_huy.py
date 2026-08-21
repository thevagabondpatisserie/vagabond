"""Bản đệm một đơn Pancake đã huỷ mà tiền khách còn nằm ở công ty.

Bảng này KHÔNG phải sổ sách. Nguồn sự thật của đơn nằm ở Pancake, nguồn sự
thật của tiền nằm ở phiếu thu và phiếu chi. Bảng này chỉ để màn hình đọc
nhanh và để đếm được số việc còn tồn, vì đơn đã huỷ thì không bao giờ sang
ERPNext thành hoá đơn (xem claude/lo-hong-huy-don-khong-ve-he.md).

Vì nó chỉ là bản đệm nên bản ghi QUÁ 30 NGÀY MÀ CHƯA PHÁT SINH PHIẾU HOÀN
sẽ tự dọn, xem `don_huy.don_ban_dem`. Bản ghi đã sinh phiếu hoàn thì giữ
lại vĩnh viễn, vì lúc đó nó là một mắt xích tra cứu chứ không còn là bản
sao đọc chơi.
"""

from frappe.model.document import Document


class VagabondDonHuy(Document):
	pass

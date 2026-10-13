"""#472: lưu payload đếm mù không phá ảnh chụp tồn trên server."""
from unittest.mock import patch
from types import SimpleNamespace
from vagabond import kiem_ke
from vagabond.khung.kiem_thu.nen import ca, la


class Phieu(SimpleNamespace):
	def get(self, key):
		return getattr(self, key, None)
	def get_doc_before_save(self):
		return self.cu


@ca('#472: ô che null/0 không được ghi đè ảnh chụp thật, dòng mới đọc Bin')
def _giu_ton():
	cu = Phieu(kho='K', items=[Phieu(name='R', item_code='M', ton_he_thong=11)])
	for che in (None, 0, 999):
		r = Phieu(name='R', item_code='M', ton_he_thong=che, so_luong=0)
		moi = Phieu(name=None, item_code='N', ton_he_thong=999, so_luong=2)
		doc = Phieu(cu=cu, kho='K', items=[r, moi])
		with patch.object(kiem_ke.frappe.db, 'get_value', return_value=5):
			kiem_ke.giu_anh_chup_ton(doc)
		la('ảnh chụp giữ nguyên', r.ton_he_thong, 11)
		la('chênh lệch từ server', r.lech, -11)
		la('dòng mới lấy Bin', moi.ton_he_thong, 5)
		la('dòng mới lệch đúng', moi.lech, -3)

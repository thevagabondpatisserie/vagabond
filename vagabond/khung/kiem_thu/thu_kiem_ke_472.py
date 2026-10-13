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


@ca('#472: retry sau phiên khác đóng phiếu giữ liên kết PKK, không rơi lại vào no-op')
def _doc_co_khoa():
	import sys
	import types
	core = types.ModuleType('erpnext.stock.doctype.stock_reconciliation.stock_reconciliation')
	core.EmptyStockReconciliationItemsError = type('KhongDoi', (Exception,), {})
	moi = Phieu(trang_thai='Đã ghi sổ', stock_reconciliation='PKK-XONG',
		check_permission=lambda *a: None)
	# Mô hình hai bản đọc: snapshot cũ và current read sau khi phiên trước commit.
	# Đây là hồi quy hành vi adapter, không thay phép đo hai kết nối MariaDB.
	cu = Phieu(trang_thai='Chờ duyệt', check_permission=lambda *a: None)
	with patch.dict(sys.modules, {core.__name__: core}), \
		patch.object(kiem_ke, 'duoc_duyet', return_value=True), \
		patch.object(kiem_ke.frappe, 'get_doc', side_effect=lambda *a, **k: moi if k.get('for_update') else cu):
		kq = kiem_ke.ghi_so('KK', {})
	la('giữ liên kết phiếu phiên trước', kq['name'], 'PKK-XONG')
	la('không đổi thành no-op mất liên kết', kq['khong_doi'], False)

@ca('#473: ghi sổ chỉ lấy dòng đã đếm 0, bỏ dòng chưa đếm còn tồn 11')
def _bo_chua_dem():
	import sys
	import types
	core = types.ModuleType('erpnext.stock.doctype.stock_reconciliation.stock_reconciliation')
	core.EmptyStockReconciliationItemsError = type('KhongDoi', (Exception,), {})
	doc = Phieu(trang_thai='Chờ duyệt', kho='K', ngay_kiem='2026-10-13',
		check_permission=lambda *a:None, save=lambda:None,
		items=[Phieu(item_code='DEM',da_dem=1,so_luong=0,ton_he_thong=11),
			Phieu(item_code='CHUA',da_dem=0,so_luong=0,ton_he_thong=11)])
	dong=[]
	sr=Phieu(name='PKK',append=lambda key,row:dong.append(row),insert=lambda:None,submit=lambda:None)
	with patch.dict(sys.modules,{core.__name__:core}), \
		patch.object(kiem_ke,'duoc_duyet',return_value=True), \
		patch.object(kiem_ke.frappe,'get_doc',return_value=doc), \
		patch.object(kiem_ke.frappe,'new_doc',return_value=sr,create=True), \
		patch.object(kiem_ke.frappe,'parse_json',side_effect=lambda x:x,create=True), \
		patch.object(kiem_ke.frappe.db,'savepoint',create=True), \
		patch.object(kiem_ke.frappe.db,'get_value',return_value='CTY'), \
		patch.object(kiem_ke.frappe,'message_log',[],create=True):
		kiem_ke.ghi_so('KK',{'purpose':'Stock Reconciliation','items':[{'item_code':'CHUA','qty':0}]})
	la('chỉ dòng đếm rõ ràng',[(r['item_code'],r['qty']) for r in dong],[('DEM',0)])

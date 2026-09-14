"""#307: GL thật của tài khoản theo món/nhóm, cờ tắt vẫn theo kho.

ERPNext de591661 stock_controller.py get_inventory_account_dict và
get_inventory_account: bật cờ lấy Item/Group/Brand, tắt lấy Warehouse.
Tài khoản 1552 thử riêng, chỉ tồn tại trong điểm lưu của bộ bench.
"""
import uuid
import frappe
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from erpnext.stock import get_warehouse_account_map
from vagabond.khung.kiem_that.nen import ca, cong_ty, mot_kho, la, dung, so_cai_cua, _DA_TAO
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu
from vagabond.khung.kiem_that.thu_tai_khoan_chi_phi import _luu


def _tai_khoan(cty, tag):
	cha = frappe.db.get_value('Account', {'company': cty, 'account_type': 'Stock', 'is_group': 0}, 'parent_account')
	if not cha:
		raise AssertionError('Bench cần tài khoản kho gốc để dựng tài khoản thử')
	ra = []
	for i in (1, 2):
		d = frappe.get_doc({'doctype': 'Account', 'account_name': 'KT307-' + tag + str(i),
			'account_number': '1552' + tag + str(i), 'company': cty, 'parent_account': cha,
			'account_type': 'Stock', 'is_group': 0})
		d.insert(ignore_permissions=True)
		_DA_TAO.append((d.doctype, d.name)); ra.append(d.name)
	return ra


def _chay(bat, rieng):
	cty, tag = cong_ty(), uuid.uuid4().hex[:8]
	tk1, tk2 = _tai_khoan(cty, tag)
	kho = mot_kho(cty)
	tk_kho = get_warehouse_account_map(cty)[kho]['account']
	frappe.db.set_value('Company', cty, 'enable_item_wise_inventory_account', int(bat))
	frappe.clear_cache(doctype='Company')
	g = frappe.get_doc({'doctype': 'Item Group', 'item_group_name': 'KT307-' + tag,
		'parent_item_group': 'All Item Groups', 'is_group': 0,
		'item_group_defaults': [{'company': cty, 'default_inventory_account': tk2}]})
	g.insert(ignore_permissions=True); _DA_TAO.append((g.doctype, g.name))
	ma = _mon_thu(('BTPB-KT307-' if rieng else 'KT307-') + tag)
	d = frappe.get_doc('Item', ma); d.item_group = g.name
	# Item.insert đã có thể dựng dòng công ty mặc định. Thêm dòng thứ hai
	# làm validate_item_defaults chặn trước khi ca đi tới GL.
	dong = next((r for r in d.get('item_defaults') or [] if r.company == cty), None)
	if dong is None:
		dong = d.append('item_defaults', {'company': cty})
	dong.default_inventory_account = None
	if rieng:
		# Đi đúng cửa sản phẩm: chặng đã khai khi cấu hình trống, rồi kế toán lưu Settings.
		cfg = frappe.get_single('Vagabond Settings')
		# Toạ độ giả trong savepoint để Settings.validate chạy đủ, không gọi dịch vụ giao hàng.
		cfg.kitchen_lat = cfg.kitchen_lat or 10
		cfg.kitchen_lng = cfg.kitchen_lng or 106
		cfg.tk_ton_btp_cap1 = None; cfg.tk_ton_btp_cap2 = None
		cfg.save(ignore_permissions=True)
		d.custom_chang_btp = 'BTP sơ cấp'
	d.save(ignore_permissions=True)
	if rieng:
		cfg.tk_ton_btp_cap1 = tk2; cfg.tk_ton_btp_cap2 = tk2
		cfg.save(ignore_permissions=True)
		d.reload()
		la('Settings lần đầu tự điền món', d.custom_tk_ton_kho_tay, tk2)
		cfg.tk_ton_btp_cap1 = tk1; cfg.tk_ton_btp_cap2 = tk1
		cfg.save(ignore_permissions=True)
		d.reload()
		la('Settings lần hai cập nhật giá trị máy', d.custom_tk_ton_kho_tay, tk1)
	p = _luu(make_stock_entry(item_code=ma, qty=2, company=cty, to_warehouse=kho,
		rate=3170, do_not_save=True))
	p.reload()
	mong = (tk1 if rieng else tk2) if bat else tk_kho
	gl = so_cai_cua(p)
	dung('GL thật không rỗng', bool(gl))
	la('Nợ tài khoản đích đúng số tiền', sum(float(r.debit)-float(r.credit) for r in gl if r.account == mong), 6340)
	la('GL cân', sum(float(r.debit)-float(r.credit) for r in gl), 0)
	p.cancel()
	la('huỷ hết GL hiệu lực', len(so_cai_cua(p)), 0)
	if rieng:
		d.reload(); d.custom_tk_ton_kho_tay = None; d.save(ignore_permissions=True)
		d.reload(); d.description = 'Đã xoá tài khoản riêng'; d.save(ignore_permissions=True)
		d.reload()
		la('xoá trắng vẫn trống qua lần lưu khác', d.custom_tk_ton_kho_tay or '', '')
		# Mô phỏng mã chặng lịch sử, rồi người dùng lưu cùng chặng bằng nhãn mới.
		frappe.db.set_value('Item', d.name, 'custom_chang_btp', 'btp_so_cap')
		d.reload(); d.custom_chang_btp = 'BTP sơ cấp'; d.save(ignore_permissions=True)
		d.reload()
		la('đổi nhãn cùng chặng giữ xoá trắng', d.custom_tk_ton_kho_tay or '', '')
		cfg.tk_ton_btp_cap1 = tk2; cfg.tk_ton_btp_cap2 = tk2
		cfg.save(ignore_permissions=True); d.reload()
		la('đổi cấu hình không lấp lựa chọn trống', d.custom_tk_ton_kho_tay or '', '')


@ca('#307 GL thật: cờ bật ưu tiên tài khoản riêng trên món')
def _mon():
	_chay(True, True)


@ca('#307 GL thật: cờ bật dùng tài khoản nhóm khi món chưa khai')
def _nhom():
	_chay(True, False)


@ca('#307 GL thật: cờ tắt giữ tài khoản kho dù món khai tài khoản riêng')
def _tat():
	_chay(False, True)

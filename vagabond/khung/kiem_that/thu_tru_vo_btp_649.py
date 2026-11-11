"""v649 trên ERPNext thật: bếp nhập Bếp làm trên Kiem Banh Ngay thì BTP sẵn và Đủ
decor trừ ngay (on_update của doctype, câu UPDATE cộng dồn trên bảng BTP Banh O),
sửa bớt thì cộng lại, chốt sổ không trừ lần hai. Chạy trong savepoint của khung."""
import frappe

from vagabond.khung.kiem_that.nen import _DA_TAO, ca, la
from vagabond.khung.kiem_that.thu_kiem_banh_document import _bang_moi


def _o(ma):
	r = frappe.db.sql("""select so_btp, so_decor from `tabBTP Banh O Dong`
		where parent = 'BTP Banh O' and parenttype = 'BTP Banh O' and ma_hang = %s""", ma)
	return (int(r[0][0]), int(r[0][1])) if r else None


@ca("v649 thật: lưu Bếp làm trên Kiem Banh Ngay trừ ngay BTP sẵn, Đủ decor; sửa bớt cộng lại; huỷ không đụng; mã khác không đổi")
def _():
	b, ma = _bang_moi()
	kho = frappe.get_single("BTP Banh O")
	# Nguồn singleton được khung rollback; chỉ thay bằng fixture trong ca.
	kho.set("dong", [])
	kho.append("dong", {"ma_hang": ma, "ten_banh": "Bánh v649", "so_btp": 10, "so_decor": 9})
	kho.append("dong", {"ma_hang": ma + "-KHAC", "ten_banh": "Mã khác", "so_btp": 5, "so_decor": 5})
	kho.save(ignore_permissions=True)
	b.append("dong", {"ma_hang": ma, "ten_banh": "Bánh v649", "ton_d1": 1, "da_dat": 1, "phat_sinh": 1})
	b.insert(ignore_permissions=True)
	_DA_TAO.append((b.doctype, b.name))
	la("tạo bảng chưa làm gì thì chưa trừ", _o(ma), (10, 9))
	b.reload(); b.dong[0].sx = 1; b.save(ignore_permissions=True)
	la("làm 1", _o(ma), (9, 8))
	b.reload(); b.dong[0].sx = 3; b.save(ignore_permissions=True)
	la("làm 3", _o(ma), (7, 6))
	b.reload(); b.dong[0].sx = 1; b.save(ignore_permissions=True)
	la("sửa về 1: cộng lại 2", _o(ma), (9, 8))
	b.reload(); b.dong[0].huy = 1; b.save(ignore_permissions=True)
	la("huỷ không đụng vỏ", _o(ma), (9, 8))
	la("mã khác không đổi", _o(ma + "-KHAC"), (5, 5))
	# Codex #552 vòng 4: cột phần đã trừ có thật trong CSDL và cộng đúng (làm 1, 3, rồi về 1).
	la("phần Đủ decor đã trừ theo Bếp làm", int(frappe.db.sql("""select decor_da_lam from `tabBTP Banh O Dong`
		where parent = 'BTP Banh O' and parenttype = 'BTP Banh O' and ma_hang = %s""", ma)[0][0]), 1)
	d = [x for x in frappe.get_doc("BTP Banh O").dong if x.ma_hang == ma][0]
	la("đọc lại bảng BTP như màn đọc", (d.so_btp, d.so_decor), (9, 8))

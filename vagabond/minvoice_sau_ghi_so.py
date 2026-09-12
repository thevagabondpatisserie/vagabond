"""#266: hook After Submit cũng phải biết nhịp ghi sổ đang hoãn phát hành.

Frappe model/document.py gọi run_server_script_for_doc_event sau on_submit;
trả về trước _tu_xuat_hddt là quá muộn. Chỉ cờ nội bộ trên Document đang
submit được xét, không nhận tham số bỏ hàng rào từ API hoặc form_dict.
Snapshot đọc production 12/09/2026, đối chiếu SHA256 trước khi đưa vào git.
"""
from pathlib import Path
from vagabond.minvoice_kich_ban import bam, thay_mot

TEN = 'SI - Xuat hoa don m-invoice khi ghi so'
BAM_GOC = '626ee03b384fd21e2a6f95a974adc53f3f15338eb8b8a611a9fdad411df78c39'


def ban_goc():
	ma = (Path(__file__).parent / 'khung/kiem_thu/du_lieu/minvoice_sau_ghi_so_20260912.txt').read_text()
	if bam(ma) != BAM_GOC:
		raise ValueError('Snapshot After Submit khác production đã đối chiếu.')
	return ma


def ban_moi():
	return thay_mot(ban_goc(), "if doc.get('custom_nguon')", "if not doc.flags.get('vgb_hoan_phat_hanh') and doc.get('custom_nguon')")


def dong_bo():
	import frappe
	doc = frappe.get_doc('Server Script', TEN)
	ma = ban_moi()
	if bam(doc.script) not in (BAM_GOC, bam(ma)):
		frappe.throw('Script sau ghi sổ đã đổi khác bản review #266. Dừng migrate để đối chiếu.')
	if doc.reference_doctype != 'Sales Invoice' or doc.doctype_event != 'After Submit':
		frappe.throw('Script sau ghi sổ không còn đúng sự kiện Sales Invoice After Submit.')
	if doc.script != ma:
		doc.script = ma
		doc.save(ignore_permissions=True)

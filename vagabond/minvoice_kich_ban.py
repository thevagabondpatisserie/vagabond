"""#227: đưa bản vá hai Server Script đang chạy vào quy trình review git.

Chỉ thay các đoạn đã đọc trên site ngày 07/09/2026. Nếu ai đổi chúng trước
deploy thì dừng migrate để Claude xem khác biệt; không ghi đè cả kịch bản.
Không gọi API phát hành và không sửa bất kỳ hoá đơn cũ nào trong migrate.
"""

TEN_PHAT_HANH = "MInvoice - Phat hanh HD Sales (API)"
TEN_NAP = "VGB - Nap thong tin xuat hoa don tu Pancake"
MOC = "# VGB-227: kiểm đúng đơn và người nhận"


def thay_mot(ma, cu, moi):
	if ma.count(cu) != 1:
		raise ValueError("Kịch bản M-Invoice đã đổi khác bản review #227. Đối chiếu đoạn: " + cu[:100])
	return ma.replace(cu, moi, 1)


def sua_nap(ma):
	if MOC in ma:
		return ma
	ma = thay_mot(ma, "    si = frappe.get_doc('Sales Invoice', row['name'])", "    si = frappe.get_doc('Sales Invoice', row['name'], for_update=True)")
	ma = thay_mot(ma, "        dd = (r.get('data') or [None])[0]", """        # Tìm kiếm gần đúng không chứng minh đây là đơn cần nạp.
        khop = [d for d in (r.get('data') or []) if str(d.get('display_id') or '').strip() == so_dh.strip()
                and (not si.get('custom_pancake_id') or str(d.get('id') or '') == str(si.get('custom_pancake_id')))]
        dd = khop[0] if len(khop) == 1 else None""")
	ma = thay_mot(ma, "    can_xhd = ghi_de or not si.get('vgb_xhd_mst')", """    # Hoá đơn đã ra ngoài không được nạp lại; tên cá nhân đã xác nhận cũng được giữ.
    if si.get('custom_minvoice_id') or si.get('custom_hddt_id') or si.get('custom_hddt_so') or si.get('vgb_hddt_cho_doi_chieu'):
        continue
    can_xhd = ghi_de or (not si.get('vgb_xhd_mst') and str(si.get('vgb_xhd_ten') or '').strip() in ('', 'Bán cho người tiêu dùng'))""")
	ma = thay_mot(ma, "        if can_xhd and (ten or mst or mail):", "        if can_xhd and (ten or mst):")
	ma = thay_mot(ma, "        if not dd:\n            continue", "        if not dd:\n            loi.append(si.name + ': Không tìm được duy nhất đơn Pancake khớp cả mã đơn và ID. Kiểm lại liên kết đơn trước khi xuất.')\n            continue")
	ma = thay_mot(ma, """            if ten:
                si.db_set('vgb_xhd_ten', ten[:140], update_modified=False)
            if mst:
                si.db_set('vgb_xhd_mst', mst[:20], update_modified=False)""", """            si.db_set('vgb_xhd_ten', ten[:140], update_modified=False)
            si.db_set('vgb_xhd_mst', mst[:20], update_modified=False)""")
	# Không ghép email mới vào bộ người mua cũ; không tự lấy email ở ghi chú chung.
	ma = thay_mot(ma, "            if mail:\n                si.db_set('vgb_xhd_email', mail[:140], update_modified=False)", "            si.db_set('vgb_xhd_email', mail[:140] if (ten or mst) else '', update_modified=False)")
	return MOC + "\n" + ma


def sua_phat_hanh(ma):
	if MOC in ma:
		return ma
	ma = thay_mot(ma, "        if si.docstatus == 2:", "        if si.docstatus != 1 or si.get('vgb_huy') or si.get('vgb_tam_tinh'):")
	ma = thay_mot(ma, "        if si.get('custom_minvoice_id'):", "        if si.get('custom_minvoice_id') or si.get('custom_hddt_id') or si.get('custom_hddt_so') or si.get('vgb_hddt_cho_doi_chieu'):")
	cu = """        goiA = {'editmode': 1, 'data': [dd]}
        if che_do == 'thu':"""
	moi = """        goiA = {'editmode': 1, 'data': [dd]}
        try:
            goiA = frappe.call('vagabond.minvoice_an_toan.kiem_goi', phieu=si.name, goi=goiA, giu_cho=0 if che_do == 'thu' else 1)
        except Exception as e:
            errs.append(si.name + ': ' + str(e)[:250])
            continue
        if che_do == 'thu':"""
	ma = thay_mot(ma, cu, moi)
	ma = thay_mot(ma, """            frappe.get_doc('Server Script', 'VGB - Nap thong tin xuat hoa don tu Pancake').execute_method()
            si.reload()""", """            frappe.get_doc('Server Script', 'VGB - Nap thong tin xuat hoa don tu Pancake').execute_method()
            loi_nap = (frappe.response.get('message') or {}).get('loi') or []
            if loi_nap:
                errs.append(si.name + ': ' + str(loi_nap)[:250])
                continue
            si.reload()""")
	ma = thay_mot(ma, "                ok_n = ok_n + 1", "                si.db_set('vgb_hddt_cho_doi_chieu', 0, update_modified=False)\n                ok_n = ok_n + 1")
	# Phiếu timeout được giữ để đối chiếu, không nằm đầu mỗi lô làm kẹt đơn sau.
	ma = thay_mot(ma, "        # Tu 12/08/2026", "        dk['vgb_hddt_cho_doi_chieu'] = ['!=', 1]\n        # Tu 12/08/2026")
	# Nạp thông tin hỏng phải dừng đơn đó, không phát hành bộ dữ liệu dở dang.
	ma = thay_mot(ma, """            si.reload()
        except Exception:
            pass""", """            si.reload()
        except Exception as e:
            errs.append(si.name + ': Không nạp được thông tin đúng đơn: ' + str(e)[:150])
            continue""")
	return MOC + "\n" + ma


def dong_bo():
	"""Tính cả hai bản mới trước khi lưu để một đoạn lệch không vá nửa chừng."""
	import frappe
	moi = []
	for ten, sua in ((TEN_NAP, sua_nap), (TEN_PHAT_HANH, sua_phat_hanh)):
		if not frappe.db.exists("Server Script", ten):
			frappe.throw("Thiếu kịch bản %s. Claude cần đối chiếu cấu hình M-Invoice trước deploy #227." % ten)
		doc = frappe.get_doc("Server Script", ten)
		try:
			ma = sua(doc.script)
		except ValueError as loi:
			frappe.throw(str(loi))
		moi.append((doc, ma))
	for doc, ma in moi:
		if doc.script != ma:
			doc.script = ma
			doc.save(ignore_permissions=True)

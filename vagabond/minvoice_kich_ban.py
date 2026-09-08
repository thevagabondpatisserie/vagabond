"""#227: đưa bản vá hai Server Script đang chạy vào quy trình review git.

Nguyên tắc (sửa lại 08/09/2026 theo review Codex trên PR #228):

1. Bản vá LUÔN tính từ bản gốc đã snapshot ngày 07/09/2026
   (`khung/kiem_thu/du_lieu/minvoice_*_20260907.txt`), không tính từ bản
   đang nằm trên site. Bản trên site chỉ được nhận nếu mã băm sha256 của nó
   trùng đúng một trong ba bản đã biết: bản gốc, bản vá v446 (bench của
   Claude đã chạy patch cũ), hoặc bản vá hiện tại. Khác cả ba là dừng
   migrate, không ghi đè ai.
2. Không dùng mốc "# VGB-227" để bỏ qua. Một bench đã chạy patch v446 vẫn
   phải nhận đủ sửa mới của v447, vì mốc chỉ nói "đã vá một lần", không nói
   "đã vá đúng bản này".
3. Không gọi API phát hành và không sửa bất kỳ hoá đơn cũ nào trong migrate.
"""

import hashlib
from pathlib import Path

TEN_PHAT_HANH = "MInvoice - Phat hanh HD Sales (API)"
TEN_NAP = "VGB - Nap thong tin xuat hoa don tu Pancake"
MOC_V446 = "# VGB-227: kiểm đúng đơn và người nhận"
MOC_V449 = "# VGB-227 v449: kiểm đúng đơn và người nhận, phân loại phản hồi M-Invoice"
MOC = "# VGB-225 v454: nạp đúng nguồn Pancake"
MOC_V447 = "# VGB-227 v447: kiểm đúng đơn và người nhận, phân loại phản hồi M-Invoice"

# sha256 các bản vá cũ đã từng chạy trên bench (không còn hàm sinh, giữ mã băm
# để migrate nhận ra và vá lên bản mới thay vì dừng). Bản v447 lần đầu (đầu
# nhánh 39a47f8): nạp chưa có kiểm hết kết quả phân trang; phát hành giống hiện tại.
BAM_BAN_CU = {
	"nap": {
		"ba7e29e233595f72d87dbabb8f1ace0bbf1cef52e86e6e5be82e67b49d6bc290": "v449",
		"986a3b5d4471e6140dea1cdeb66d2f9ca099f1f1fb2d58dafb69abc61babbed6": "v447_39a47f8",
		# v448 (fa79821, đã deploy site 08/09 10:42): đối chiếu display_id mà Pancake không trả.
		"81fb0f8bbb526c305d82d96beb96193b4092fe6f915b9c42fc49b75f7d959cfa": "v448_fa79821",
	},
	"phat_hanh": {
		"44d7dfaf295e7cffb1cb0491edf5d730ba6853547f2df355b258e97dca89876e": "v449",
		# v447/v448 phát hành: chỉ khác mốc đầu tệp so với bản v449.
		"5e6464ba35de7c1fc5873b4e2f94a4d1da81781fc45bfaa71e769e9c2d52c3eb": "v448_fa79821",
	},
}

# Snapshot đọc từ Desk ngày 07/09/2026, đối chiếu FNV-1a với clipboard gốc
# (nạp 6470 ký tự / 471469736, phát hành 9865 ký tự / 511990956).
FNV_GOC = {"nap": (6470, 471469736), "phat_hanh": (9865, 511990956)}


def fnv1a(chuoi):
	h = 2166136261
	for c in chuoi:
		h ^= ord(c)
		h = (h * 16777619) & 0xFFFFFFFF
	return h


def bam(chuoi):
	return hashlib.sha256((chuoi or "").encode("utf-8")).hexdigest()


def ban_goc(loai):
	"""Bản gốc từ snapshot; kiểm độ dài và FNV-1a để chắc tệp chưa bị sửa."""
	p = Path(__file__).resolve().parent / "khung" / "kiem_thu" / "du_lieu" / ("minvoice_" + loai + "_20260907.txt")
	ma = p.read_text(encoding="utf-8")
	if (len(ma), fnv1a(ma)) != FNV_GOC[loai]:
		raise ValueError("Snapshot %s đã đổi khác bản đọc trên site 07/09/2026 (%s ký tự, FNV %s)." % (loai, len(ma), fnv1a(ma)))
	return ma


def thay_mot(ma, cu, moi):
	if ma.count(cu) != 1:
		raise ValueError("Kịch bản M-Invoice đã đổi khác bản review #227. Đối chiếu đoạn: " + cu[:100])
	return ma.replace(cu, moi, 1)


def _chan_da_va(ma):
	if ma.startswith(MOC_V446) or ma.startswith(MOC_V447) or ma.startswith(MOC_V449) or ma.startswith(MOC):
		raise ValueError("Kịch bản đã mang mốc vá; phải vá lại từ bản gốc snapshot, không vá chồng.")


# ---------------------------------------------------------------- bản v446 (giữ để nhận diện bench đã chạy patch cũ)

def _sua_nap_v446(ma):
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
	ma = thay_mot(ma, "            if mail:\n                si.db_set('vgb_xhd_email', mail[:140], update_modified=False)", "            si.db_set('vgb_xhd_email', mail[:140] if (ten or mst) else '', update_modified=False)")
	return MOC_V446 + "\n" + ma


def _sua_phat_hanh_v446(ma):
	ma = thay_mot(ma, "        if si.docstatus == 2:", "        if si.docstatus != 1 or si.get('vgb_huy') or si.get('vgb_tam_tinh'):")
	ma = thay_mot(ma, "        if si.get('custom_minvoice_id'):", "        if si.get('custom_minvoice_id') or si.get('custom_hddt_id') or si.get('custom_hddt_so') or si.get('vgb_hddt_cho_doi_chieu'):")
	ma = thay_mot(ma, """        goiA = {'editmode': 1, 'data': [dd]}
        if che_do == 'thu':""", """        goiA = {'editmode': 1, 'data': [dd]}
        try:
            goiA = frappe.call('vagabond.minvoice_an_toan.kiem_goi', phieu=si.name, goi=goiA, giu_cho=0 if che_do == 'thu' else 1)
        except Exception as e:
            errs.append(si.name + ': ' + str(e)[:250])
            continue
        if che_do == 'thu':""")
	ma = thay_mot(ma, """            frappe.get_doc('Server Script', 'VGB - Nap thong tin xuat hoa don tu Pancake').execute_method()
            si.reload()""", """            frappe.get_doc('Server Script', 'VGB - Nap thong tin xuat hoa don tu Pancake').execute_method()
            loi_nap = (frappe.response.get('message') or {}).get('loi') or []
            if loi_nap:
                errs.append(si.name + ': ' + str(loi_nap)[:250])
                continue
            si.reload()""")
	ma = thay_mot(ma, "                ok_n = ok_n + 1", "                si.db_set('vgb_hddt_cho_doi_chieu', 0, update_modified=False)\n                ok_n = ok_n + 1")
	ma = thay_mot(ma, "        # Tu 12/08/2026", "        dk['vgb_hddt_cho_doi_chieu'] = ['!=', 1]\n        # Tu 12/08/2026")
	ma = thay_mot(ma, """            si.reload()
        except Exception:
            pass""", """            si.reload()
        except Exception as e:
            errs.append(si.name + ': Không nạp được thông tin đúng đơn: ' + str(e)[:150])
            continue""")
	return MOC_V446 + "\n" + ma


# ---------------------------------------------------------------- bản hiện tại (v447)

TRANG_TOI_DA = 5
CO_TRANG = 50

DOAN_TIM_PANCAKE = """        # #227 v449: không lấy kết quả tìm đầu tiên. Pancake của tiệm không trả
        # display_id (đo trên site 08/09/2026: display_id null, mã đơn chính là id),
        # nên mã đơn đối chiếu là display_id nếu có, không thì id, đúng như lúc
        # đồng bộ đơn về (ban_hang: did = display_id or id). Có ID Pancake thì tra
        # đúng đơn theo ID rồi đối chiếu mã; không có ID thì duyệt các trang tìm
        # kiếm (tối đa %d trang x %d), dấu hết là total_pages Pancake trả về
        # (đã đo có), không có thì trang ngắn hơn %d. Chạm trần mà chưa hết thì
        # không nạp, báo kế toán kiểm liên kết.
        khop = []
        het_ket_qua = False
        pid = str(si.get('custom_pancake_id') or '').strip()
        so_dh_c = so_dh.strip()
        if pid:
            r = frappe.make_get_request(url + '/' + pid, params={'api_key': key})
            d1 = (r or {}).get('data') or {}
            if isinstance(d1, dict) and str(d1.get('id') or '') == pid and str(d1.get('display_id') or d1.get('id') or '').strip() == so_dh_c:
                khop.append(d1)
            het_ket_qua = True
        else:
            trang = 1
            while trang <= %d:
                r = frappe.make_get_request(url, params={'api_key': key, 'page_size': %d, 'page_number': trang, 'search': so_dh_c})
                ds_r = (r or {}).get('data') or []
                for d1 in ds_r:
                    if str(d1.get('display_id') or d1.get('id') or '').strip() == so_dh_c:
                        khop.append(d1)
                tong_trang = frappe.utils.cint((r or {}).get('total_pages') or 0)
                if (tong_trang and trang >= tong_trang) or (not tong_trang and len(ds_r) < %d):
                    het_ket_qua = True
                    break
                trang = trang + 1
        dd = khop[0] if (het_ket_qua and len(khop) == 1) else None
        if not dd and not het_ket_qua:
            loi.append(si.name + ': Tìm kiếm Pancake vượt %d trang mà chưa hết kết quả, không xác định được đơn duy nhất. Gắn ID Pancake cho phiếu hoặc kiểm liên kết đơn trước khi xuất.')
            continue""" % (TRANG_TOI_DA, CO_TRANG, CO_TRANG, TRANG_TOI_DA, CO_TRANG, CO_TRANG, TRANG_TOI_DA)


def sua_nap(ma):
	_chan_da_va(ma)
	# Cửa chung cho nạp tay và xuất rải. Mã TAICHO/GRABFOOD cũng nằm
	# trong custom_pancake_display_id, không phải bằng chứng nguồn Pancake.
	# Phiếu cũ thiếu nguồn vẫn đi qua kiểm ID nghiêm ngặt như trước.
	ma = thay_mot(ma, "    can_xhd = ghi_de or not si.get('vgb_xhd_mst')", """    if str(si.get('custom_nguon') or '').strip() not in ('', 'Pancake'):
        continue
    can_xhd = ghi_de or not si.get('vgb_xhd_mst')""")
	ma = thay_mot(ma, "    si = frappe.get_doc('Sales Invoice', row['name'])", "    si = frappe.get_doc('Sales Invoice', row['name'], for_update=True)")
	ma = thay_mot(ma, """        r = frappe.make_get_request(url, params={'api_key': key, 'page_size': 1, 'search': so_dh})
        dd = (r.get('data') or [None])[0]""", DOAN_TIM_PANCAKE)
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


DOAN_GUI_GOC = """        try:
            r = frappe.make_post_request(a_base + '/api/InvoiceApi78/Save', data=json.dumps(goiA), headers=a_hdr)
            if isinstance(r, dict) and ('code' in r) and r['code'] == '00' and r['data']:
                si.db_set('custom_minvoice_id', r['data']['inv_invoiceAuth_id'], update_modified=False)
                si.db_set('custom_minvoice_ngay_day', frappe.utils.now(), update_modified=False)
                si.db_set('custom_hddt_trang_thai', 'Chờ ký', update_modified=False)
                si.db_set('custom_hddt_ky_hieu', stg.ky_hieu, update_modified=False)
                so_moi = r['data'].get('inv_invoiceNumber') if isinstance(r['data'], dict) else None
                if not so_moi:
                    try:
                        rz = frappe.make_get_request(a_base + '/api/InvoiceApi78/GetInfoInvoice', headers=a_hdr, params={'keyApi': si.name})
                        so_moi = (rz.get('data') or {}).get('inv_invoiceNumber')
                    except Exception:
                        so_moi = None
                if so_moi:
                    si.db_set('custom_hddt_so', str(so_moi), update_modified=False)
                ok_n = ok_n + 1
            else:
                errs.append(row['name'] + ': ' + str(r)[:150])
        except Exception as e:
            errs.append(row['name'] + ': ' + str(e).replace(str(a_tok), '***')[-150:])"""

DOAN_GUI_MOI = """        # #227 v447: cờ chờ đối chiếu đã được kiem_goi ghi và commit TRƯỚC HTTP.
        # Sau HTTP phân loại bằng đúng quy tắc chung với Python
        # (vagabond.minvoice_an_toan.phan_loai_phan_hoi): tao / tu_choi / khong_ro.
        r = None
        loi_http = None
        try:
            r = frappe.make_post_request(a_base + '/api/InvoiceApi78/Save', data=json.dumps(goiA), headers=a_hdr)
        except Exception as e:
            loi_http = str(e).replace(str(a_tok), '***')[-150:]
        kq = frappe.call('vagabond.minvoice_an_toan.phan_loai_phan_hoi', phan_hoi=r, loi=loi_http)
        if kq['loai'] == 'tao':
            si.db_set('custom_minvoice_id', kq['id'], update_modified=False)
            si.db_set('custom_minvoice_ngay_day', frappe.utils.now(), update_modified=False)
            si.db_set('custom_hddt_trang_thai', 'Chờ ký', update_modified=False)
            si.db_set('custom_hddt_ky_hieu', stg.ky_hieu, update_modified=False)
            so_moi = r['data'].get('inv_invoiceNumber') if isinstance(r['data'], dict) else None
            if not so_moi:
                try:
                    rz = frappe.make_get_request(a_base + '/api/InvoiceApi78/GetInfoInvoice', headers=a_hdr, params={'keyApi': si.name})
                    so_moi = (rz.get('data') or {}).get('inv_invoiceNumber')
                except Exception:
                    so_moi = None
            if so_moi:
                si.db_set('custom_hddt_so', str(so_moi), update_modified=False)
            si.db_set('vgb_hddt_cho_doi_chieu', 0, update_modified=False)
            ok_n = ok_n + 1
        elif kq['loai'] == 'tu_choi':
            # Từ chối rõ: mở lại ngay để kế toán sửa rồi gửi lại, có vết.
            si.add_comment('Comment', 'M-Invoice từ chối lần gửi HĐĐT, mở lại để kế toán sửa và gửi lại: ' + str(kq['cau'])[:300])
            si.db_set('vgb_hddt_cho_doi_chieu', 0, update_modified=False)
            if not kc_goc:
                frappe.db.commit()
            errs.append(row['name'] + ': ' + str(kq['cau'])[:150] + ' (da mo lai de sua va gui lai)')
        else:
            # Không rõ: giữ cờ, kế toán đối chiếu theo mã phiếu rồi mới mở lại.
            errs.append(row['name'] + ': ' + str(kq['cau'])[:150] + ' (giu doi chieu)')"""


def sua_phat_hanh(ma):
	_chan_da_va(ma)
	# Dòng 94 bản gốc đặt form_dict['khong_commit'] = 1 để gọi kịch bản nạp,
	# rồi không trả lại, nên dòng commit cuối của chính nó không bao giờ chạy
	# (chỉ nhờ Frappe commit cuối request). Nhớ ý caller từ đầu để commit đúng.
	ma = thay_mot(ma, "che_do = frappe.form_dict.get('che_do') or 'day'", "che_do = frappe.form_dict.get('che_do') or 'day'\nkc_goc = frappe.utils.cint(frappe.form_dict.get('khong_commit') or 0)")
	ma = thay_mot(ma, "        if not frappe.utils.cint(frappe.form_dict.get('khong_commit') or 0):\n            frappe.db.commit()", "        if not kc_goc:\n            frappe.db.commit()")
	ma = thay_mot(ma, "        if si.docstatus == 2:", "        if si.docstatus != 1 or si.get('vgb_huy') or si.get('vgb_tam_tinh'):")
	ma = thay_mot(ma, "        if si.get('custom_minvoice_id'):", "        if si.get('custom_minvoice_id') or si.get('custom_hddt_id') or si.get('custom_hddt_so') or si.get('vgb_hddt_cho_doi_chieu'):")
	ma = thay_mot(ma, """        goiA = {'editmode': 1, 'data': [dd]}
        if che_do == 'thu':""", """        goiA = {'editmode': 1, 'data': [dd]}
        try:
            goiA = frappe.call('vagabond.minvoice_an_toan.kiem_goi', phieu=si.name, goi=goiA, giu_cho=0 if che_do == 'thu' else 1)
        except Exception as e:
            errs.append(si.name + ': ' + str(e)[:250])
            continue
        if che_do == 'thu':""")
	ma = thay_mot(ma, """            frappe.get_doc('Server Script', 'VGB - Nap thong tin xuat hoa don tu Pancake').execute_method()
            si.reload()""", """            frappe.get_doc('Server Script', 'VGB - Nap thong tin xuat hoa don tu Pancake').execute_method()
            loi_nap = (frappe.response.get('message') or {}).get('loi') or []
            if loi_nap:
                errs.append(si.name + ': ' + str(loi_nap)[:250])
                continue
            si.reload()""")
	ma = thay_mot(ma, DOAN_GUI_GOC, DOAN_GUI_MOI)
	# Phiếu chờ đối chiếu không nằm đầu mỗi lô làm kẹt đơn sau.
	ma = thay_mot(ma, "        # Tu 12/08/2026", "        dk['vgb_hddt_cho_doi_chieu'] = ['!=', 1]\n        # Tu 12/08/2026")
	# Nạp thông tin hỏng phải dừng đơn đó, không phát hành bộ dữ liệu dở dang.
	ma = thay_mot(ma, """            si.reload()
        except Exception:
            pass""", """            si.reload()
        except Exception as e:
            errs.append(si.name + ': Không nạp được thông tin đúng đơn: ' + str(e)[:150])
            continue""")
	return MOC + "\n" + ma


BO = ((TEN_NAP, "nap", _sua_nap_v446, sua_nap), (TEN_PHAT_HANH, "phat_hanh", _sua_phat_hanh_v446, sua_phat_hanh))


def ban_moi(loai):
	"""Bản phải có trên site sau migrate, tính từ snapshot."""
	for _ten, l, _cu, sua in BO:
		if l == loai:
			return sua(ban_goc(loai))
	raise ValueError(loai)


def doi_chieu(loai, hien_tai):
	"""Trả ("goc" | "v446" | tên bản cũ | "moi" | None) theo sha256 của bản trên site."""
	goc = ban_goc(loai)
	for _ten, l, cu, sua in BO:
		if l == loai:
			bang = dict(BAM_BAN_CU.get(loai, {}))
			bang.update({bam(goc): "goc", bam(cu(goc)): "v446", bam(sua(goc)): "moi"})
			return bang.get(bam(hien_tai or ""))
	return None


def dong_bo():
	"""Tính cả hai bản mới trước khi lưu để một đoạn lệch không vá nửa chừng."""
	import frappe
	moi = []
	for ten, loai, _cu, _sua in BO:
		if not frappe.db.exists("Server Script", ten):
			frappe.throw("Thiếu kịch bản %s. Claude cần đối chiếu cấu hình M-Invoice trước deploy #227." % ten)
		doc = frappe.get_doc("Server Script", ten)
		try:
			nhan = doi_chieu(loai, doc.script)
			ma = ban_moi(loai)
		except ValueError as loi:
			frappe.throw(str(loi))
		if nhan is None:
			frappe.throw("Kịch bản %s trên site (sha256 %s, %s ký tự) khác cả bản gốc snapshot 07/09, các bản vá cũ đã biết và bản vá hiện tại. Dừng migrate, không ghi đè; Claude đối chiếu khác biệt trước." % (ten, bam(doc.script)[:16], len(doc.script or "")))
		moi.append((doc, ma))
	for doc, ma in moi:
		if doc.script != ma:
			doc.script = ma
			doc.save(ignore_permissions=True)

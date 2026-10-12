# -*- coding: utf-8 -*-
"""#456: xuất hoá đơn cho tổ chức không có mã số thuế Việt Nam (công đoàn,
trường, hội) và khách nước ngoài.

Anh Việt chốt 08/10/2026: mã số thuế nước ngoài ghi kèm bên cạnh tên công
ty, địa chỉ ghi đúng như khách đưa. Hành vi màn Sales chạy thật trong node
(hanh_vi/xhd_khong_mst_456.js). Ở đây chốt phần máy chủ và tờ gửi m-invoice:
tên không có MST đi vào inv_buyerDisplayName, mã số thuế để trống, địa chỉ
giữ nguyên văn.
"""

import os
import subprocess

from vagabond import minvoice_an_toan as at
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _goi():
	return {"data": [{"inv_buyerEmail": "", "inv_TotalAmount": 100000, "inv_TotalAmountWithoutVat": 92593,
		"inv_vatAmount": 7407, "details": [{"data": [{"inv_itemName": "Bánh", "inv_TotalAmount": 100000}]}]}]}


@ca("#456 khách nước ngoài: tên kèm MST nước ngoài, mã số thuế Việt Nam trống, địa chỉ nguyên văn lên m-invoice")
def _():
	si = {"name": "SI-456", "vgb_xhd_ten": "ACME PTE. LTD. (MST nước ngoài: 201912345K)", "vgb_xhd_mst": "",
		"vgb_xhd_dia_chi": "10 Anson Road, #10-01, Singapore 079903", "vgb_xhd_email": "ap@acme.sg"}
	kq = at.chuan_goi(si, _goi())["data"][0]
	la("tên hiển thị là tên kèm mã", kq["inv_buyerDisplayName"], "ACME PTE. LTD. (MST nước ngoài: 201912345K)")
	la("không có tên pháp nhân VN, không có MST", (kq["inv_buyerLegalName"], kq["inv_buyerTaxCode"]), ("", ""))
	la("địa chỉ nguyên văn", kq["inv_buyerAddressLine"], "10 Anson Road, #10-01, Singapore 079903")
	la("email", kq["inv_buyerEmail"], "ap@acme.sg")


@ca("#456 công đoàn không MST: tên và địa chỉ lên tờ, không bị coi là khách lẻ")
def _():
	si = {"name": "SI-456b", "vgb_xhd_ten": "Công đoàn Công ty TNHH ABC", "vgb_xhd_mst": "",
		"vgb_xhd_dia_chi": "12 Lê Lợi, Quận 1, TP HCM", "vgb_xhd_email": ""}
	kq = at.chuan_goi(si, _goi())["data"][0]
	la("tên", kq["inv_buyerDisplayName"], "Công đoàn Công ty TNHH ABC")
	la("địa chỉ", kq["inv_buyerAddressLine"], "12 Lê Lợi, Quận 1, TP HCM")
	la("không MST", kq["inv_buyerTaxCode"], "")


@ca("#456 cổng deploy có chạy bộ ca hành vi màn Sales; bộ đó chạy xanh")
def _():
	sh = open(os.path.join(GOC, "kiem_truoc_deploy.sh"), encoding="utf-8").read()
	dung("có trong cổng", "hanh_vi/xhd_khong_mst_456.js" in sh)
	r = subprocess.run(["node", os.path.join(GOC, "vagabond", "khung", "kiem_thu", "hanh_vi", "xhd_khong_mst_456.js")],
		capture_output=True, text=True, timeout=60)
	la("node chạy xanh", (r.returncode, "0 ca hỏng" in r.stdout), (0, True))

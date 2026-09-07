# -*- coding: utf-8 -*-
"""Mã lần nhận chống trùng cho màn Nhận hàng (Codex P1 trên PR #222, vòng 3).

Phần thuần của `vagabond/lan_nhan.py`: đọc mã lần nhận, đọc dòng nhận, và
khai báo ô duy nhất trên Stock Entry. Phần chèn và ghi sổ thật, kể cả lỗi
trùng khoá ở cơ sở dữ liệu, nằm ở bộ kiểm tích hợp
`vagabond/khung/kiem_that/thu_nhan_nvl.py`; ở đây không giả lập nó.
"""

from vagabond import lan_nhan
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem


@ca("lan nhan: ma dung dang thi nhan, cat khoang trang hai dau")
def _ma_dung():
	la("mã kiểu app sinh", lan_nhan.doc_ma_lan("LN-mf3k2z9a-4h7q1x2p"), "LN-mf3k2z9a-4h7q1x2p")
	la("cắt khoảng trắng", lan_nhan.doc_ma_lan("  LN-abcdefgh  "), "LN-abcdefgh")
	la("gạch dưới cũng được", lan_nhan.doc_ma_lan("LAN_NHAN_01"), "LAN_NHAN_01")


@ca("lan nhan: thieu ma, ma ngan, ma co ky tu la, ma khong phai chuoi deu bi nem, KHONG tu sinh ma thay")
def _ma_sai():
	for x in (None, "", "   ", "ngan", "a" * 81, "LN-abc def", "LN-abc;drop", 12345678, ["LN-abcdefgh"]):
		nem("ném với %r" % (x,), lambda x=x: lan_nhan.doc_ma_lan(x))


@ca("lan nhan: doc dong nhan giu ma, so, don vi, he so, dong yeu cau; bo dong 0; bo lo neu app lo gui")
def _dong():
	ds = lan_nhan.doc_dong_nhan([
		{"item_code": "NVLT00109", "qty": 30, "uom": "Gram", "conversion_factor": 1,
			"material_request": "MAT-MR-0001", "material_request_item": "dong-1",
			"s_warehouse": "Kho Lab - TV", "t_warehouse": "Kho Bep - TV",
			"batch_no": "LO-CU", "serial_and_batch_bundle": "SABB-1"},
		{"item_code": "NVLT00110", "qty": 0},
		{"item_code": "NVLT00111", "qty": 2, "uom": "Tui", "conversion_factor": 1000},
		{"item_code": "", "qty": 5},
	])
	la("hai dòng còn lại", [d["item_code"] for d in ds], ["NVLT00109", "NVLT00111"])
	la("số", ds[0]["qty"], 30.0)
	la("dòng yêu cầu", (ds[0]["material_request"], ds[0]["material_request_item"]), ("MAT-MR-0001", "dong-1"))
	dung("không mang lô của app", "batch_no" not in ds[0] and "serial_and_batch_bundle" not in ds[0])
	dung("không mang kho trong dòng, kho lấy ở đầu phiếu", "s_warehouse" not in ds[0])
	la("hệ số quy đổi", (ds[1]["uom"], ds[1]["conversion_factor"]), ("Tui", 1000.0))
	la("hệ số thiếu thì 1", ds[0]["conversion_factor"], 1.0)


@ca("lan nhan: chuoi JSON cung doc duoc; khong dong nao > 0 thi nem")
def _dong_json():
	ds = lan_nhan.doc_dong_nhan('[{"ma": "NVLT00109", "sl": "7.5"}]')
	la("đọc từ JSON, tên khoá kiểu cũ", (ds[0]["item_code"], ds[0]["qty"]), ("NVLT00109", 7.5))
	nem("rỗng", lambda: lan_nhan.doc_dong_nhan([]))
	nem("toàn 0", lambda: lan_nhan.doc_dong_nhan([{"item_code": "A", "qty": 0}]))
	nem("None", lambda: lan_nhan.doc_dong_nhan(None))


@ca("lan nhan: o vgb_ma_lan_nhan tren Stock Entry phai DUY NHAT, khong sao chep, chi doc")
def _o_duy_nhat():
	o = [x for x in lan_nhan.TRUONG_MOI.get("Stock Entry", []) if x.get("fieldname") == "vgb_ma_lan_nhan"]
	la("có đúng một ô", len(o), 1)
	o = o[0]
	la("unique", int(o.get("unique") or 0), 1)
	la("no_copy (amend không kéo mã sang phiếu mới)", int(o.get("no_copy") or 0), 1)
	la("read_only", int(o.get("read_only") or 0), 1)
	la("kiểu Data", o.get("fieldtype"), "Data")


@ca("lan nhan: man Nhan hang khong con goi frappe.client.insert/submit, gui qua lan_nhan kem ma")
def _man_hinh():
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	duong = os.path.join(goc, "public", "js", "bep", "03-kho-chung-tu.js")
	with io.open(duong, encoding="utf-8") as f:
		src = f.read()
	dau = src.index("async function doReceive(")
	cuoi = src.index("\nfunction errMsg(", dau)
	than = src[dau:cuoi]
	dung("doReceive không gọi frappe.client.insert", "frappe.client.insert" not in than)
	dung("doReceive không gọi frappe.client.submit", "frappe.client.submit" not in than)
	dung("doReceive gọi lan_nhan.nhan_theo_phieu", "vagabond.lan_nhan.nhan_theo_phieu" in than)
	dung("gửi kèm mã lần nhận của lần đang gửi", "ma_lan_nhan: lan.ma_lan" in than)
	# Đây chỉ là dò chuỗi (điều 16): hành vi giữ mã khi hỏng, đổi mã khi
	# xong hay khi sửa số nằm ở hanh_vi/chay_nhan_hang.js ca 10 tới 14.


@ca("lan nhan: cua tra_lan_nhan CHI DOC, doc ma cung mot quy tac, va man Nhan hang co lan cho trong localStorage")
def _tra_lai():
	import io
	import os

	nem("tra với mã sai dạng cũng ném", lambda: lan_nhan.tra_lan_nhan("x"))
	nem("tra với None ném", lambda: lan_nhan.tra_lan_nhan(None))
	# Bàn giả frappe.db.get_value trả None: chưa có phiếu.
	la("chưa có phiếu thì co = 0", lan_nhan.tra_lan_nhan("LN-abcdefgh"), {"co": 0})
	# Dò chuỗi (điều 16), chỉ để chốt "có đường": hành vi giữ khoá, gửi lại
	# đúng payload, tự tra khi mở lại nằm ở hanh_vi/chay_nhan_hang.js ca 10 tới 16.
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	with io.open(os.path.join(goc, "public", "js", "bep", "03-kho-chung-tu.js"), encoding="utf-8") as f:
		src = f.read()
	dung("ghi lần chờ TRƯỚC khi gửi", src.index("ghiLanCho(mr.name, lan);") < src.index("await api('vagabond.lan_nhan.nhan_theo_phieu'"))
	dung("mở màn thì tra lại máy chủ", "if (rcv.cho) traLanCho(mr);" in src)
	dung("retry không xoá lần chờ vì mã HTTP", "daGui && !cho && loiDaChacHong(err)" in src)

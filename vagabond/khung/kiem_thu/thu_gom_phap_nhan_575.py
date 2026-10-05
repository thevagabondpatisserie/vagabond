"""v575: gom hoá đơn của nhiều pháp nhân vào một phiếu đề nghị thanh toán.

Ca thật 05/10/2026, Loan Anh (Sales Manager): Công ty TNHH Oshima's 3 bill và
anh Vũ Oshima 10 bill, cần một phiếu chung 13 bill.

Phần thuần (gom_phap_nhan.py) kiểm thẳng. Phần chạm hệ chạy THẬT
cong_no.tao_phieu trên bản Frappe giả của nen.py, chỉ thay cửa đọc hoá đơn và
cửa lưu phiếu, rồi soi các dòng phiếu được lưu.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem, gia_lap

fr = gia_lap()

from vagabond import gom_phap_nhan as gpn  # noqa: E402
from vagabond.khung.kiem_thu.thu_cong_no_571 import Doi, _nap_cong_no  # noqa: E402

cn = _nap_cong_no()


@ca("v575 thuần: gom một khách như cũ, hoá đơn khách khác bị chặn khi chưa chọn gom chung")
def _():
	la("một khách", gpn.kiem_khach("A", [("H1", "A"), ("H2", "A")]), ("", ["A"]))
	loi, _c = gpn.kiem_khach("A", [("H1", "A"), ("H2", "B")])
	la("chặn khách khác", loi, "Hoá đơn H2 không phải của khách này.")


@ca("v575 thuần: gom chung hai pháp nhân, khách đứng tên phải có hoá đơn trong phiếu")
def _():
	la("Oshima's và anh Vũ", gpn.kiem_khach("VU", [("H1", "OSH"), ("H2", "VU"), ("H3", "VU")], True),
		("", ["OSH", "VU"]))
	loi, _c = gpn.kiem_khach("KHAC", [("H1", "OSH"), ("H2", "VU")], True)
	la("đứng tên khách ngoài cuộc thì chặn", loi, "Khách đứng tên phiếu phải có ít nhất một hoá đơn trong phiếu.")
	la("chưa chọn khách đứng tên", gpn.kiem_khach("", [("H1", "A")], True)[0], "Chưa chọn khách đứng tên phiếu.")
	la("hoá đơn không có khách", gpn.kiem_khach("A", [("H1", "")], True)[0], "Hoá đơn H1 chưa có khách hàng.")


@ca("v575 thuần: chủ nợ ưu tiên ô khách nợ kế toán gán lại; dòng phiếu cũ lấy khách đứng tên")
def _():
	la("có khách nợ", gpn.chu_no("KH-GOC", "KH-NO"), "KH-NO")
	la("không có thì customer", gpn.chu_no("KH-GOC", None), "KH-GOC")
	la("dòng cũ không ghi khách", gpn.khach_dong(None, "A"), "A")
	la("dòng mới giữ khách của nó", gpn.khach_dong("B", "A"), "B")
	ra = gpn.gom_theo_khach([{"khach": "OSH", "so_tien": 1580000}, {"khach": None, "so_tien": 500000},
		{"khach": "OSH", "so_tien": 1480000}], "VU")
	la("cộng theo khách, giữ thứ tự", [(x["khach"], x["so_hd"], x["tien"]) for x in ra],
		[("OSH", 2, 3060000.0), ("VU", 1, 500000.0)])


HD = {
	"HDB-2026-01066": Doi(customer="CUS-OSHIMA", posting_date="2026-08-10", grand_total=1580000.0),
	"HDB-2026-01972": Doi(customer="CUS-OSHIMA", posting_date="2026-08-14", grand_total=1480000.0),
	"HDB-26-09-00201": Doi(customer="CUS-VU", posting_date="2026-09-01", grand_total=500000.0),
	# Kế toán gán lại chủ nợ sau khi ghi sổ: tính là của anh Vũ.
	"HDB-26-09-00202": Doi(customer="KHACH-LE", vgb_khach_no="CUS-VU", posting_date="2026-09-02", grand_total=500000.0),
}


class PhieuGia(Doi):
	def __init__(self):
		super().__init__(dong=[])

	def append(self, k, v):
		self[k].append(Doi(v))

	def insert(self, **k):
		self.name = "CN-1"
		LUU.append(self)


LUU = []


def _chay(**k):
	import json
	moc = (fr.db.get_value, getattr(fr, "new_doc", None), cn._hd_da_gom, cn._sinh_ma_cn, cn.xem_phieu, cn._kiem_quyen_ban)
	pj = getattr(fr, "parse_json", None)
	fr.parse_json = json.loads

	def get_value(dt, ten, truong=None, **kk):
		if dt == "Sales Invoice":
			h = HD.get(ten)
			if not h:
				return None
			r = Doi(h)
			r.setdefault("vgb_khach_no", None)
			r.update(docstatus=1, vgb_pt_thanh_toan="Công nợ", custom_nguon="Pancake")
			return r
		if dt == "Customer":
			return {"CUS-VU": "Anh Vũ Oshima"}.get(ten)
		return None
	fr.db.get_value = get_value
	fr.new_doc = lambda dt: PhieuGia()
	cn._hd_da_gom = lambda: set()
	cn._sinh_ma_cn = lambda: "DNTT-26-10-00001"
	cn.xem_phieu = lambda name: {"name": name}
	cn._kiem_quyen_ban = lambda: None
	del LUU[:]
	try:
		return cn.tao_phieu(**k)
	finally:
		fr.db.get_value, fr.new_doc, cn._hd_da_gom, cn._sinh_ma_cn, cn.xem_phieu, cn._kiem_quyen_ban = moc
		if pj is None:
			del fr.parse_json
		else:
			fr.parse_json = pj


@ca("v575 thật: tao_phieu gom chung Oshima's và anh Vũ, mỗi dòng ghi đúng khách của hoá đơn")
def _():
	import json
	_chay(khach="CUS-VU", hoa_don=json.dumps(list(HD)), nhieu_khach=1)
	la("lưu một phiếu", len(LUU), 1)
	p = LUU[0]
	la("đứng tên anh Vũ", (p.khach, p.ten_khach), ("CUS-VU", "Anh Vũ Oshima"))
	la("khách từng dòng", [(d.hoa_don, d.khach) for d in p.dong], [
		("HDB-2026-01066", "CUS-OSHIMA"), ("HDB-2026-01972", "CUS-OSHIMA"),
		("HDB-26-09-00201", "CUS-VU"), ("HDB-26-09-00202", "CUS-VU")])


@ca("v575 thật: không bật gom chung thì hoá đơn khách khác vẫn bị chặn như cũ")
def _():
	import json
	try:
		_chay(khach="CUS-VU", hoa_don=json.dumps(list(HD)))
		dung("phải chặn", False)
	except fr.ValidationError as e:
		la("câu chặn", str(e), "Hoá đơn HDB-2026-01066 không phải của khách này.")
	la("không lưu gì", len(LUU), 0)
	# Một khách thì vẫn lập được, dòng vẫn ghi khách.
	_chay(khach="CUS-OSHIMA", hoa_don=json.dumps(["HDB-2026-01066", "HDB-2026-01972"]))
	la("gom một khách", [d.khach for d in LUU[0].dong], ["CUS-OSHIMA", "CUS-OSHIMA"])


@ca("v575 thật: gom chung mà đứng tên khách ngoài cuộc thì chặn, không lưu")
def _():
	import json
	nem("chặn", lambda: _chay(khach="CUS-KHAC", hoa_don=json.dumps(list(HD)), nhieu_khach="1"))
	la("không lưu gì", len(LUU), 0)

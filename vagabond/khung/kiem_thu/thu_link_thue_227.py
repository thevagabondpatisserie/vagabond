"""#227: link không lẫn bill/hạn; chọn mẫu bằng tài khoản, không bằng nhãn."""

from vagabond.link_xhd import ky_link, link_hop_le
from vagabond.khung.kiem_thu.nen import ca, la


@ca("#227 link mới: không đổi bill, kéo dài hạn, dùng lại hết hạn hoặc giả chữ ký")
def _link():
	t = ky_link("SI-227", 8200, "bi-mat-thu")
	la("đúng bill, đúng hạn", link_hop_le("SI-227", 8200, t, "bi-mat-thu", 1000), True)
	for bill, han, chu, muoi, gio in [
		("SI-228", 8200, t, "bi-mat-thu", 1000),
		("SI-227", 8201, t, "bi-mat-thu", 1000),
		("SI-227", 8200, t, "sai", 1000),
		("SI-227", 8200, t, "bi-mat-thu", 8200),
		("SI-227", 8200, "ả", "bi-mat-thu", 1000),
		("SI-227", "nan", t, "bi-mat-thu", 1000),
		("SI-227", "８２００", t, "bi-mat-thu", 1000),
	]:
		la("từ chối link bị thay hoặc hết hạn", link_hop_le(bill, han, chu, muoi, gio), False)



@ca("#227 thuế: chính sách đầu phiếu giữ qua nạp lại mẫu món; chế độ riêng giữ nhiều mức")
def _giu_thue():
	from types import SimpleNamespace
	from vagabond.thue_don_mua import xoa_thue_rieng, theo_mau_dau_phieu
	class Phieu(dict):
		pass
	dong = SimpleNamespace(item_tax_template="8%", item_tax_rate='{"1331":8}')
	p = Phieu(vgb_thue_theo_mau=1, taxes_and_charges="5%", items=[dong])
	xoa_thue_rieng(p)
	la("bỏ template riêng bằng chuỗi rỗng", dong.item_tax_template, "")
	la("bỏ bản đồ cũ", dong.item_tax_rate, "{}")
	dong.item_tax_template, dong.item_tax_rate = "8%", '{"1331":8}'
	xoa_thue_rieng(p)
	la("sửa giá không kéo lại mẫu 8", dong.item_tax_template, "")
	p["vgb_thue_theo_mau"] = 0
	dong.item_tax_template = "10%"
	theo_mau_dau_phieu(p)
	la("giữ chế độ từng món", dong.item_tax_template, "10%")


@ca("#227 tạo link: hạn tính lúc gửi, chặn sai quyền/đã gửi/bill cũ, QR cũ không đổi")
def _tao_link():
	import ast
	from datetime import datetime, timedelta
	from pathlib import Path
	from types import SimpleNamespace
	from urllib.parse import parse_qs, urlparse
	from vagabond.minvoice_an_toan import da_gui
	ma = Path(__file__).resolve().parents[2].joinpath("ban_hang.py").read_text()
	cay = ast.parse(ma)
	class BoImport(ast.NodeTransformer):
		def visit_ImportFrom(self, node): return node if node.module == "urllib.parse" else None
	cac = []
	for n in cay.body:
		if isinstance(n, ast.FunctionDef) and n.name in ("pos_link_xhd", "_chan_phieu_xhd"):
			n.decorator_list = []
			cac.append(BoImport().visit(n))
	class Phieu(dict):
		def __getattr__(self, k): return self[k]
		def check_permission(self, quyen):
			if not self.get("duoc_doc"): raise ValueError("sai quyền")
	p = Phieu(posting_date="2026-09-08", duoc_doc=True)
	def nem(s): raise ValueError(s)
	gio = datetime(2026, 9, 8, 20, 0, 0)
	f = SimpleNamespace(get_doc=lambda *a: p, throw=nem,
		local=SimpleNamespace(conf={"encryption_key": "thu"}))
	ns = {"frappe": f, "cint": lambda x: int(x or 0), "_kiem_quyen": lambda: None,
		"link_khach": lambda x: "https://order.example" + x, "ky_link": ky_link,
		"da_gui": da_gui, "now_datetime": lambda: gio,
		"getdate": lambda x: datetime.fromisoformat(str(x)).date(),
		"get_datetime": lambda x: x, "timedelta": timedelta, "_xhd_token": lambda n: "qr-cu"}
	exec(compile(ast.fix_missing_locations(ast.Module(body=cac, type_ignores=[])), "link-thuc", "exec"), ns)
	goi = ns["pos_link_xhd"]
	q = parse_qs(urlparse(goi("SI-227", 1)["url"]).query)
	la("neo đúng SI", q["d"], ["SI-227"])
	la("2 giờ từ bây giờ", int(q["e"][0]), int(gio.timestamp()) + 7200)
	la("ký đúng hạn", q["t"][0], ky_link("SI-227", q["e"][0], "thu"))
	la("QR cũ giữ nguyên", goi("SI-227")["duong"], "/xhd?d=SI-227&t=qr-cu")
	for truong, gt in [("duoc_doc", False), ("vgb_hddt_cho_doi_chieu", 1),
		("custom_hddt_so", "123"), ("docstatus", 2), ("vgb_huy", 1),
		("posting_date", "2026-09-07")]:
		cu = p.get(truong)
		p[truong] = gt
		try:
			goi("SI-227", 1)
			la("phải chặn " + truong, True, False)
		except ValueError:
			pass
		p[truong] = cu

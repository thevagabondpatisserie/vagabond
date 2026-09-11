"""Render wkhtmltopdf và upload HTTP trên bench dùng một lần, PR263."""
import base64
import io
import json
import os
from pathlib import Path


def chay():
	if os.environ.get("GITHUB_ACTIONS") != "true":
		raise RuntimeError("Chỉ chạy trên bench CI dùng một lần")
	import frappe
	from pypdf import PdfReader, PdfWriter
	from PIL import Image
	from frappe.utils.pdf import get_pdf
	from vagabond import ho_so_tt as hs
	from vagabond.mau_in.le_in import css_trang
	from vagabond.ho_so_bo_sung import nen_pdf
	thu = Path(os.environ["VGB_ARTIFACTS"])
	frappe.init(site="bench-ci.localhost", sites_path=".")
	frappe.connect()
	assert frappe.conf.get("vagabond_bench_thu")
	frappe.set_user("Administrator")
	ket = []
	try:
		anh = io.BytesIO()
		Image.new("RGB", (1200, 1800), "#222222").save(anh, format="JPEG")
		mot = {"b64": base64.b64encode(anh.getvalue()).decode(), "kieu": "jpeg", "nhan": "Chứng từ thử " * 20}
		for so in (1, 2, 9):
			html = '<html><head>' + css_trang().replace('A4 portrait', 'A4 landscape') + '</head><body><div class="vgb-in">' + hs.luoi_anh([mot] * so) + '</div></body></html>'
			pdf = get_pdf(html, options={"page-size": "A4", "orientation": "Landscape", "margin-top": "15mm", "margin-bottom": "15mm", "margin-left": "15mm", "margin-right": "15mm"})
			(thu / ("app-263-%s-anh.pdf" % so)).write_bytes(pdf)
			r = PdfReader(io.BytesIO(pdf))
			assert len(r.pages) == (so + 1) // 2, (so, len(r.pages))
			for p in r.pages:
				assert abs(float(p.mediabox.width) * 25.4 / 72 - 297) < 1
				assert abs(float(p.mediabox.height) * 25.4 / 72 - 210) < 1
			ket.append({"anh": so, "trang": len(r.pages), "a4_ngang": True})
		w = PdfWriter()
		for _ in range(100):
			w.add_blank_page(width=595, height=842)
		b = io.BytesIO()
		w.write(b)
		noi = b.getvalue()
		assert len(PdfReader(io.BytesIO(nen_pdf(noi))).pages) == 100
		w.add_blank_page(width=595, height=842)
		b = io.BytesIO()
		w.write(b)
		for x, cau in ((b.getvalue(), "100 trang"), (b"x" * (13 * 1024 * 1024), "12 MB")):
			try:
				nen_pdf(x)
			except ValueError as e:
				assert cau in str(e)
			else:
				raise AssertionError("Không chặn " + cau)
	finally:
		frappe.db.rollback()
		frappe.destroy()
	# WSGI thật có login, multipart upload và RPC, chạy sau bộ hoàn nguyên.
	from frappe.app import application
	from werkzeug.test import Client
	from werkzeug.wrappers import Response
	c = Client(application, Response)
	url = "http://bench-ci.localhost"
	r = c.post('/api/method/login', base_url=url, data={"usr": "Administrator", "pwd": "bench-only-admin"})
	assert r.status_code == 200, r.get_data(as_text=True)
	r = c.post('/api/method/upload_file', base_url=url, data={"is_private": "1", "file": (io.BytesIO(noi), "app-263-thu.pdf")})
	assert r.status_code == 200, r.get_data(as_text=True)
	ten = r.get_json()["message"]["name"]
	r = c.post('/api/method/vagabond.ho_so_bo_sung.nen_tep', base_url=url, data={"tep": ten})
	assert r.status_code == 200, r.get_data(as_text=True)
	assert r.get_json()["message"]["ma"]
	ket.append({"upload_http": True, "nen_rpc": True, "pdf_100_trang": True, "gioi_han": True})
	(thu / "in-app-263.json").write_text(json.dumps(ket, ensure_ascii=False, indent=2))
	print(json.dumps(ket, ensure_ascii=False), flush=True)


if __name__ == "__main__":
	chay()

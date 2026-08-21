"""Ca kiem cho bieu mau in do ma nguon giu.

Khong can jinja2: may chay CI cua GitHub tay khong, khong cai them goi nao
(tieu chuan so 9). Nen o tang khung chi PHAN TICH TINH tep mau. Phep render
that chay o tang tich hop tren site, xem khung/kiem_that/thu_mau_in.py.

Nghe co ve yeu, nhung chinh may phep tinh nay bat duoc dung ba loi anh Viet
bao ngay 21/08/2026:
  - o Ma NCC goi nham truong ten cong ty,
  - vong lap chi lay Purchase Invoice nen bang trong voi don mua hang,
  - khong co nhanh nao cho phieu KHONG neo vao chung tu nao.
"""

from vagabond import mau_in
from vagabond.khung.kiem_thu.nen import ca, dung, la

TEP = "chung_tu_thanh_toan.html"


def _mau():
	return mau_in.doc_mau(TEP)


@ca("mau in: khai bao trong MAU_IN phai tro toi tep co that")
def _khai_bao():
	dung("co khai chung tu thanh toan", "Vagabond - Chứng từ thanh toán" in mau_in.MAU_IN)
	for ten, (tep, doctype) in mau_in.MAU_IN.items():
		noi_dung = mau_in.doc_mau(tep)
		dung("tep %s doc duoc va khong rong" % tep, len(noi_dung) > 500)
		dung("mau %s co khai doctype" % ten, bool(doctype))


@ca("mau in: cac khoi Jinja phai dong du, mo bao nhieu dong bay nhieu")
def _can_bang():
	s = _mau()
	# Mot the {% endfor %} thieu la ca ban in trang, va loi chi lo ra luc in.
	la("for va endfor", s.count("{% for "), s.count("{% endfor %}"))
	so_if = s.count("{% if ") + s.count("{%- if ")
	so_endif = s.count("{% endif %}") + s.count("{%- endif -%}") + s.count("{%- endif %}")
	la("if va endif", so_if, so_endif)


@ca("mau in: o Ma doi tac KHONG duoc goi ten cong ty mot lan nua")
def _ma_doi_tac():
	# Anh Viet 21/08/2026: "he thong dang lay nham Ten cong ty" o o
	# Ma NCC / Vendor code.
	s = _mau()
	i = s.find("Vendor code")
	dung("van con o Ma NCC", i > -1)
	khuc = s[i:i + 300]
	dung("khong dung party_name ngay tai o ma", "doc.party_name" not in khuc)
	dung("o ma in ra bien da tinh san", "ma_hien" in khuc)
	j = s.find("set ma_hien")
	dung("co dung bien ma_hien", j > -1)
	dong_ma = s[j:j + 220]
	dung("ma_hien lay tu doc.party", "doc.party" in dong_ma)


@ca("mau in: bang chi tiet phai nhan CA don mua hang, khong chi hoa don")
def _nhan_don_mua():
	s = _mau()
	dung("co nhanh Purchase Invoice", '"Purchase Invoice"' in s)
	dung("co nhanh Purchase Order", '"Purchase Order"' in s)
	i = s.find("for rf in doc.references")
	j = s.find('"Purchase Order"')
	dung("nhanh don mua nam trong vong lap references", -1 < i < j)
	dung("co nhanh cuoi cho loai chung tu khac", "{% else %}" in s[i:])


@ca("mau in: phieu KHONG neo chung tu nao van phai in ra noi dung giai trinh")
def _khong_co_tham_chieu():
	# Hoan ung khong hoa don, hoan tien khach, chi tu tai khoan cong ty deu
	# roi vao ca nay. Anh Viet chot: "xuat PDF ra luc nao cung phai co noi
	# dung giai trinh".
	s = _mau()
	dung("co nhanh du phong khi bang rong", "{% if not dong %}" in s)
	i = s.find("{% if not dong %}")
	khuc = s[i:i + 420]
	dung("nhanh do lay dien giai cua phieu", "doc.remarks" in khuc)
	dung("nhanh do co so tien", "doc.paid_amount" in khuc)


@ca("mau in: cot Noi dung phai in bien cua dong, khong bo trong")
def _cot_noi_dung():
	s = _mau()
	dung("co o cot noi dung", 'class="nd"' in s)
	i = s.find('<td class="nd">')
	khuc = s[i:i + 90]
	dung("cot noi dung in r.nd", "r.nd" in khuc)
	la("so lan append vao bang", s.count('"nd":'), s.count("dong.append"))


@ca("mau in: nhan cot doi theo loai chung tu, khong cung nhac 'So hoa don'")
def _nhan_cot():
	s = _mau()
	dung("co bien chi_hoa_don", "chi_hoa_don" in s)
	dung("co nhan So chung tu", "Số chứng từ" in s)
	dung("van giu nhan So hoa don cho ca chi co hoa don", "Số hóa đơn" in s)


@ca("mau in: chi hoi Supplier va Customer, khong hoi bua bang khac")
def _khong_hoi_bua():
	# Payment Entry con nhan party_type la Employee hay Shareholder. Hai bang
	# do khong co cot supplier_name / customer_name; hoi bua vao la Frappe nem
	# loi cot khong ton tai va ban in ra TRANG - kieu hong chi lo ra dung luc
	# co nguoi bam nut In.
	s = _mau()
	dung("khong truyen thang doc.party_type lam ten bang",
		'get_value(doc.party_type' not in s)
	dung("co nhanh rieng cho Supplier", 'get_value("Supplier"' in s)
	dung("co nhanh rieng cho Customer", 'get_value("Customer"' in s)
	dung("co bien la_khach de tach nhanh", "la_khach" in s)

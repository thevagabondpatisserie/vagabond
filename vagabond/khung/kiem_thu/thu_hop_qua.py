"""Ca kiểm cho tuỳ biến ruột hộp quà. Toàn phép thuần, không cần site."""

from vagabond import hop_qua as hq
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = [
	{"ma": "BANU00021", "ten": "Bánh sầu riêng", "sl": 1},
	{"ma": "BANU00022", "ten": "Bánh trà xanh", "sl": 1},
	{"ma": "BANU00023", "ten": "Bánh thập cẩm", "sl": 2},
]


@ca("hop qua: doc chuoi JSON hong thi tra rong, KHONG no")
def _doc_hong():
	la("chuoi rac", hq.doc_ruot("{khong phai json"), [])
	la("rong", hq.doc_ruot(""), [])
	la("None", hq.doc_ruot(None), [])
	# JSON dung nhung khong phai danh sach cung tra rong.
	la("khong phai list", hq.doc_ruot('{"ma":"X"}'), [])


@ca("hop qua: doc duoc chuoi JSON that")
def _doc_that():
	la("mot mon", hq.doc_ruot('[{"ma":"A","ten":"A","sl":1}]'),
		[{"ma": "A", "ten": "A", "sl": 1}])


@ca("hop qua: nan ruot bo dong rac va vet so luong am")
def _nan():
	r = hq.chuan_ruot([
		{"ma": "A", "ten": "Banh A", "sl": 2},
		{"ma": "", "ten": ""},
		"khong phai tu dien",
		{"ma": "B", "ten": "Banh B", "sl": 0},
		{"ma": "C", "ten": "Banh C", "sl": -3},
	])
	la("so dong con lai", len(r), 3)
	la("sl 0 thanh 1", r[1]["sl"], 1)
	la("sl am thanh 1", r[2]["sl"], 1)


@ca("hop qua: thieu ten thi lay ma lam ten")
def _thieu_ten():
	r = hq.chuan_ruot([{"ma": "BANU00021", "sl": 1}])
	la("ten", r[0]["ten"], "BANU00021")


@ca("hop qua: doi mon thi biet la da doi")
def _da_doi():
	moi = [
		{"ma": "BANU00050", "ten": "Bánh hạt dẻ long nhãn", "sl": 1},
		{"ma": "BANU00022", "ten": "Bánh trà xanh", "sl": 1},
		{"ma": "BANU00023", "ten": "Bánh thập cẩm", "sl": 2},
	]
	dung("co doi", hq.da_doi_ruot(GOC, moi))
	dung("giu nguyen thi khong doi", not hq.da_doi_ruot(GOC, GOC))


@ca("hop qua: xep lai thu tu KHONG tinh la doi ruot")
def _doi_thu_tu():
	dao = list(reversed(GOC))
	dung("dao thu tu van la mot hop", not hq.da_doi_ruot(GOC, dao))


@ca("hop qua: cau mo ta doc ra dung viec khach xin")
def _mo_ta():
	moi = [
		{"ma": "BANU00050", "ten": "Bánh hạt dẻ long nhãn", "sl": 1},
		{"ma": "BANU00022", "ten": "Bánh trà xanh", "sl": 1},
		{"ma": "BANU00023", "ten": "Bánh thập cẩm", "sl": 2},
	]
	t = hq.mo_ta_thay_doi(GOC, moi)
	dung("co chu doi", "đổi" in t)
	dung("neu ten mon bo", "sầu riêng" in t)
	dung("neu ten mon them", "hạt dẻ long nhãn" in t)


@ca("hop qua: khong doi gi thi cau mo ta rong")
def _mo_ta_rong():
	la("rong", hq.mo_ta_thay_doi(GOC, GOC), "")


@ca("hop qua: bot mon thi mo ta noi bo")
def _bot_mon():
	t = hq.mo_ta_thay_doi(GOC, GOC[:2])
	dung("co chu bo", "bỏ" in t)


@ca("hop qua: dem dung so banh trong hop")
def _dem():
	la("tong", hq.so_mon(GOC), 4)
	la("rong", hq.so_mon([]), 0)


@ca("hop qua: don gia cong phu thu")
def _don_gia():
	la("cong them", hq.don_gia_sau_phu_thu(850000, 120000), 970000)
	la("khong phu thu", hq.don_gia_sau_phu_thu(850000, 0), 850000)


@ca("hop qua: phu thu AM la tru tien, van nhan")
def _phu_thu_am():
	la("bot banh thi tru", hq.don_gia_sau_phu_thu(850000, -100000), 750000)


@ca("hop qua: KHONG cho don gia xuong duoi 0")
def _khong_am():
	la("chan san", hq.don_gia_sau_phu_thu(100000, -500000), 0)


@ca("hop qua: hop theo mua PHAI doc dinh muc mua vu, KHONG doc Product Bundle")
def _nguon_mua_vu():
	# Chot bang ca kiem chu khong bang loi ghi chu: ERPNext tu choi tao
	# Product Bundle cho mon dang theo ton kho, ma hai hop Trung thu deu
	# theo ton va phai giu nhu vay cho chot chan ban lo dem duoc. Ly do day
	# du o dau ham ruot_goc.
	import inspect

	nguon = inspect.getsource(hq.ruot_goc)
	dung("doc mua vu truoc", "_ruot_tu_mua_vu" in nguon)
	dung("co noi ly do", "validate_main_item" in nguon)
	# Ham doc dinh muc mua vu phai ton tai va doc dung bang.
	dung("co ham doc dinh muc", callable(getattr(hq, "_ruot_tu_mua_vu", None)))
	dm = inspect.getsource(hq._ruot_tu_mua_vu)
	dung("doc dung bang", "Vagabond Mua Vu Dinh Muc" in dm)
	dung("loc dung cot ma hop", "ma_hop" in dm)


@ca("hop qua: quyen tuy bien PHAI lay tu bao_gia.QUYEN_SUA")
def _quyen():
	# Ngay 21/08/2026 Loan Anh bi chan khong tuy bien duoc hop du chi ay sua
	# bao gia moi ngay, vi cho nay tu che mot danh sach vai rieng va bo sot
	# "Sales User". Chot bang ca kiem de khong ai dung lai danh sach rieng.
	#
	# Doc bao_gia.py bang AST chu KHONG import: bao_gia keo cong_no, cong_no
	# keo ban_hang, ban_hang import requests. May chay CI cua GitHub tay
	# khong nen ca kiem nao keo theo thu vien mang la ca kiem dat sai cho.
	import ast
	import inspect
	import os

	tep = os.path.join(os.path.dirname(os.path.abspath(hq.__file__)),
		"bao_gia.py")
	cay = ast.parse(open(tep, encoding="utf-8").read())
	quyen = None
	for n in cay.body:
		if isinstance(n, ast.Assign) and any(
				getattr(t, "id", "") == "QUYEN_SUA" for t in n.targets):
			quyen = ast.literal_eval(n.value)
	dung("bao_gia co khai QUYEN_SUA", quyen is not None)
	dung("bao_gia co Sales User", "Sales User" in (quyen or ()))
	nguon = inspect.getsource(hq._quyen_sua)
	dung("import tu bao_gia", "from vagabond.bao_gia import QUYEN_SUA" in nguon)
	dung("khong tu che danh sach vai", "Sales User" not in nguon)
	chan = inspect.getsource(hq._chan)
	dung("cong goi ham chung", "_quyen_sua()" in chan)


@ca("hop qua: doi ngang thi KHONG bu them tien")
def _doi_ngang():
	# Banh trong hop deu loai 80 gram (anh Viet chot 21/08/2026).
	moi = [{"ma": "A", "ten": "A", "sl": 2}, {"ma": "C", "ten": "C", "sl": 2}]
	dung("doi mon van du so", hq.doi_ngang(GOC, moi))
	dung("bot mon la khong ngang", not hq.doi_ngang(GOC, [{"ma": "A", "sl": 1}]))
	la("doi ngang, phu thu 0, khong nhac", hq.nhac_phu_thu(GOC, moi, 0), "")
	dung("doi ngang ma go phu thu thi nhac",
		"để 0" in hq.nhac_phu_thu(GOC, moi, 50000))
	dung("them mon thi nhac ghi duong",
		"dương" in hq.nhac_phu_thu(GOC, GOC + [{"ma": "Z", "ten": "Z", "sl": 1}], 0))
	dung("bot mon thi nhac ghi am",
		"ÂM" in hq.nhac_phu_thu(GOC, [{"ma": "A", "ten": "A", "sl": 1}], 0))

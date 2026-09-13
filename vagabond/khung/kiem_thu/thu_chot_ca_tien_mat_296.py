"""Chốt ca chỉ đếm tiền mặt (issue #296 mục 3, anh Việt chốt 12/09/2026).

Vì sao có bộ ca này: trước v487 màn chốt ca vẽ mỗi phương thức một ô đếm
mù. Thu ngân không "đếm" được tiền chuyển khoản hay tiền thẻ, nên các ô đó
chỉ là gõ lại số máy, gõ lệch một số là ca lệch và phải bịa lý do. Từ nay
chỉ đếm tiền mặt; phương thức khác giữ số máy trong biên bản để đối chiếu,
không có lệch. Lệch chuyển khoản bắt ở bảng đối soát SePay (#290 D2).

Ca kiểm chia ba lớp: phép thuần (bảng đối soát, đọc số đếm), nguồn duy
nhất (chot_ca không tự ghép bảng ở chỗ khác), và hành vi màn hình chạy
thật trong node (hanh_vi/chot_ca_296.js).
"""

import os
import subprocess

from vagabond import ca_quay as cq
from vagabond.khung.kiem_thu.nen import ca, dung, la

MAY = {"Tiền mặt": 4850000.0, "Chuyển khoản": 3200000.0, "Quẹt thẻ": 950000.0}
SO_BILL = {"Tiền mặt": 41, "Chuyển khoản": 18, "Quẹt thẻ": 5}
GOC = os.path.join(os.path.dirname(__file__), "..", "..", "..")


def _py(ten):
	with open(os.path.join(GOC, "vagabond", ten), encoding="utf-8") as f:
		return f.read()


# ------------------------------------------------------------- phép thuần


@ca("#296.3 chỉ dòng Tiền mặt có lệch, dòng khác đếm = máy và lệch 0")
def _chi_tien_mat_lech():
	bang = cq.ghep_chi_tien_mat(MAY, 5300000, 500000, SO_BILL)
	tm = [d for d in bang if d["phuong_thuc"] == "Tiền mặt"][0]
	ck = [d for d in bang if d["phuong_thuc"] == "Chuyển khoản"][0]
	the = [d for d in bang if d["phuong_thuc"] == "Quẹt thẻ"][0]
	la("tiền mặt phải có = máy + tiền lẻ", tm["phai_co"], 5350000.0)
	la("tiền mặt thiếu 50k", tm["lech"], -50000.0)
	la("chuyển khoản đếm bằng máy", ck["dem"], 3200000.0)
	la("chuyển khoản không lệch", ck["lech"], 0.0)
	la("thẻ không lệch", the["lech"], 0.0)
	la("số bill vẫn đi theo dòng", ck["so_bill"], 18)
	la("tổng lệch chỉ là lệch tiền mặt", cq.tong_lech(bang), 50000.0)
	dung("phải gõ lý do vì tiền mặt lệch", cq.can_ly_do(bang))


@ca("#296.3 tiền mặt khớp thì cả ca khớp, dù máy có nhiều phương thức")
def _khop():
	bang = cq.ghep_chi_tien_mat(MAY, 5350000, 500000, SO_BILL)
	la("không lệch", cq.tong_lech(bang), 0.0)
	dung("không đòi lý do", not cq.can_ly_do(bang))
	la("Tiền mặt vẫn đứng đầu bảng", bang[0]["phuong_thuc"], "Tiền mặt")


@ca("#296.3 máy không ghi tiền mặt mà thu ngân đếm ra tiền thì vẫn lộ dòng Tiền mặt")
def _khong_co_tien_mat_tren_may():
	bang = cq.ghep_chi_tien_mat({"Chuyển khoản": 100000.0}, 20000, 0)
	ten = [d["phuong_thuc"] for d in bang]
	dung("có dòng Tiền mặt", "Tiền mặt" in ten)
	tm = [d for d in bang if d["phuong_thuc"] == "Tiền mặt"][0]
	la("thừa 20k không rõ nguồn", tm["lech"], 20000.0)


@ca("#296.3 đọc số tiền mặt: nhận số, chuỗi số, chuỗi có dấu chấm nghìn, JSON bản app cũ")
def _doc_so():
	la("số", cq.doc_tien_mat_dem(5350000), 5350000.0)
	la("chuỗi số", cq.doc_tien_mat_dem("5350000"), 5350000.0)
	la("dấu chấm nghìn", cq.doc_tien_mat_dem("5.350.000"), 5350000.0)
	la("JSON bản mới", cq.doc_tien_mat_dem('{"Tiền mặt": "5350000"}'), 5350000.0)
	# App bản cũ còn trên máy quầy gửi đủ mọi ô: chỉ lấy tiền mặt, bỏ phần
	# còn lại, không được ném lỗi làm thu ngân kẹt không chốt được ca.
	la("JSON bản cũ", cq.doc_tien_mat_dem({"Tiền mặt": 1, "Chuyển khoản": 9}), 1.0)
	la("số 0 là hợp lệ", cq.doc_tien_mat_dem(0), 0.0)


@ca("#296.3 đọc số tiền mặt: thiếu, âm, không phải số đều ném lỗi")
def _doc_so_hong():
	for x in ["", None, "-5", "abc", {"Chuyển khoản": 1}, "{}", "nan", "inf", float('nan'), float('inf'), {"Tiền mặt":"abc"}, True, "1.5", 1.5, "1..000"]:
		try:
			cq.doc_tien_mat_dem(x)
			dung("phải ném lỗi với %r" % (x,), False)
		except ValueError:
			dung("đã chặn %r" % (x,), True)


# ------------------------------------------------------------ nguồn duy nhất


@ca("#296.3 chot_ca dựng bảng qua MỘT nguồn ghep_chi_tien_mat, không tự ghép")
def _mot_nguon():
	# Điều 18 CLAUDE.md: giá trị tính ở nhiều nơi thì mỗi nơi là một chỗ
	# sai. Phép dò chuỗi ở đây chỉ chốt "không còn chỗ nào tự ghép", hành vi
	# thật kiểm ở các ca trên và trong node.
	than = _py("ca_quay.py").split("def chot_ca(")[1].split("\n@frappe.whitelist()")[0]
	dung("gọi ghep_chi_tien_mat", "ghep_chi_tien_mat(" in than)
	dung("không gọi thẳng ghep_doi_soat", "ghep_doi_soat(" not in than)
	dung("đọc số bằng doc_tien_mat_dem", "doc_tien_mat_dem(" in than)
	dung("không còn doc_so_dem trong chot_ca", "doc_so_dem(" not in than)
	dung("tiền mặt đếm ghi từ biến đã đọc", "doc.tien_mat_dem = tien_mat_dem" in than)


@ca("#296.3 tinh_trang và chot_ca báo cờ chi_dem_tien_mat cho màn hình")
def _co_bao():
	s = _py("ca_quay.py")
	la("ba chỗ trả cờ", s.count('"chi_dem_tien_mat": 1'), 4)


# -------------------------------------------------------- hành vi màn hình


@ca("#296.3 màn Chốt ca chạy thật trong node: một ô, đúng payload, đúng bảng")
def _hanh_vi():
	js = os.path.join(os.path.dirname(__file__), "hanh_vi", "chot_ca_296.js")
	r = subprocess.run(["node", js], capture_output=True, text=True, timeout=30, cwd=GOC)
	la(r.stdout + r.stderr, r.returncode, 0)
	dung("đủ 9 ca", "PASS 9" in r.stdout)


@ca('#299 một dấu nghìn và JSON cũ không đổi nghĩa số tiền')
def dau_nghin():
	la('5.000 là năm nghìn',cq.doc_tien_mat_dem('5.000'),5000)
	la('chỉ đọc dòng tiền mặt',cq.doc_tien_mat_dem({'Tiền mặt':'5.000','Chuyển khoản':-9}),5000)


@ca('#290 D2 bảng chốt ca dùng mã Pancake, không cộng trùng hai cách khớp')
def sepay_sales():
	from types import SimpleNamespace as NS
	from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap
	from vagabond import chiem_sao_ke
	for co_ma_bill in (False,True):
		d=D(name='SI',grand_total=100000,docstatus=0,custom_nguon='Pancake',custom_pancake_display_id='296',vgb_pt_thanh_toan='Chuyển khoản',vgb_ma_tham_chieu='VGB296',vgb_tam_tinh=0)
		vet=[]
		def doc(shop, ids):vet.append(ids);return {'296':{'nhan':100000,'gd':['GD1']}}
		g=dict(frappe=NS(get_all=lambda *a,**kw:[d],utils=NS(cint=lambda x:int(x or 0))),
			_kiem_quyen=lambda:None,_loc_diem_ban=lambda q:{},getdate=lambda x:x,nowdate=lambda:'2026-09-13',flt=lambda x:float(x or 0),
			_sepay_theo_ma_bill=lambda *a:({'VGB296':{'nhan':100000,'gd':['GD1']}} if co_ma_bill else {},[]),
			_sepay_theo_don=doc,cfg=lambda:D(pancake_shop_id='SHOP'),chiem_sao_ke=chiem_sao_ke,
			pt_thanh_toan=NS(chua_ve_tien=lambda:[],ve_sau=lambda:[],khong_thu=lambda:[]))
		k=nap('ban_hang.py','pos_chot_ca',g)('SALES')
		la('đọc đúng mã đơn một lần',vet,[['296']]);la('đủ tiền',k['ck_ve'],100000);la('không thiếu giả',k['ck_thieu'],[])

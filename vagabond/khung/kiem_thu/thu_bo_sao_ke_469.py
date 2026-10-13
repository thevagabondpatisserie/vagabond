"""Phép thuần cho việc 4 #469. Không thay bằng chứng giao dịch DB/bench."""
from vagabond.khung.kiem_thu.nen import ca, la, dung, nem
from vagabond.khop_sao_ke import xet_bo


def dong(ma, tien, **kw):
	return dict(name=ma, tien=tien, bank_account="MB-CTY", chieu="ra", **kw)


@ca("#469 bộ tiền Adecco 450 triệu và 264138056 đủ 714138056")
def _():
	a = dong("ACC-BTN-2026-07222", 450000000)
	b = dong("ACC-BTN-2026-07223", 264138056)
	la("đủ", xet_bo([a,b],714138056,"MB-CTY","ra")["ket_qua"], "du")
	k = xet_bo([a],714138056,"MB-CTY","ra")
	la("thiếu", k["thieu"],264138056)
	la("trạng thái thiếu",k["ket_qua"],"thieu")
	la("thừa",xet_bo([a,b],700000000)["ket_qua"],"thua")


@ca("#469 bộ tiền lỗi từng dòng, trùng không cộng hai lần")
def _():
	for doi in ({"bank_account":"ACB"},{"chieu":"vao"},{"chu_cu":"APP-X"},{"tien":"NaN"}):
		d = dong("A",100); d.update(doi)
		k=xet_bo([d],100,"MB-CTY","ra")
		la("lỗi",k["ket_qua"],"loi")
		la("chỉ đúng dòng lỗi",k["loi"][0]["name"],"A")
	la("trùng",xet_bo([dong("A",50),dong("A",50)],100)["ket_qua"],"loi")


@ca("#469 một dòng chia hai phiếu chỉ lấy phần còn, không nhân đôi tiền")
def _():
	la("phiếu 600",xet_bo([dong("A",1000,con_lai=1000,phan_bo=600)],600)["ket_qua"],"du")
	la("phiếu 400",xet_bo([dong("A",1000,con_lai=400,phan_bo=400)],400)["ket_qua"],"du")
	la("hết phần",xet_bo([dong("A",1000,con_lai=0,phan_bo=100)],100)["ket_qua"],"loi")
	la("không dung sai chiếm dư dòng",xet_bo([dong("A",1000,con_lai=400,phan_bo=400.5)],400.5)["ket_qua"],"loi")


@ca("#469 số tiền bộ hữu hạn, dương và dung sai chỉ áp tổng")
def _():
	for v in (0,-1,"NaN","Infinity",None):
		nem("từ chối %s" % v,lambda:xet_bo([],v),ValueError)
	la("trong dung sai",xet_bo([dong("A",100.5)],100)["ket_qua"],"du")
	la("ngoài dung sai",xet_bo([dong("A",101.1)],100)["ket_qua"],"thua")

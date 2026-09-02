# -*- coding: utf-8 -*-
"""Kiem thu hai viec anh Viet chot ngay 02/09/2026.

Viec mot: O NGUOI BAN NGAY LUC LEN DON
--------------------------------------
Anh Viet: *"Con thieu, can mot ban rieng: o nguoi ban ngay luc len don, de
het ro 1.071 hoa don chua gan nguoi ban cua phan he KPI. Viec nay cham man
tinh tien nen em tach ra -> em lam doan nay luon nhe, nhung theo anh hieu
thi no se tu map theo ten dang nhap cua nguoi dang thao tac?"*

Cau tra loi la CO cho don do nguoi lam ra, va KHONG cho don may dong bo
ve. Do chinh la cho ro 1.071 to sinh ra: don Pancake va don san keo ve
luc khong co ai dang dang nhap, nen khong co "nguoi dang thao tac" nao de
map. Ba hang rao phai con nguyen:

  1. Chay nen (dong bo, migrate, patch) thi de TRONG, khong gan.
  2. Administrator va Guest khong phai nguoi ban, de TRONG.
  3. Chi gan luc TAO MOI, va chi khi o con trong. To da co nguoi ban roi
     thi lan luu sau khong duoc ghi de - neu khong, quan ly gan tay xong
     lan luu ke tiep la mat.

De trong CO CHU DICH: nhung to do van nam trong ro "chua gan" de con
nhin thay va gan tay. Ghi "He thong" vao do la giau mot ro so lieu sai
duoi mot cai ten nghe nhu that.

Viec hai: BANG KIEM KHO THEO DIEM BAN
-------------------------------------
Anh Viet: *"Trong man kiem banh theo ngay em cho them 2 tab nua la Kiem
banh 9 TCV va tab Kiem banh NVHTN dum anh voi cac truong ton dau, nhap
banh (chia ra cac dot: dot 1, dot 2, dot 3,...), da ban (tu dong bo
realtime tu hoa don ban hang sang), co the ban,... so co the ban nay se
hien thi sang man tinh tien luon ke ben moi mon"*.

Bon cho de hong ma ca kiem nay chot lai:

  1. Cot "da ban" khong duoc nam trong danh sach sua tay. Mo cua cho sua
     tay la mo cua cho lech, va la mat luon ly do bang nay ton tai.
  2. "Co the ban" KHONG duoc ep ve khong. So am la dau hieu co cai da ban
     ma khong ai ghi nhap - do la thu can nhin thay, khong phai thu can
     giau.
  3. Dem duoc SO KHONG cung la mot ket qua dem. Lay "kiem_tay > 0" lam
     dau hieu da kiem thi cuoi ngay ban het sach se bi hieu la chua ai
     kiem, va ton dau ngay mai lay nham so may.
  4. Chip "con/het" o man tinh tien chi ve cho mon CO trong bang. Mon
     khong ai theo doi ton ma ghi "het" la chan ban mot mon dang con.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import kiem_kho, nguoi_ban

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(duong):
	with io.open(os.path.join(GOC, duong), encoding="utf-8") as f:
		return f.read()


# ------------------------------------------------------- o nguoi ban

@ca("nguoi ban: don do nguoi lam ra thi map theo tai khoan dang dang nhap")
def _():
	la("thu ngan", nguoi_ban.ai_ban("de@thevagabond.vn"), "de@thevagabond.vn")
	la("sales", nguoi_ban.ai_ban("loananh@thevagabond.vn"), "loananh@thevagabond.vn")
	la("co khoang trang thua", nguoi_ban.ai_ban("  de@thevagabond.vn  "), "de@thevagabond.vn")


@ca("nguoi ban: don may dong bo ve thi de trong, khong gan bua")
def _():
	la("dang chay nen", nguoi_ban.ai_ban("loananh@thevagabond.vn", dang_chay_nen=True), "")
	la("Administrator", nguoi_ban.ai_ban("Administrator"), "")
	la("Guest", nguoi_ban.ai_ban("Guest"), "")
	la("khong co ai", nguoi_ban.ai_ban(""), "")
	la("None", nguoi_ban.ai_ban(None), "")


@ca("nguoi ban: hook chi gan luc tao moi va chi khi o con trong")
def _():
	m = _doc("vagabond/nguoi_ban.py")
	i = m.find("def truoc_khi_luu(")
	dung("co ham hook", i > 0)
	than = m[i:i + 1400]
	dung("chi gan luc tao moi", "is_new" in than)
	dung("khong ghi de o da co nguoi", "doc.get(O)" in than or "doc.get(%s)" % "O" in than)


@ca("nguoi ban: cua ngo mo ra ngoai chi co dung mot ham gan tay")
def _():
	from vagabond.khung.kiem_thu import thu_cua_ngo

	la("dung mot cua ngo", thu_cua_ngo.CUA_NGO.get("nguoi_ban.py"), ["gan"])
	m = _doc("vagabond/nguoi_ban.py")
	dung("truoc_khi_luu khong duoc whitelist", "@frappe.whitelist()\ndef truoc_khi_luu" not in m)


@ca("nguoi ban: to quy ve tai khoan may thi man hinh ghi 'chua gan'")
def _():
	# Cung dinh nghia voi ro "chua gan" ben KPI: to nao quy ve tai khoan
	# may la to chua ai gan. Ghi ten "He thong" vao do la giau mot ro so
	# lieu sai duoi mot cai ten nghe nhu that.
	kt = _doc("vagabond/ke_toan.py")
	dung("may chu danh dau to cua tai khoan may", 'o["nguoi_ban_may"]' in kt)
	dung("dung chung bang tai khoan may voi nguoi_ban", "_MAY_BAN" in kt)
	js = _doc("vagabond/public/js/bep/16-mua-hang.js")
	dung("man hinh ghi chua gan", "d.nguoi_ban_may" in js and "chưa gán" in js)
	dung("Administrator la tai khoan may", "Administrator" in nguoi_ban.MAY)
	dung("Guest la tai khoan may", "Guest" in nguoi_ban.MAY)


@ca("nguoi ban: go bo nguoi gan nham duoc, chan tai khoan may")
def _():
	m = _doc("vagabond/nguoi_ban.py")
	i = m.find("def gan(")
	than = m[i:i + 1800]
	dung("chuoi rong la go bo, khong bi chan", "if nguoi and nguoi in MAY:" in than)
	dung("co ghi vet", "Comment" in than)
	dung("mat ghi vet khong lam hong viec gan", "except Exception:" in than)


@ca("nguoi ban: hoa don cu khong bi sua nguoc lai (dieu 11 cua anh Viet)")
def _():
	for tep in ("vagabond/nguoi_ban.py",):
		m = _doc(tep)
		dung("%s khong co nhip quet lai hoa don cu" % tep, "for si in frappe.get_all" not in m)
		dung("%s khong ghi hang loat" % tep, "db_set" not in m or "backfill" not in m)


# ------------------------------------------------------ bang kiem kho

@ca("kiem kho: co the ban = ton dau + nhap - da ban - hong + dieu chinh")
def _():
	la("ngay thuong", kiem_kho.tinh_co_the_ban(10, 24, 18, 1, 0), 15)
	la("khong nhap gi", kiem_kho.tinh_co_the_ban(6, 0, 4, 0, 0), 2)
	la("dieu chinh am", kiem_kho.tinh_co_the_ban(10, 0, 0, 0, -3), 7)
	la("het sach", kiem_kho.tinh_co_the_ban(5, 0, 5, 0, 0), 0)


@ca("kiem kho: ban lo hon so nhap thi ra so AM, khong ep ve khong")
def _():
	la("ban lo ba cai", kiem_kho.tinh_co_the_ban(2, 0, 5, 0, 0), -3)
	dung("phai am that", kiem_kho.tinh_co_the_ban(0, 0, 1, 0, 0) < 0)
	m = _doc("vagabond/kiem_kho.py")
	i = m.find("def tinh_co_the_ban(")
	than = m[i:m.find("def tinh_lech(")]
	dung("khong co max(0 trong phep tinh", "max(0" not in than)


@ca("kiem kho: cong sau dot nhap, va biet dot trong ke tiep la dot nao")
def _():
	o = {"nhap_1": 12, "nhap_2": 8, "nhap_3": 0, "nhap_4": 0, "nhap_5": 0, "nhap_6": 0}
	la("tong nhap", kiem_kho.tong_nhap(o), 20)
	la("dot ke tiep", kiem_kho.dot_ke_tiep(o), 3)
	day = dict((k, 1) for k in kiem_kho.O_NHAP)
	la("sau dot da day", kiem_kho.dot_ke_tiep(day), 0)
	la("chua nhap gi", kiem_kho.dot_ke_tiep({}), 1)
	la("dung sau dot", len(kiem_kho.O_NHAP), 6)


@ca("kiem kho: dem duoc SO KHONG cung la mot ket qua dem")
def _():
	# Cuoi ngay ban het sach, nguoi dem ghi 0. Neu he hieu la "chua ai
	# kiem" thi ton dau ngay mai lay so may thay vi so nguoi dem.
	la("da kiem, dem duoc 0", kiem_kho.tinh_lech(0, 1, 2), -2)
	la("chua ai kiem", kiem_kho.tinh_lech(0, 0, 2), 0)
	la("kiem khop", kiem_kho.tinh_lech(5, 1, 5), 0)
	la("kiem thua", kiem_kho.tinh_lech(7, 1, 5), 2)
	la("mang sang mai khi dem duoc 0", kiem_kho.con_lai_ngay_mai(0, 1, 4), 0)
	la("mang sang mai khi chua kiem", kiem_kho.con_lai_ngay_mai(0, 0, 4), 4)
	la("so am khong mang sang mai", kiem_kho.con_lai_ngay_mai(0, 0, -3), 0)


@ca("kiem kho: cot may dem khong nam trong danh sach sua tay")
def _():
	for cot in ("da_ban", "co_the_ban", "lech", "ma_hang"):
		dung("%s khong sua tay duoc" % cot, cot not in kiem_kho.SUA_DUOC)
	for cot in ("ton_dau", "hong", "dieu_chinh", "kiem_tay", "nhap_1", "nhap_6"):
		dung("%s phai sua tay duoc" % cot, cot in kiem_kho.SUA_DUOC)


@ca("kiem kho: hoa don con nhap van tinh la da ban, hoa don huy thi khong")
def _():
	m = _doc("vagabond/kiem_kho.py")
	i = m.find("def da_ban(")
	than = m[i:m.find("def _ten_hang(")]
	dung("bill nhap van tru", "si.docstatus < 2" in than)
	dung("bill huy khong tru", "ifnull(si.vgb_huy, 0) = 0" in than)
	dung("phieu tam tinh khong tru", "ifnull(si.vgb_tam_tinh, 0) = 0" in than)
	dung("loc dung quay", "ifnull(si.vgb_quay, '') = %s" in than)
	dung("loc dung ngay", "si.posting_date = %s" in than)


@ca("kiem kho: da_ban khong mo ra ngoai, tam cua ngo con lai deu la cua man hinh")
def _():
	from vagabond.khung.kiem_thu import thu_cua_ngo

	ds = thu_cua_ngo.CUA_NGO.get("kiem_kho.py") or []
	dung("da_ban khong mo ra ngoai", "da_ban" not in ds)
	for t in ("bang", "chot", "con_lai", "diem_ds", "them_dong", "tim_mon", "luu_o", "xoa_dong"):
		dung("%s phai co cua ngo" % t, t in ds)


@ca("kiem kho: tab sinh tu danh sach diem ban, khong go cung TCV va NVHTN")
def _():
	m = _doc("vagabond/kiem_kho.py")
	dung("doc tu diem_ban", "diem_ban.ds(chi_bat=True)" in m)
	dung("chi lay diem co quay", 'd["quay"]' in m)
	dung("khong go cung ma diem", '"TCV"' not in m and '"NVHTN"' not in m)
	j = _doc("vagabond/trang/kiem-banh.js")
	dung("man hinh cung sinh tab tu may chu", "kiem_kho.diem_ds" in j or 'API("diem_ds")' in j)


@ca("kiem kho: ten phieu mot diem mot ngay, khong the trung")
def _():
	la("TCV", kiem_kho.ten_phieu("TCV", "2026-09-02"), "KKD-TCV-2026-09-02")
	la("viet thuong cung ra hoa", kiem_kho.ten_phieu("nvhtn", "2026-09-02"), "KKD-NVHTN-2026-09-02")
	dung("hai diem khac ten",
		kiem_kho.ten_phieu("TCV", "2026-09-02") != kiem_kho.ten_phieu("NVHTN", "2026-09-02"))


@ca("kiem kho: may chi tu them dong cho banh, khong tu them ca phe va tra")
def _():
	dung("banh o", kiem_kho.la_banh("BAWC00098"))
	dung("banh nuong", kiem_kho.la_banh("BANU00065"))
	dung("banh si", kiem_kho.la_banh("BAWS00001"))
	dung("ca phe khong tu them", not kiem_kho.la_banh("NUCF00012"))
	dung("phu kien khong tu them", not kiem_kho.la_banh("BAPK00003"))
	dung("ma rong", not kiem_kho.la_banh(""))


@ca("kiem kho: dong may tu them ma chua ai khai thi khong bao so ra man tinh tien")
def _():
	# Ngay dau bat bang, moi dong deu do may tu them vi thay co ban ra, va
	# con lai cua chung deu am (bang dung so da ban). Ve chip "het" cho tat
	# ca la chan ban ca tu banh trong ngay dau.
	chua = {"theo_doi": 0, "ton_dau": 0, "hong": 0, "dieu_chinh": 0}
	dung("dong may tu them, chua ai cham", not kiem_kho.dang_theo_doi(chua))
	da = dict(chua); da["theo_doi"] = 1
	dung("co nguoi cham vao roi", kiem_kho.dang_theo_doi(da))
	khai = dict(chua); khai["ton_dau"] = 6
	dung("khai ton dau la dang theo doi", kiem_kho.dang_theo_doi(khai))
	nhap = dict(chua); nhap["nhap_2"] = 4
	dung("ghi mot dot nhap la dang theo doi", kiem_kho.dang_theo_doi(nhap))
	hong = dict(chua); hong["hong"] = 1
	dung("ghi hang hong la dang theo doi", kiem_kho.dang_theo_doi(hong))

	m = _doc("vagabond/kiem_kho.py")
	i = m.find("def con_lai(")
	than = m[i:]
	dung("con lai bo qua dong chua khai", "if not dang_theo_doi(r):" in than)
	dung("sua mot o la bat co theo doi", "r.theo_doi = 1" in m)
	dung("them tay thi theo doi ngay", '"theo_doi": 1,' in m)
	j = _doc("vagabond/trang/kiem-banh.js")
	dung("bang co bao dong chua khai", "kk-chuakhai" in j and "chưa khai tồn" in j)


@ca("man tinh tien: chip con hang chi ve cho mon co trong bang kiem kho")
def _():
	j = _doc("vagabond/public/js/bep/09-tinh-tien-quay.js")
	dung("co goi con_lai", "vagabond.kiem_kho.con_lai" in j)
	i = j.find("function posChipCon(")
	dung("co ham ve chip", i > 0)
	than = j[i:i + 900]
	dung("mon khong theo doi ton thi khong ve chip",
		"n === null" in than and "undefined" in than)
	dung("so 0 van ve chip", "n <= 0" in than)
	dung("loi goi khong duoc lam chet o tim mon", "catch (eCL)" in j)

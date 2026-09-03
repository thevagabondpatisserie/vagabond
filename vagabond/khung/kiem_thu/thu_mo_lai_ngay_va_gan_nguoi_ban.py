# -*- coding: utf-8 -*-
"""Kiem thu hai viec anh Viet chot ngay 03/09/2026.

MUC 1: MO LAI MOT NGAY DA CHOT NHAM
-----------------------------------
Ngay 02/09 quay District 1 bam "Chot ngay" luc giua buoi. Bang kiem kho
cua chinh hom do khoa cung tu luc do toi nua dem: khong nhap them dot
banh nao, khong sua duoc o nao, va KHONG CO DUONG NAO MO LAI. Muon cuu
phai vao Desk sua tay tinh trang phieu.

Loi that o day KHONG phai la nguoi bam sai gio. Loi la mot thao tac
thuong ngay lai khong co duong lui. Nen ban nay lam hai viec, va thu tu
quan trong:

  1. Co duong MO LAI. Day moi la thu chua benh.
  2. Bam som thi HOI LAI mot cau. Day chi la giam so lan phai dung toi
     viec 1. Tuyet doi khong duoc bien thanh CHAN theo gio: co ngay tiem
     dong som, co ngay doi ca kiem so luc trua. Chan cung theo gio la
     lay mot lo hong doi lay mot lo hong khac.

Va mot hang rao nua, de o `mo_lai`: mo lai KHONG duoc dung vao ton dau
cua ngay hom sau. Chot xong thi sales co the da nhap tiep cho ngay mai;
xoa so do di la lay mat cong cua nguoi khac. Nguoi bam phai duoc NHAC
rang con mot buoc nua (bam Chot ngay lai) thi so moi chay sang.

MUC 2 (viec 4): GAN TAY NGUOI BAN NGAY TREN MAN HOA DON
-------------------------------------------------------
Ro 1.071 to hoa don "chua gan nguoi ban" ben KPI la don may dong bo ve
(Pancake, cac san giao hang): luc do khong co ai dang dang nhap nen
khong co "nguoi dang thao tac" nao de lay. O nguoi ban de trong CO CHU
DICH - xem `vagabond/nguoi_ban.py`. Nhung de trong ma khong co cach gan
lai thi ro do khong bao gio voi di.

Bon hang rao ca kiem nay chot:

  1. To chua gan phai NHIN THAY duoc la chua gan, chu khong duoc lang le
     hien ten nguoi lap phieu thay vao. Hien ten may thay ten nguoi ban
     la giau mot so lieu sai duoi mot cai ten nghe nhu that.
  2. "Chua gan" chi tinh khi nguoi lap la TAI KHOAN MAY. To cu lap boi
     nguoi that truoc khi co o nay thi khong phai la thieu.
  3. Quyen gan tach RIENG khoi quyen xem. Thu ngan van thay to nay chua
     co nguoi ban, nhung khong tu gan duoc: o nay quyet dinh doanh so va
     hoa hong roi vao tay ai.
  4. Nut gan chi cham o nguoi ban, khong cham mot con so tien nao va
     khong cham hoa don dien tu. Nho vay gan lai luc nao cung an toan,
     dung dieu anh Viet chot 13/08/2026 ve du lieu qua khu.
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


# ------------------------------------------------------------- muc 1: chot som

@ca("chot som: gio truoc gio dong cua thi coi la som, gio sau thi khong")
def _():
	dung("9h sang la som", kiem_kho.chot_som(9))
	dung("13h trua la som", kiem_kho.chot_som(13))
	dung("16h van la som", kiem_kho.chot_som(16))
	dung("17h khong con som", not kiem_kho.chot_som(17))
	dung("21h khong som", not kiem_kho.chot_som(21))
	dung("23h khong som", not kiem_kho.chot_som(23))


@ca("chot som: gio hong hay thieu thi KHONG hoi, de nguoi bam di tiep")
def _():
	# Hoi lai la de giup, khong duoc bien thanh cai chan nguoi ta lai chi vi
	# may khong doc noi dong ho cua chinh no.
	dung("None thi khong hoi", not kiem_kho.chot_som(None))
	dung("chuoi rong thi khong hoi", not kiem_kho.chot_som(""))
	dung("chu thi khong hoi", not kiem_kho.chot_som("toi"))
	dung("so am thi khong hoi", not kiem_kho.chot_som(-3))
	dung("gio > 23 thi khong hoi", not kiem_kho.chot_som(99))


@ca("chot som: doi duoc gio dong cua, khong go cung mot con so")
def _():
	dung("tiem dong 14h thi 15h het som", not kiem_kho.chot_som(15, 14))
	dung("tiem dong 22h thi 20h van som", kiem_kho.chot_som(20, 22))


@ca("chot som: chi HOI, tuyet doi khong CHAN")
def _():
	m = _doc("vagabond/kiem_kho.py")
	i = m.find("def chot(diem")
	than = m[i:m.find("def mo_lai(")]
	dung("tra ve co hoi lai", '"hoi_lai": 1' in than)
	dung("nguoi dong y thi di tiep", "cint(dong_y_som)" in than)
	dung("khong throw vi gio", "chưa tới giờ đóng cửa" in than and "frappe.throw(\n\t\t\t\"Bây giờ" not in than)
	# Chi hoi cho NGAY HOM NAY. Chot bu cho ngay hom qua thi gio hien tai
	# khong noi len dieu gi, hoi la hoi vo nghia.
	dung("chi hoi cho hom nay", "ngay == hom_nay" in than)


# ------------------------------------------------------------- muc 1: mo lai

@ca("mo lai: co cua ra ngoai va da khai o hang rao cua ngo")
def _():
	from vagabond.khung.kiem_thu import thu_cua_ngo

	m = _doc("vagabond/kiem_kho.py")
	dung("co whitelist", "@frappe.whitelist()\ndef mo_lai(" in m)
	dung("da khai cua ngo", "mo_lai" in thu_cua_ngo.CUA_NGO.get("kiem_kho.py", []))


@ca("mo lai: KHONG duoc dung vao ton dau ngay hom sau")
def _():
	# Chot xong thi sales co the da nhap tiep cho ngay mai. Mo lai ma keo
	# theo xoa so do la lay mat cong cua nguoi khac, va khong ai bao truoc.
	m = _doc("vagabond/kiem_kho.py")
	than = m[m.find("def mo_lai("):m.find("def con_lai(")]
	for cam in ("add_days", "ton_dau", "ngay_mai"):
		dung("khong cham %s cua ngay mai" % cam, cam not in than)


@ca("mo lai: bat buoc nhac nguoi bam rang con mot buoc nua")
def _():
	m = _doc("vagabond/kiem_kho.py")
	than = m[m.find("def mo_lai("):m.find("def con_lai(")]
	dung("co loi nhac", '"nhac"' in than)
	dung("nhac dung chuyen ton dau", "Tồn đầu ngày mai" in than)
	dung("nhac phai bam chot lai", "Chốt ngày lại" in than)


@ca("mo lai: co hang rao quyen va co ghi vet")
def _():
	m = _doc("vagabond/kiem_kho.py")
	than = m[m.find("def mo_lai("):m.find("def con_lai(")]
	dung("co kiem quyen", "_chan_neu_khong_duoc_sua()" in than)
	dung("ngay dang mo thi tu choi", "không cần mở lại" in than)
	dung("chua co bang thi tu choi", "chưa có bảng kiểm kho" in than)
	dung("co ghi vet", '"doctype": "Comment"' in than)
	dung("ghi vet nho ai chot truoc do", "trước đó" in than)
	# Mat mot dong ghi vet khong duoc lam hong viec mo lai.
	dung("ghi vet hong thi bo qua", "except Exception:" in than)


@ca("mo lai: man hinh co nut, va nut chi hien khi ngay DA chot")
def _():
	ht = _doc("vagabond/trang/kiem-banh.html")
	js = _doc("vagabond/trang/kiem-banh.js")
	dung("co nut tren trang", 'id="kk-mo-lai"' in ht)
	dung("nut mac dinh an", 'id="kk-mo-lai" style="display:none"' in ht)
	dung("co chu giai cho nguoi dung", "Mở lại ngày" in ht)
	dung("js goi dung cua", '"mo_lai"' in js or "'mo_lai'" in js)
	dung("chi hien khi da chot", "kk-mo-lai" in js and "daChot" in js)


@ca("mo lai: man hinh hoi lai khi chot som, dong y thi goi lai")
def _():
	js = _doc("vagabond/trang/kiem-banh.js")
	dung("doc co hoi lai", "hoi_lai" in js)
	dung("hoi lai bang cau may gui xuong", "r.cau_hoi" in js)
	dung("dong y thi goi lai kem co", "dong_y_som" in js)


@ca("mo lai: man kiem banh khong in thang loi may chu ra man")
def _():
	# Loi tho cua Frappe co the loi ten bang, ten truong, doi khi ca cau
	# lenh. Moi loi tren man nay deu phai di qua bo loc chung.
	js = _doc("vagabond/trang/kiem-banh.js")
	dung("co bo loc loi", "function loiKK" in js)
	dung("co bo loc chu", "function sachKK" in js)
	dung("khong in thang e.message", "bao(e.message" not in js)


# ------------------------------------------------------- viec 4: gan nguoi ban

@ca("gan nguoi ban: chua gan chi tinh khi nguoi lap la tai khoan may")
def _():
	dung("don Pancake do Administrator lap", nguoi_ban.chua_gan("", "Administrator"))
	dung("don web khach chua dang nhap", nguoi_ban.chua_gan(None, "Guest"))
	dung("khong co nguoi lap", nguoi_ban.chua_gan("", ""))
	# To cu do nguoi that lap truoc khi co o nay: man hinh van hien ten ho,
	# khong phai mot to thieu nguoi ban.
	dung("to cu nguoi that lap thi khong tinh la thieu",
		not nguoi_ban.chua_gan("", "ngan@vagabond.vn"))
	# Da gan roi thi thoi, du nguoi lap la may.
	dung("da gan tay roi thi het thieu",
		not nguoi_ban.chua_gan("bao@vagabond.vn", "Administrator"))
	dung("khoang trang khong tinh la da gan", nguoi_ban.chua_gan("   ", "Administrator"))


@ca("gan nguoi ban: quyen gan TACH RIENG khoi quyen xem hoa don")
def _():
	dung("quan ly cua hang gan duoc", nguoi_ban.duoc_gan(["Quản lý cửa hàng"]))
	dung("ke toan gan duoc", nguoi_ban.duoc_gan(["Kế toán"]))
	dung("giam doc gan duoc", nguoi_ban.duoc_gan(["Giám đốc"]))
	dung("quan tri gan duoc", nguoi_ban.duoc_gan(["System Manager", "Sales User"]))
	# Thu ngan XEM duoc to hoa don (co vai Sales User) nhung KHONG duoc tu
	# gan: o nay quyet dinh doanh so va hoa hong roi vao tay ai.
	dung("thu ngan khong tu gan duoc",
		not nguoi_ban.duoc_gan(["Sales User", "Bộ phận đặt hàng"]))
	dung("khong co vai nao thi khong gan duoc", not nguoi_ban.duoc_gan([]))
	dung("None cung khong gan duoc", not nguoi_ban.duoc_gan(None))


@ca("gan nguoi ban: mot cua duy nhat tra ca hai co cho man hinh")
def _():
	m = _doc("vagabond/ban_hang.py")
	i = m.find("def ai_lam_gi(")
	than = m[i:m.find("# ---------------------------------------------------------------- m-invoice")]
	dung("tra co chua gan", '"chua_gan"' in than)
	dung("tra co gan duoc", '"gan_duoc"' in than)
	dung("tra ma tai khoan de o chon dung san", '"nguoi_ban_ma"' in than)
	dung("doc quyen tu vai that", "frappe.get_roles()" in than)
	dung("dung chung phep thuan cua o nguoi ban", "_nb.chua_gan(" in than)
	# Cua nay CHI DOC. No duoc goi moi lan mo mot to hoa don.
	dung("khong ghi gi", "set_value" not in than)


@ca("gan nguoi ban: to chua gan hien dung chu 'chua gan', khong muon ten nguoi lap")
def _():
	js = _doc("vagabond/public/js/bep/10-bill-quay.js")
	i = js.find("async function hdAiLamGi(")
	than = js[i:js.find("function hdGanBind(")]
	dung("chua gan thi hien dung su that", "a.chua_gan ? 'chưa gán'" in than)
	dung("to mau canh bao", "#b45309" in than)
	dung("nut chi hien cho nguoi co quyen", "if (a.gan_duoc)" in than)
	dung("chua gan thi moi la Gan, con lai la Doi", "'Gán người bán' : 'Đổi người bán'" in than)


@ca("gan nguoi ban: nut goi dung cua cu, khong mo cua moi cho tien")
def _():
	js = _doc("vagabond/public/js/bep/10-bill-quay.js")
	i = js.find("function hdGanBind(")
	than = js[i:js.find("async function scrPosBill(")]
	dung("goi dung cua gan", "'vagabond.nguoi_ban.gan'" in than)
	dung("danh sach nguoi lay tu cua san co", "'vagabond.kpi.nguoi_dung'" in than)
	dung("cho phep de trong de go nguoi gan nham", "để trống, chưa gán" in than)
	dung("chon san nguoi dang giu o", "n.ma === hdGanMa" in than)
	# Khong duoc dung toi bat ky cua nao cham tien hay hoa don dien tu.
	for cam in ("pos_chot", "ghi_so", "hddt", "hoan_tien", "frappe.client.set_value"):
		dung("khong cham %s" % cam, cam not in than)


@ca("gan nguoi ban: nut duoc noi vao CA HAI man hoa don")
def _():
	# Man quay va man Sales cung dung mot khoi. Noi mot ben thi cung mot to
	# hoa don mo hai duong ra hai ket qua khac nhau, ma day la cho quy
	# trach nhiem.
	q = _doc("vagabond/public/js/bep/10-bill-quay.js")
	sl = _doc("vagabond/public/js/bep/08-doanh-so-sales.js")
	dung("man quay co noi", "hdGanBind();" in q)
	dung("man Sales co noi", "hdGanBind();" in sl)
	dung("chi dung MOT ham bind", q.count("function hdGanBind(") == 1)
	dung("man Sales khong tu dung khoi rieng", "function hdGanBind(" not in sl)


@ca("gan nguoi ban: cua ghi van giu nguyen hang rao cu")
def _():
	m = _doc("vagabond/nguoi_ban.py")
	than = m[m.find("def gan("):]
	dung("co kiem quyen", "_kiem_quyen()" in than)
	dung("tai khoan may khong phai nguoi ban", "Tài khoản máy không phải người bán" in than)
	dung("van cho go ra khi gan nham", "if nguoi and nguoi in MAY" in than)
	dung("co ghi vet", '"doctype": "Comment"' in than)
	dung("khong dung dau thoi gian cua to hoa don", "update_modified=False" in than)
	for cam in ("grand_total", "docstatus", "custom_hddt", "outstanding"):
		dung("khong cham %s" % cam, cam not in than)

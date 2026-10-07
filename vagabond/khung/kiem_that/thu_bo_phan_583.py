"""v583 #450: doi bo phan nguoi dung chay that tren site.

Tang khung dung lop Frappe gia. Ca nay chung minh tren site that: o
`custom_phong_ban` co tren User sau migrate, `dat_bo_phan` ghi thang o do
(khong luu ca tai lieu User nen bo vai giu nguyen), va ho so `chi_tiet` doc
lai dung bo phan moi kem danh sach chon duoc tu Department that.
"""

import frappe

from vagabond import nguoi_dung as nd
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO


def _nguoi():
	u = frappe.get_doc({"doctype": "User", "email": "kt583-bp-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Kiểm Bộ phận 583", "enabled": 1, "send_welcome_email": 0,
		"roles": [{"role": "Sales User"}]}).insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	return u


@ca("v583 site: doi bo phan mot nguoi ghi thang User, giu nguyen vai, ho so doc lai dung")
def _():
	# O `custom_phong_ban` la Custom Field tao tren Desk cua site that (Link
	# Department), khong nam trong ma nguon. Bench GitHub dung moi KHONG co o
	# do: ca kiem lan nhanh "thieu o" (chan ro rang, khong no co so du lieu).
	# Site that co o nen di nhanh day du; kiem them tren site sau khi deploy.
	u = _nguoi()
	if not nd._co_o_bo_phan():
		try:
			nd.dat_bo_phan(u.name, "Bếp Pastry - TV")
			chan = False
		except frappe.ValidationError as e:
			chan = "chưa có ô Bộ phận" in str(e)
		la("thieu o: chan ro rang", chan, True)
		la("thieu o: ho so khong moi doi", nd.chi_tiet(u.name)["bo_phan_chon_duoc"], [])
		return
	cac = nd._bo_phan_co_that()
	dung("site co it nhat hai bo phan chon duoc", len(cac) >= 2)
	vai_truoc = sorted(frappe.get_roles(u.name))
	dich = cac[0] if cac[0] != nd._bo_phan_cua(u.name) else cac[1]
	kq = nd.dat_bo_phan(u.name, dich)
	la("ghi dung o chinh", frappe.db.get_value("User", u.name, "custom_phong_ban"), dich)
	la("vai giu nguyen", sorted(frappe.get_roles(u.name)), vai_truoc)
	d = nd.chi_tiet(u.name)
	la("ho so doc lai", (d["bo_phan"], d["bo_phan_ten"]), (dich, nd.ten_ngan_bo_phan(dich)))
	dung("danh sach chon co bo phan vua dat", dich in [x["k"] for x in d["bo_phan_chon_duoc"]])
	dung("cau bao co ten bo phan", nd.ten_ngan_bo_phan(dich) in kq["loi_nhan"])
	try:
		nd.dat_bo_phan(u.name, "Không có bộ phận này - TV")
		chan = False
	except frappe.ValidationError:
		chan = True
	la("bo phan khong co that bi chan", chan, True)
	la("van giu bo phan cu sau lan bi chan", frappe.db.get_value("User", u.name, "custom_phong_ban"), dich)

"""Kiem thu THUAN cho tinh nang phien ban bao gia.

Khong can Frappe, khong can CSDL: mo phong dung ngu nghia LIKE va ORDER BY
cua MariaDB tren mot danh sach ten, roi chay lai dung cong thuc trong
autoname() va _tinh_khoa(). Muc dich la bat cho bo dem bi vong -vN lam hong
TRUOC khi no no tren du lieu that.

Chay: python3 kiem_phien_ban.py
"""


def _like(ten, mau):
	"""Mo phong LIKE cua SQL cho hai ky tu dai dien % va _."""
	import re

	bd = "^"
	for c in mau:
		if c == "%":
			bd += ".*"
		elif c == "_":
			bd += "."
		else:
			bd += re.escape(c)
	return re.match(bd + "$", ten) is not None


def dem_cu(ds, tien_to):
	"""Cach dem CU: chi loc theo tien to. Day la cho co loi."""
	hop = [x for x in ds if _like(x, tien_to + "%")]
	hop.sort(reverse=True)
	if not hop:
		return 1
	try:
		return int(hop[0].rsplit("-", 1)[1]) + 1
	except Exception:
		return 1


def dem_moi(ds, tien_to):
	"""Cach dem MOI: loai cac to -vN, xep theo do dai truoc roi den ten."""
	hop = [
		x for x in ds
		if _like(x, tien_to + "%") and not _like(x, tien_to + "%-v%")
	]
	hop.sort(key=lambda x: (len(x), x), reverse=True)
	if not hop:
		return 1
	try:
		return int(hop[0].rsplit("-", 1)[1]) + 1
	except Exception:
		return 1


def tinh_khoa(o):
	"""Ban sao THUAN cua bao_gia._tinh_khoa, giu dong bo bang tay."""
	TT_KHONG_SUA_DE = {
		"Đã gửi khách", "Khách duyệt", "Khách từ chối", "Hết hiệu lực",
		"Đã lên hợp đồng",
	}
	if o.get("la_mau"):
		return 0
	if o.get("thay_the_boi"):
		return 1
	tt = o.get("trang_thai") or "Nháp"
	if tt == "Đã lên hợp đồng":
		return 1
	if tt in TT_KHONG_SUA_DE:
		return 1
	return 0


CA = []


def ca(ten, chay, mong):
	CA.append((ten, chay, mong))


T = "VGB-PQ-2026-"

# --------------------------------------------------- bo dem khi chua co vong
ca("kho trong thi bat dau tu 1", lambda: dem_moi([], T), 1)
ca("ba to thuong", lambda: dem_moi([T + "0001", T + "0002", T + "0003"], T), 4)
ca("cach dem cu cung dung khi chua co vong nao",
   lambda: dem_cu([T + "0001", T + "0002", T + "0003"], T), 4)

# ------------------------------------------- bo dem khi da co vong thuong luong
GIUA = [T + "0007", T + "0007-v2", T + "0011"]
ca("vong nam o to GIUA day thi cach cu van dung",
   lambda: dem_cu(GIUA, T), 12)
ca("vong nam o to GIUA day thi cach moi cung dung",
   lambda: dem_moi(GIUA, T), 12)

# Day la ca lam vo he: vong dung tren to co so LON NHAT.
CUOI = [T + "0007", T + "0011", T + "0011-v2"]
ca("BAY: vong tren to lon nhat lam cach cu tut ve 1",
   lambda: dem_cu(CUOI, T), 1)
ca("cach moi van ra 12 du co vong tren to lon nhat",
   lambda: dem_moi(CUOI, T), 12)

ca("nhieu vong chong len nhau",
   lambda: dem_moi([T + "0011", T + "0011-v2", T + "0011-v3", T + "0011-v10"], T), 12)

ca("qua 4 chu so van dem tiep dung",
   lambda: dem_moi([T + "9999", T + "10000", T + "10000-v2"], T), 10001)

ca("day mau khong dinh gi toi day that",
   lambda: dem_moi([T + "0007", "MAU-BG-0003", T + "0007-v2"], T), 8)
ca("day mau tu dem rieng",
   lambda: dem_moi(["MAU-BG-0001", "MAU-BG-0002", T + "0007"], "MAU-BG-"), 3)

# --------------------------------------------------------------- khoa sua de
ca("to nhap thi sua duoc", lambda: tinh_khoa({"trang_thai": "Nháp"}), 0)
ca("to da gui khach thi khoa",
   lambda: tinh_khoa({"trang_thai": "Đã gửi khách"}), 1)
ca("to khach tu choi cung khoa",
   lambda: tinh_khoa({"trang_thai": "Khách từ chối"}), 1)
ca("to het hieu luc cung khoa",
   lambda: tinh_khoa({"trang_thai": "Hết hiệu lực"}), 1)
ca("ban da bi thay the thi khoa du dang Nhap",
   lambda: tinh_khoa({"trang_thai": "Nháp", "thay_the_boi": T + "0007-v2"}), 1)
ca("mau bao gia khong bao gio bi khoa",
   lambda: tinh_khoa({"trang_thai": "Đã gửi khách", "la_mau": 1}), 0)
ca("mau bao gia van khong khoa khi thieu trang thai",
   lambda: tinh_khoa({"la_mau": 1}), 0)

# ------------------------------------------------------- ten to cua mot vong
def ten_vong(goc, so):
	return "%s-v%d" % (goc, so)


ca("ten vong 2", lambda: ten_vong(T + "0007", 2), T + "0007-v2")
ca("ten vong 3 van dan vao GOC chu khong dan vao v2",
   lambda: ten_vong(T + "0007", 3), T + "0007-v3")


# ------------------------------------------------------------ xep cac vong
#
# Frappe 16 chan moi loi goi ham trong order_by, ke ca ifnull(), nen phai xep
# o Python. To lap truoc dot nay co phien_ban rong, phai doc thanh 1.
def xep_vong(ds):
	"""Ban sao THUAN cua phan xep trong lich_su()."""
	r = [dict(x) for x in ds]
	for x in r:
		x["phien_ban"] = int(x.get("phien_ban") or 1)
	r.sort(key=lambda x: (x["phien_ban"], str(x.get("creation") or "")))
	return [x["name"] + "/v" + str(x["phien_ban"]) for x in r]


ca("to cu co phien_ban rong van doc thanh vong 1",
   lambda: xep_vong([{"name": "A", "phien_ban": None, "creation": "1"}]),
   ["A/v1"])
ca("phien_ban bang 0 cung doc thanh vong 1",
   lambda: xep_vong([{"name": "A", "phien_ban": 0, "creation": "1"}]),
   ["A/v1"])
ca("xep dung khi goc rong con cac vong sau co so",
   lambda: xep_vong([
	   {"name": "A-v3", "phien_ban": 3, "creation": "3"},
	   {"name": "A", "phien_ban": None, "creation": "1"},
	   {"name": "A-v2", "phien_ban": 2, "creation": "2"}]),
   ["A/v1", "A-v2/v2", "A-v3/v3"])
ca("vong 10 dung sau vong 9 chu khong dung sau vong 1",
   lambda: xep_vong([
	   {"name": "A-v10", "phien_ban": 10, "creation": "b"},
	   {"name": "A-v9", "phien_ban": 9, "creation": "a"}]),
   ["A-v9/v9", "A-v10/v10"])


# -------------------------------------------------- muc chenh lech tung vong
def chenh_vong(tong):
	"""Ban sao THUAN cua phep tinh chenh trong lich_su()."""
	ra, truoc = [], None
	for t in tong:
		ra.append(0.0 if truoc is None else float(t) - float(truoc))
		truoc = t
	return ra


ca("vong dau khong co chenh", lambda: chenh_vong([900000]), [0.0])
ca("giam gia thi chenh am",
   lambda: chenh_vong([900000, 450000]), [0.0, -450000.0])
ca("tang roi giam van dung tung buoc",
   lambda: chenh_vong([100, 150, 120]), [0.0, 50.0, -30.0])


def chay():
	dat = hong = 0
	for ten, ham, mong in CA:
		try:
			duoc = ham()
		except Exception as e:  # noqa: BLE001
			duoc = "LỖI: %s" % e
		if duoc == mong:
			dat += 1
		else:
			hong += 1
			print("  HỎNG  %s\n         mong %r, được %r" % (ten, mong, duoc))
	print("\n%d ca đạt, %d ca hỏng, tổng %d ca." % (dat, hong, len(CA)))
	return hong


if __name__ == "__main__":
	print("Bộ kiểm thử phiên bản báo giá\n")
	raise SystemExit(1 if chay() else 0)

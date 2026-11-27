"""v693: tab In season cho Panettone và Bûche (anh Việt chốt 26/11/2026).

Chốt các luật ở vagabond/mua_vu_web.py (phần THUẦN) và phép tương ứng của trình
duyệt ở web_vue/kho/thuan.js bằng CÙNG một bộ số:
- gộp size theo "Nhóm trên web", dòng chưa điền nhóm đứng một mình;
- lịch nhận từng loại và giỏ trộn, ngày kết thúc mùa, ô cài đặt có áp thật
  (số 0 là giá trị người dùng chọn, để trống mới là mặc định);
- sốt chấm tối đa 2 hũ mỗi bánh Panettone;
- Panettone không có dĩa nĩa, không cờ lời chúc;
- máy chủ từ chối ngày sai lúc tạo đơn, sau phép tìm trùng nonce.
Dữ liệu trong ca là GIẢ. Không cần Frappe, không cần mạng.
"""
import datetime
import json
import subprocess
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[3]
D = datetime.date


def _w():
	from vagabond import mua_vu_web

	return mua_vu_web


def _mon(ma, gia, con=5, nhom="", nhan="", loai="", ten=None):
	return {"ma": ma, "ten": ten or ma, "gia": gia, "con": con, "het": 0 if con > 0 else 1, "anh": "/files/%s.jpg" % ma.lower(),
		"la_hop": 0, "ruot": "", "nhom": nhom, "nhan_size": nhan, "loai": loai}


def _node(ma):
	r = subprocess.run(["node", "--input-type=module", "-e", ma], cwd=GOC, capture_output=True, text=True, timeout=60)
	la("node chạy được: " + r.stderr[-600:], r.returncode, 0)
	return json.loads(r.stdout)


@ca("v693 gộp size: các mã cùng Nhóm trên web thành MỘT thẻ, size đắt đứng trước; dòng chưa điền nhóm đứng một mình như trước")
def _gop_size():
	w = _w()
	mon = [
		_mon("GIA-BU1", 1600000, loai="Bûche", ten="Bûche Giả"),
		_mon("GIA-P2", 320000, nhom="Classic  Panettone", nhan="Bánh Mini 250gr", loai="Panettone"),
		_mon("GIA-P1", 780000, nhom="classic panettone", nhan="Bánh lớn 680gr", loai="Panettone"),
		_mon("GIA-P3", 780000, con=0, nhom="Saigonettone", nhan="Bánh lớn 680gr", loai="panettone"),
		_mon("GIA-CU", 450000, ten="Hộp cũ"),
	]
	nhom = w.gom_nhom(mon)
	la("6 mã của ảnh Minh Vũ thành 3 thẻ: ở đây 5 dòng thành 4 thẻ", [g["ten"] for g in nhom], ["Bûche Giả", "Classic Panettone", "Saigonettone", "Hộp cũ"])
	g = nhom[1]
	la("thẻ gộp: khoá đường dẫn, loại, cờ gộp", (g["khoa"], g["loai"], g["gop"]), ("classic-panettone", "panettone", 1))
	la("size đắt trước, nhãn gọn khoảng trắng", [(s["ma"], s["nhan"]) for s in g["sizes"]], [("GIA-P1", "Bánh lớn 680gr"), ("GIA-P2", "Bánh Mini 250gr")])
	la("giá từ là giá thấp nhất", g["gia_tu"], 320000)
	la("dòng chưa điền nhóm: khoá là mã, một size, không gộp", (nhom[3]["khoa"], len(nhom[3]["sizes"]), nhom[3]["gop"], nhom[3]["loai"]), ("GIA-CU", 1, 0, ""))
	la("Bûche chưa điền nhóm vẫn mang loại", (nhom[0]["khoa"], nhom[0]["loai"]), ("GIA-BU1", "buche"))
	la("thẻ hết khi mọi size hết", [g["het"] for g in nhom], [0, 0, 1, 0])
	lon = w.gom_nhom([_mon("A", 1, nhom="X", loai="Bûche"), _mon("B", 2, nhom="X", loai="Panettone")])
	la("nhóm khai lẫn hai loại thì theo Panettone (luật chặt hơn)", lon[0]["loai"], "panettone")
	la("danh sách rỗng", w.gom_nhom([]), [])
	la("đường dẫn bỏ dấu", w.duong_dan_nhom("Bûche Rừng Thông"), "buche-rung-thong")


@ca("v693 lịch nhận: Panettone chỉ thứ 2, 4, 6 và trước 3 ngày; Bûche ngày nào cũng nhận, trước 2 ngày; đơn có cả hai theo lịch chặt hơn; không quá ngày kết thúc mùa")
def _lich():
	w = _w()
	luat = w.luat_mua({})
	la("mặc định anh Việt chốt", luat, {"panettone": {"truoc": 3, "thu": [2, 4, 6]}, "buche": {"truoc": 2, "thu": None}})
	hn = D(2026, 11, 26)  # thứ Năm
	het = D(2026, 12, 31)
	pan, bu, ca_hai = w.luat_don(["panettone"], luat), w.luat_don(["buche", ""], luat), w.luat_don(["buche", "panettone"], luat)
	la("đơn không có loại mang luật", w.luat_don(["", None], luat), None)
	la("đơn trộn: số ngày lớn nhất, thứ của Panettone", (ca_hai["truoc"], ca_hai["thu"]), (3, [2, 4, 6]))
	bang = [
		(pan, D(2026, 11, 27), "som"), (pan, D(2026, 11, 28), "som"), (pan, D(2026, 11, 29), "sai_thu"),
		(pan, D(2026, 11, 30), ""), (pan, D(2026, 12, 1), "sai_thu"), (pan, D(2026, 12, 2), ""), (pan, D(2026, 12, 4), ""),
		(pan, D(2026, 12, 30), ""), (pan, D(2026, 12, 31), "sai_thu"), (pan, D(2027, 1, 1), "qua_mua"),
		(bu, D(2026, 11, 27), "som"), (bu, D(2026, 11, 28), ""), (bu, D(2026, 11, 29), ""), (bu, D(2026, 12, 31), ""), (bu, D(2027, 1, 1), "qua_mua"),
		(ca_hai, D(2026, 11, 28), "som"), (ca_hai, D(2026, 11, 29), "sai_thu"), (ca_hai, D(2026, 11, 30), ""),
		(None, D(2026, 11, 26), ""), (pan, None, "khong_ngay"),
	]
	for ld, ngay, mong in bang:
		la("%s nhận %s" % ((ld or {}).get("loai"), ngay), w.ngay_hop_le(ngay, hn, ld, het), mong)
	la("cuối tháng 2: thứ Sáu 26/02 đặt thứ Hai 01/03 đủ 3 ngày", w.ngay_hop_le(D(2027, 3, 1), D(2027, 2, 26), pan, None), "")
	la("cuối tháng 2: thứ Bảy 27/02 đặt thứ Hai 01/03 mới 2 ngày", w.ngay_hop_le(D(2027, 3, 1), D(2027, 2, 27), pan, None), "som")
	cau = w.cau_luat(ca_hai, het)
	dung("câu cho đơn trộn nói rõ lịch chặt hơn, thứ, số ngày, ngày cuối mùa",
		all(x in cau for x in ("cả Panettone và Bûche", "thứ 2, thứ 4, thứ 6", "ít nhất 3 ngày", "31/12")))
	dung("câu không có gạch dài", chr(8212) not in cau and chr(8211) not in cau)


@ca("v693 ô cài đặt lịch của Mùa vụ có áp thật: số 0 là giá trị người dùng chọn, để trống mới về mặc định, ghi sai bị chặn lúc lưu")
def _cai_dat():
	w = _w()
	luat = w.luat_mua({"panettone_thu": "3, 5 CN", "panettone_truoc": "0", "buche_thu": "7,cn", "buche_truoc": "5"})
	la("ô đã điền thay mặc định", luat, {"panettone": {"truoc": 0, "thu": [3, 5, 8]}, "buche": {"truoc": 5, "thu": [7, 8]}})
	hn = D(2026, 11, 26)  # thứ Năm = 5
	la("đặt trước 0 ngày: nhận ngay hôm nay nếu đúng thứ", w.ngay_hop_le(hn, hn, w.luat_don(["panettone"], luat)), "")
	la("mặc định thì hôm nay là quá sớm", w.ngay_hop_le(hn, hn, w.luat_don(["panettone"], w.luat_mua({}))), "som")
	la("Bûche 5 ngày: ngày thứ tư bị chặn", w.ngay_hop_le(D(2026, 11, 29), hn, w.luat_don(["buche"], luat)), "som")
	la("Bûche chỉ thứ 7, CN: thứ Ba bị chặn", w.ngay_hop_le(D(2026, 12, 1), hn, w.luat_don(["buche"], luat)), "sai_thu")
	la("để trống (None và chuỗi rỗng) là mặc định", w.luat_mua({"panettone_thu": "", "panettone_truoc": None, "buche_truoc": "  "}), w.luat_mua({}))
	la("tất cả = ngày nào cũng nhận", w.luat_mua({"panettone_thu": "Tất cả"})["panettone"]["thu"], None)
	la("đủ 7 thứ = ngày nào cũng nhận", w.luat_mua({"panettone_thu": "2,3,4,5,6,7,CN"})["panettone"]["thu"], None)
	la("ô hợp lệ không có câu lỗi", w.loi_cai_dat({"panettone_thu": "2,4,6", "buche_truoc": "0"}), [])
	la("ghi sai thứ và số ngày: hai câu lỗi", len(w.loi_cai_dat({"panettone_thu": "thứ hai", "buche_truoc": "-1"})), 2)
	la("số ngày quá lớn bị chặn", len(w.loi_cai_dat({"panettone_truoc": "61"})), 1)
	# Trường mà mã đọc phải có thật trên doctype (bài học: ô cấu hình ghi áp mà không ai đọc).
	dt = json.loads((GOC / "vagabond/vagabond/doctype/vagabond_mua_vu/vagabond_mua_vu.json").read_text())
	ten = {f["fieldname"]: f for f in dt["fields"]}
	for k in ("panettone_thu", "panettone_truoc", "buche_thu", "buche_truoc"):
		dung("doctype Mùa vụ có ô " + k + " kiểu Data (phân biệt được trống với 0)", ten.get(k, {}).get("fieldtype") == "Data")
		dung(k + " nằm trong field_order", k in dt["field_order"])
	la("bảng sốt trỏ đúng doctype con", ten["sot_web"]["options"], "Vagabond Mua Vu Sot")
	sot = json.loads((GOC / "vagabond/vagabond/doctype/vagabond_mua_vu_sot/vagabond_mua_vu_sot.json").read_text())
	la("mã sốt là ô chọn có tìm (Link Item), không gõ tay", [(f["fieldtype"], f.get("options")) for f in sot["fields"] if f["fieldname"] == "ma_hang"], [("Link", "Item")])
	dong = {f["fieldname"]: f for f in json.loads((GOC / "vagabond/vagabond/doctype/vagabond_mua_vu_dong/vagabond_mua_vu_dong.json").read_text())["fields"]}
	la("ba ô của dòng", [dong[k]["fieldtype"] for k in ("nhom_web", "nhan_size", "loai_web")], ["Data", "Data", "Select"])
	la("lựa chọn Loại trên web khớp bảng đổi loại", sorted(x for x in dong["loai_web"]["options"].split("\n") if x in w.LOAI_THEO_O), sorted(w.LOAI_THEO_O))
	src = (GOC / "vagabond/mua_vu.py").read_text()
	dung("luu_o cho sửa ba ô từ app", all('"%s"' % k in src.split("SUA_DUOC = {")[1].split("}")[0] for k in ("nhom_web", "nhan_size", "loai_web")))


@ca("v693 sốt chấm: tối đa 2 hũ mỗi bánh Panettone, cộng cả đơn; sốt không kèm Panettone bị từ chối")
def _sot():
	w = _w()
	loai = {"P1": "panettone", "P2": "panettone", "B1": "buche"}
	sot = ["S1", "S2", "S3"]
	h = lambda **k: [{"variation_id": ma, "quantity": sl} for ma, sl in k.items()]  # noqa: E731
	la("1 bánh 2 hũ: nhận", w.kiem_sot(h(P1=1, S1=1, S2=1), sot, loai), None)
	la("1 bánh 3 hũ: vượt", w.kiem_sot(h(P1=1, S1=2, S3=1), sot, loai), (3, 2))
	la("3 bánh hai size, 6 hũ: nhận", w.kiem_sot(h(P1=2, P2=1, S1=6), sot, loai), None)
	la("3 bánh 7 hũ: vượt", w.kiem_sot(h(P1=2, P2=1, S1=4, S2=3), sot, loai), (7, 6))
	la("Bûche không được tính vào trần sốt", w.kiem_sot(h(B1=2, S1=1), sot, loai), (1, 0))
	la("đơn không có sốt", w.kiem_sot(h(P1=1, B1=1), sot, loai), None)
	la("mùa chưa khai mã sốt thì mã lạ không bị coi là sốt", w.kiem_sot(h(P1=1, S1=9), [], loai), None)
	kq = w.xet_don(h(P1=1, S1=3), D(2026, 11, 30), D(2026, 11, 26), {"loai_theo_ma": loai, "ma_sot": sot, "luat": w.luat_mua({}), "den_ngay": D(2026, 12, 31)})
	la("máy chủ từ chối đơn vượt sốt", (kq or {}).get("ly_do"), "sot_qua_so")
	dung("câu nói rõ trần của đơn", "tối đa 2 hũ" in kq["nhac"][0])


@ca("v693 máy chủ từ chối ngày nhận sai lịch của hàng mùa vụ lúc tạo đơn; đơn không có hàng mang luật không bị ảnh hưởng; phép kiểm nằm SAU phép tìm trùng nonce")
def _may_chu():
	w = _w()
	mua = {"loai_theo_ma": {"P1": "panettone", "B1": "buche"}, "ma_sot": [], "luat": w.luat_mua({}), "den_ngay": D(2026, 12, 31)}
	hn = D(2026, 11, 26)
	h = lambda *ma: [{"variation_id": m, "quantity": 1} for m in ma]  # noqa: E731
	la("Panettone nhận thứ Ba: từ chối", (w.xet_don(h("P1"), D(2026, 12, 1), hn, mua) or {}).get("ly_do"), "ngay_mua_vu")
	la("Panettone nhận thứ Hai đủ ngày: nhận", w.xet_don(h("P1"), D(2026, 11, 30), hn, mua), None)
	la("Bûche nhận ngày mai: từ chối", (w.xet_don(h("B1"), D(2026, 11, 27), hn, mua) or {}).get("ly_do"), "ngay_mua_vu")
	la("Bûche nhận sau 2 ngày: nhận", w.xet_don(h("B1"), D(2026, 11, 28), hn, mua), None)
	la("đơn trộn nhận thứ Bảy (hợp Bûche, sai Panettone): từ chối", (w.xet_don(h("B1", "P1"), D(2026, 11, 28), hn, mua) or {}).get("ly_do"), "ngay_mua_vu")
	la("bánh thường nhận ngày mai: không đụng", w.xet_don(h("BANHGIA"), D(2026, 11, 27), hn, mua), None)
	la("thiếu ngày nhận mà có Panettone: từ chối", (w.xet_don(h("P1"), None, hn, mua) or {}).get("ly_do"), "ngay_mua_vu")
	la("sau ngày kết thúc mùa: từ chối", (w.xet_don(h("B1"), D(2027, 1, 2), D(2026, 12, 30), mua) or {}).get("ly_do"), "ngay_mua_vu")
	la("không có mùa đang chạy", w.xet_don(h("P1"), D(2026, 12, 1), hn, None), None)
	la("ngày từ chuỗi ISO có giờ", w.ngay_tu_iso("2026-11-30T13:00:00"), D(2026, 11, 30))
	la("chuỗi hỏng", w.ngay_tu_iso("hom nay"), None)
	src = (GOC / "vagabond/don_hang.py").read_text()
	tao = src[src.index("def tao_don("):]
	dung("tao_don gọi mua_vu_web.kiem_don và trả đúng lý do", 'mua_vu_web.kiem_don(hang, ngay, mua_web, don.get("items"), MAX_SL)' in tao and 'tu_choi_mua["ly_do"]' in tao)
	dung("phép kiểm theo trạng thái máy chủ nằm sau phép tìm trùng nonce", tao.index("don_web.tim_trung(khoa)") < tao.index("mua_vu_web.kiem_don("))
	dung("kiểm trước khi đổi mã sang UUID Pancake", tao.index("mua_vu_web.kiem_don(") < tao.index("_uuid_tu_ma(c, k, h["))


@ca("v693 Panettone không có dĩa nĩa tặng và không cờ lời chúc: máy chủ và trình duyệt cùng một bộ số; Bûche theo luật hiện có")
def _dung_cu_va_co():
	w = _w()
	# don_hang nạp requests ở đầu tệp; CI tay không không có, nên nạp riêng hàm thuần như ca v692.
	from vagabond.khung.kiem_thu import thu_dia_nia_theo_co_692 as t692

	tran_dung_cu = t692._dh()["tran_dung_cu"]

	dong = [("P1", 0, 2), ("B1", 0, 1), ("BANH16", 16, 1)]
	la("máy chủ: Panettone bị loại khỏi trần", tran_dung_cu(dong, {"P1"}), 11)
	la("máy chủ: không khai mã loại trừ thì như v692", tran_dung_cu(dong), 13)
	la("máy chủ: giỏ chỉ có Panettone thì trần 0", tran_dung_cu([("P1", 0, 3)], {"P1"}), 0)
	chiec = [{"ma": "P1", "co": True, "loi_chuc": "Noel", "thiep": "nho", "loi_thiep": "a"}, {"ma": "B1", "co": True, "loi_chuc": "Joyeux", "thiep": "khong", "loi_thiep": ""}]
	ra = w.chot_chiec(chiec, {"P1": "panettone", "B1": "buche"})
	la("máy chủ bỏ cờ và lời chúc của Panettone, giữ thiệp", (ra[0]["co"], ra[0]["loi_chuc"], ra[0]["thiep"], ra[0]["loi_thiep"]), (False, "", "nho", "a"))
	la("Bûche giữ cờ", (ra[1]["co"], ra[1]["loi_chuc"]), (True, "Joyeux"))
	la("trang cũ không gửi chiếc", w.chot_chiec(None, {}), None)
	dung("bản gốc không bị sửa tại chỗ", chiec[0]["co"] is True)
	js = _node("""
import * as T from './vagabond/public/web_vue/kho/thuan.js';
const pan = {id: 'P1', cm: 0, qty: 2, mua: 1, loai: 'panettone', adds: []}, bu = {id: 'B1', cm: 0, qty: 1, mua: 1, loai: 'buche', adds: []};
const banh = {id: 'BANH16', cm: 16, qty: 1, nguon: 'order', adds: []}, cu = {id: 'CU', cm: 0, qty: 1, adds: []};
T.dongBoChiec(pan); T.dongBoChiec(bu); T.dongBoChiec(cu);
pan.chiec[0].co = true; pan.chiec[0].wish = 'x'; pan.chiec[0].thiep = 'ep_kim'; T.dongBoChiec(pan);
const luat = {panettone: {truoc: 3, thu: [2, 4, 6]}, buche: {truoc: 2, thu: null}};
const d = (y, m, n) => new Date(y, m - 1, n);
const hn = d(2026, 11, 26), lech = x => Math.round((x - hn) / 86400000);
const chan = (gio, x) => T.ngayMuaChan(lech(x), x, T.luatGioMua(gio, luat), '2026-12-31');
console.log(JSON.stringify({
  tran: [T.tranDcGio([pan, bu, banh]), T.tranDcGio([pan]), T.tranDcGio([bu])],
  chiecPan: pan.chiec.map(c => [c.co, c.wish, c.thiep]), chiecBu: bu.chiec.map(c => [c.co, c.thiep]), chiecCu: cu.chiec === undefined,
  hoi: [T.chiecCanHoi(pan, pan.chiec[0]), T.chiecCanHoi(pan, Object.assign({}, pan.chiec[0], {loi_thiep: 'a'})), T.chiecCanHoi(banh, {wish: '', thiep: 'nho', loi_thiep: ''})],
  ngay: [chan([pan], d(2026, 11, 28)), chan([pan], d(2026, 11, 29)), chan([pan], d(2026, 11, 30)), chan([pan], d(2026, 12, 1)), chan([pan], d(2027, 1, 1)),
    chan([bu], d(2026, 11, 27)), chan([bu], d(2026, 11, 28)), chan([bu, pan], d(2026, 11, 28)), chan([bu, pan], d(2026, 11, 30)), chan([banh, cu], d(2026, 11, 26))],
  thu: [T.thuVN(d(2026, 11, 29)), T.thuVN(d(2026, 11, 30))],
  sot: [T.tranSot(3), T.doiSot({}, 'S1', 1), T.doiSot({S1: 1}, 'S2', 1), T.doiSot({S1: 1, S2: 1}, 'S3', 1), T.doiSot({S1: 2}, 'S1', -1), T.doiSot({S1: 1}, 'S1', -1), T.doiSot({}, 'S1', -1)],
  gop: T.tenAddsGop([{n: 'Sốt A'}, {n: 'Sốt A'}, {n: 'Nón'}])
}));
""")
	la("trình duyệt: trần dĩa nĩa khớp máy chủ (11, 0), Bûche một cỡ theo luật hiện có (1 bộ)", js["tran"], [11, 0, 1])
	la("trình duyệt: Panettone ép về không cờ, không lời chúc, thiệp miễn phí", js["chiecPan"], [[False, "", "nho"], [False, "", "nho"]])
	la("trình duyệt: Bûche có cờ, chọn sẵn thiệp miễn phí", js["chiecBu"], [[True, "nho"]])
	dung("hàng mùa vụ thường (không loại) không có chiếc như trước", js["chiecCu"])
	la("bớt chiếc mùa vụ chỉ hỏi lại khi khách đã gõ lời; bánh thường như cũ", js["hoi"], [False, True, True])
	hn, het = D(2026, 11, 26), D(2026, 12, 31)
	luat = w.luat_mua({})
	py = [w.ngay_hop_le(n, hn, w.luat_don(l, luat), het) for l, n in (
		(["panettone"], D(2026, 11, 28)), (["panettone"], D(2026, 11, 29)), (["panettone"], D(2026, 11, 30)), (["panettone"], D(2026, 12, 1)), (["panettone"], D(2027, 1, 1)),
		(["buche"], D(2026, 11, 27)), (["buche"], D(2026, 11, 28)), (["buche", "panettone"], D(2026, 11, 28)), (["buche", "panettone"], D(2026, 11, 30)), ([""], D(2026, 11, 26)))]
	la("trình duyệt và máy chủ cùng kết quả trên 10 ngày thử", js["ngay"], py)
	la("thứ kiểu Việt hai phía", js["thu"], [w.thu_cua_ngay(D(2026, 11, 29)), w.thu_cua_ngay(D(2026, 11, 30))])
	la("trần sốt hai phía", js["sot"][0], w.tran_sot(3))
	la("bảng chọn sốt: không quá 2 hũ, không âm", js["sot"][1:], [{"S1": 1}, {"S1": 1, "S2": 1}, {"S1": 1, "S2": 1}, {"S1": 1}, {}, {}])
	la("tên món mua thêm gộp món trùng", js["gop"], "Sốt A × 2, Nón")
	la("hằng số trần sốt hai phía", _node("import * as T from './vagabond/public/web_vue/kho/thuan.js'; console.log(T.SOT_MOI_BANH)"), w.SOT_MOI_BANH)


@ca("v693 một nguồn: tab In season và phép kiểm lúc tạo đơn chọn cùng một mùa; luật lịch không còn chỗ nào tự tính")
def _mot_nguon():
	src = (GOC / "vagabond/mua_vu.py").read_text()
	la("chỉ mua_cho_web chọn mùa cho web", src.count('"den_ngay") or "9999-12-31"'), 1)
	dung("hang_theo_mua dùng mua_cho_web", "doc = mua_cho_web()" in src[src.index("def hang_theo_mua("):])
	web = (GOC / "vagabond/mua_vu_web.py").read_text()
	dung("doc_mua_web dùng mua_cho_web", "mua_vu.mua_cho_web()" in web)
	kho = (GOC / "vagabond/public/web_vue/banh/kho-banh.js").read_text()
	dung("trình duyệt không gắn cứng thứ 2, 4, 6 hay số ngày", "[2, 4, 6]" not in kho and "truoc: 3" not in kho)
	dung("lịch, lúc bấm ngày, lúc gửi đơn đều qua muaChan", kho.count("muaChan(") >= 6)
	dl = (GOC / "vagabond/public/web_vue/banh/du-lieu.js").read_text()
	dung("chữ anh Việt chốt cho hộp", "Hộp màu nâu champagne" in dl and "Hộp màu xanh turquoise" in dl)


@ca("v693 Codex #625: loại hiệu lực của từng mã là MỘT phép cho thẻ trên web và phép kiểm lúc tạo đơn; nhóm chỉ điền loại ở một size thì size kia vẫn theo loại của nhóm")
def _loai_hieu_luc():
	w = _w()
	dong = [{"ma": "P1", "nhom": "Nhóm X", "loai": "Panettone"}, {"ma": "P2", "nhom": "nhóm  x", "loai": ""},
		{"ma": "B1", "nhom": "", "loai": "Bûche"}, {"ma": "L1", "nhom": "Nhóm Y", "loai": "Bûche"}, {"ma": "L2", "nhom": "Nhóm Y", "loai": "Panettone"},
		{"ma": "K1", "nhom": "", "loai": "Khác"}, {"ma": "K2", "nhom": "Nhóm Z", "loai": ""}]
	loai = w.loai_hieu_luc(dong)
	la("size chưa điền loại theo loại của nhóm; nhóm lẫn hai loại theo Panettone; Khác và trống không có khoá", loai,
		{"P1": "panettone", "P2": "panettone", "B1": "buche", "L1": "panettone", "L2": "panettone"})
	mon = [dict(_mon(d["ma"], 100, nhom=d["nhom"]), loai=loai.get(d["ma"], "")) for d in dong]
	la("thẻ trên web mang đúng loại đó", {g["ten"]: g["loai"] for g in w.gom_nhom(mon)},
		{"Nhóm X": "panettone", "B1": "buche", "Nhóm Y": "panettone", "K1": "", "Nhóm Z": ""})
	mua = {"loai_theo_ma": loai, "ma_sot": ["S1"], "luat": w.luat_mua({}), "den_ngay": D(2026, 12, 31)}
	hn = D(2026, 11, 26)
	h = lambda **k: [{"variation_id": ma, "quantity": sl} for ma, sl in k.items()]  # noqa: E731
	la("size chưa điền loại kèm 1 hũ sốt, ngày đúng lịch: nhận (trước đây bị từ chối với trần 0 hũ)", w.xet_don(h(P2=1, S1=1), D(2026, 11, 30), hn, mua), None)
	la("size chưa điền loại vẫn theo lịch Panettone", (w.xet_don(h(P2=1), D(2026, 12, 1), hn, mua) or {}).get("ly_do"), "ngay_mua_vu")
	src = (GOC / "vagabond/mua_vu.py").read_text() + (GOC / "vagabond/mua_vu_web.py").read_text()
	web, mvs = (GOC / "vagabond/mua_vu_web.py").read_text(), (GOC / "vagabond/mua_vu.py").read_text()
	la("mua_vu_web chỉ đọc ô loai_web ở loai_cua_mua", web.count('get("loai_web")'), 1)
	dung("hang_theo_mua không tự đọc ô loai_web", "loai_web" not in mvs[mvs.index("def hang_theo_mua("):])
	dung("tab In season, lúc tạo đơn, thẻ nội dung đều qua loai_cua_mua", src.count("loai_cua_mua(doc)") >= 3)


@ca("v693 Codex #625: thẻ nội dung và tab In season chọn tên bằng MỘT phép; tên món đổi sau khi thẻ đã tạo thì vẫn tìm ra thẻ theo mã hàng")
def _the_noi_dung():
	w = _w()
	la("có nhóm thì theo nhóm", w.ten_the(" Nhóm  X ", "Tên hồ sơ", "Tên Pancake", "M1"), "Nhóm X")
	la("không nhóm: tên hồ sơ món trước tên trên dòng", w.ten_the("", "Tên hồ sơ", "Tên Pancake", "M1"), "Tên hồ sơ")
	la("thiếu cả hai thì mã", w.ten_the(None, None, "", "M1"), "M1")
	la("thẻ gom_nhom dùng đúng phép đó", w.gom_nhom([_mon("M1", 1, ten="Tên hồ sơ")])[0]["ten"], w.ten_the("", "Tên hồ sơ", None, "M1"))
	sg = {"tên pancake": {"khoa": "tên pancake", "ma_hang": "M1\nM2", "mo_ta": "a"}, "bánh khác": {"khoa": "bánh khác", "ma_hang": "Z9", "mo_ta": "b"}}
	la("tìm theo khoá tên", w.tim_the(sg, "Bánh  Khác", ["KHONG"])["mo_ta"], "b")
	la("tên lệch thì tìm theo mã hàng gắn trên thẻ", w.tim_the(sg, "Tên hồ sơ", ["M2"])["mo_ta"], "a")
	la("mã là đoạn con của mã khác không khớp nhầm", w.tim_the(sg, "x", ["M"]), None)
	la("không có thẻ", w.tim_the({}, "x", ["M1"]), None)
	# Khoá tên của nhóm phải trùng khoá thẻ Bánh của trình biên tập (hai tệp, một cách tính).
	from vagabond.khung.kiem_thu import thu_dia_nia_theo_co_692 as t692

	g = {"unicodedata": __import__("unicodedata")}
	t692.nap("banh_web.py", "khoa_banh", g)
	for ten in ("Classic  Panettone", "BÛCHE Rừng Thông", "  Saigonettone ", "Bûche de Noël"):
		la("khoá tên trùng banh_web.khoa_banh: " + ten, w.khoa_nhom(ten), g["khoa_banh"](ten))
	web = (GOC / "vagabond/mua_vu_web.py").read_text()
	dung("đọc nội dung và tạo thẻ đều qua tim_the, ten_the", web.count("tim_the(") >= 3 and web.count("ten_the(") >= 3)


@ca("v693 Codex #625 vòng 2: bước làm sạch cắt mỗi mã về 20 nên máy chủ từ chối rõ đơn mùa vụ gửi quá 20 một mã (bánh hoặc sốt), không tạo đơn đã bị cắt bớt; trần hai phía là một con số")
def _tran_moi_ma():
	w = _w()
	loai = {"P1": "panettone", "B1": "buche"}
	tho = lambda **k: [{"variation_id": ma, "quantity": sl} for ma, sl in k.items()]  # noqa: E731
	la("11 bánh, 22 hũ một loại: sốt vượt", w.vuot_sl(tho(P1=11, S1=22), ["P1", "B1", "S1"], 20), ["S1"])
	la("dòng trùng mã cộng lại rồi mới so", w.vuot_sl(tho(P1=12) + tho(P1=9), ["P1"], 20), ["P1"])
	la("đúng 20 thì nhận", w.vuot_sl(tho(P1=20, S1=20), ["P1", "S1"], 20), [])
	la("mã không thuộc mùa (bánh thường, dĩa nĩa) không xét ở đây", w.vuot_sl(tho(BANHGIA=25), ["P1"], 20), [])
	la("dữ liệu rác không làm nổ", w.vuot_sl([None, {"variation_id": "P1", "quantity": "x"}, 7, {"quantity": 30}], ["P1"], 20), [])
	la("items không phải danh sách", w.vuot_sl("x", ["P1"], 20), [])
	mua = {"loai_theo_ma": loai, "ma_sot": ["S1"], "luat": w.luat_mua({}), "den_ngay": D(2026, 12, 31)}
	# Sau bước làm sạch đơn còn 11 bánh 20 hũ (hợp trần 22 hũ) và ngày đúng lịch: trước đây lọt.
	sach = tho(P1=11, S1=20)
	kq = w.xet_don(sach, D(2026, 11, 30), D(2026, 11, 26), mua, tho(P1=11, S1=22), 20)
	la("máy chủ từ chối, nêu lý do riêng", (kq or {}).get("ly_do"), "sl_mua_qua_tran")
	dung("câu nói rõ trần 20", "tối đa 20" in kq["nhac"][0])
	la("đơn trong trần vẫn nhận", w.xet_don(tho(P1=10, S1=20), D(2026, 11, 30), D(2026, 11, 26), mua, tho(P1=10, S1=20), 20), None)
	from vagabond.khung.kiem_thu import thu_dia_nia_theo_co_692 as t692

	la("trần của trình duyệt bằng MAX_SL của máy chủ", _node("import * as T from './vagabond/public/web_vue/kho/thuan.js'; console.log(T.SL_MA_TOI_DA)"), t692._hang_so("MAX_SL"))
	la("trình duyệt tính trên danh sách món sẽ gửi (sốt nhân số bánh)", _node("""
import * as T from './vagabond/public/web_vue/kho/thuan.js';
const sot = {id: 'S1', n: 's', p: 1, sot: 1};
console.log(JSON.stringify([T.maVuotSl([{id: 'P1', cm: 0, qty: 11, mua: 1, loai: 'panettone', adds: [sot, sot]}]), T.maVuotSl([{id: 'P1', cm: 0, qty: 10, mua: 1, loai: 'panettone', adds: [sot, sot]}]),
  T.maVuotSl([{id: 'P1', cm: 0, qty: 12, adds: []}, {id: 'P1', cm: 0, qty: 9, adds: [sot]}])]));
"""), [["S1"], [], ["P1"]])


@ca("v696 Codex #626 P1: nội dung thẻ và việc tạo thẻ chỉ đọc thẻ Bánh của đúng các nhóm đang xét, không đọc cả bảng (ca bench chạy trên site thật không chạm bản ghi thật)")
def _chi_doc_the_cua_nhom():
	import sys
	import types

	w = _w()
	BANG = [
		{"name": "that a", "khoa": "that a", "ten": "Thật A", "mua_vu": 0, "ma_hang": "MA-THAT-1", "mo_ta": "x", "tang": "", "di_ung": "", "bao_quan": "", "anh": "[]"},
		{"name": "that b", "khoa": "that b", "ten": "Thật B", "mua_vu": 1, "ma_hang": "MA-THAT-2", "mo_ta": "y", "tang": "", "di_ung": "", "bao_quan": "", "anh": "[]"},
		{"name": "nhom gia", "khoa": "nhom gia", "ten": "Nhóm Giả", "mua_vu": 1, "ma_hang": "GIA-1\nGIA-2", "mo_ta": "Mô tả giả", "tang": "A\nB", "di_ung": "", "bao_quan": "", "anh": "[]"},
		{"name": "ten cu", "khoa": "ten cu", "ten": "Tên cũ", "mua_vu": 1, "ma_hang": "GIA-9", "mo_ta": "Theo mã", "tang": "", "di_ung": "", "bao_quan": "", "anh": "[]"},
		{"name": "banh thuong", "khoa": "banh thuong", "ten": "Bánh thường", "mua_vu": 0, "ma_hang": "GIA-8", "mo_ta": "", "tang": "", "di_ung": "", "bao_quan": "", "anh": "[]"}]
	goi, doc_ra = [], []

	def khop(x, loc):
		for k, v in (loc or {}).items():
			if isinstance(v, list) and v[0] == "in":
				if x.get(k) not in v[1]:
					return False
			elif x.get(k) != v:
				return False
		return True

	def get_all(dt, filters=None, or_filters=None, fields=None, **_k):
		goi.append((dt, filters, or_filters))
		ra = [x for x in BANG if khop(x, filters)]
		if or_filters:
			ra = [x for x in ra if any(f[3].strip("%").replace("\\_", "_") in x[f[1]] for f in or_filters)]
		ra = [{c: x.get(c) for c in (fields or ["name"])} for x in ra]
		doc_ra.extend(ra)
		return ra

	fr = types.ModuleType("frappe")
	fr.get_all = get_all
	fr.log_error = lambda *a, **k: None
	bw = types.ModuleType("vagabond.banh_web")
	bw.DT = "Vagabond Banh Web"
	bw.dang_dung = lambda: True
	bw.khoa_banh = w.khoa_nhom
	bw.so_ghi = lambda: (_ for _ in ()).throw(AssertionError("không được đọc cả bảng"))
	bw.tach_dong = lambda v, n=None: [x for x in str(v or "").split("\n") if x.strip()][:n]
	bw.doc_anh = lambda v: []
	bw.doc_kem = lambda v: None  # v697: ô kem_theo, không đọc ở ca này
	bw.SO_TANG_TOI_DA, bw.SO_ANH_TOI_DA = 8, 5
	import vagabond

	cu = {k: sys.modules.get(k) for k in ("frappe", "vagabond.banh_web")}
	cu_attr = getattr(vagabond, "banh_web", None)
	sys.modules["frappe"], sys.modules["vagabond.banh_web"] = fr, bw
	vagabond.banh_web = bw
	try:
		nhom = [{"ten": "Nhóm Giả", "sizes": [{"ma": "GIA-1"}, {"ma": "GIA-2"}]}, {"ten": "Tên mới", "sizes": [{"ma": "GIA-9"}]}]
		w.noi_dung_nhom(nhom)
		la("nội dung theo khoá tên", (nhom[0].get("mo_ta"), nhom[0].get("tang")), ("Mô tả giả", ["A", "B"]))
		la("tên đổi thì vẫn tìm ra theo mã", nhom[1].get("mo_ta"), "Theo mã")
		dung("mọi lần đọc bảng thẻ đều có bộ lọc", all(f or of for dt, f, of in goi if dt == bw.DT))
		la("không dòng thật nào bị đọc", sorted({x["name"] for x in doc_ra} - {"nhom gia", "ten cu"}), [])
		goi.clear(); doc_ra.clear()
		ra = w.the_cua([], ["GIA-9"], chi_mua_vu=True)
		la("tìm thẻ mùa vụ theo mã chỉ trả đúng thẻ có mã đó", sorted(ra), ["ten cu"])
		la("tìm thẻ mùa vụ bỏ qua thẻ bánh thường cùng mã", sorted(w.the_cua([], ["GIA-8"], chi_mua_vu=True)), [])
		la("không giới hạn mùa vụ thì thấy thẻ bánh thường", sorted(w.the_cua([], ["GIA-8"])), ["banh thuong"])
		n = len(goi)
		la("không truyền khoá, không truyền mã thì không đọc gì", (w.the_cua([], []), len(goi) - n), ({}, 0))
	finally:
		for k, v in cu.items():
			if v is None:
				sys.modules.pop(k, None)
			else:
				sys.modules[k] = v
		if cu_attr is None:
			delattr(vagabond, "banh_web") if hasattr(vagabond, "banh_web") else None
		else:
			vagabond.banh_web = cu_attr
	web = (GOC / "vagabond/mua_vu_web.py").read_text()
	dung("mua_vu_web không còn gọi so_ghi", "so_ghi(" not in web)
	dung("tạo thẻ không còn đọc mọi thẻ mùa vụ", 'filters={"mua_vu": 1}, fields=["name", "ma_hang"]' not in web)

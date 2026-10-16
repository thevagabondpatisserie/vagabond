"""v598 (16/10/2026): đơn web bị Pancake từ chối vì THẺ.

Minh Vũ báo đặt đơn không được. Error Log site thật: 3 đơn DW-2610-04905..07
cùng HTTP 422 "[tags]: Nhiều hơn 1 thẻ trong nhóm thẻ: Khách yêu cầu". Trên
Pancake, thẻ "Xuất hoá đơn" (74) và "Bánh tặng" (68) vừa được xếp chung nhóm
"Khách yêu cầu" chỉ cho một thẻ; đơn chọn cả hai bị trả về, khách thấy
"Chưa gửi được đơn".

Sửa: Pancake trả lời rõ là chặn THẺ (chưa tạo đơn) thì gửi lại MỘT lần chỉ
với thẻ khung giờ, ghi các thẻ còn lại thành chữ vào ghi chú cho Sales. Mọi
lỗi khác vẫn KHÔNG gửi lại (luật cũ #367: không có chống trùng phía Pancake).

Ca kiểm gọi tao_don THẬT trong môi trường giả của thu_don_web_367, chỉ thay
Pancake bằng chuỗi phản hồi định sẵn.
"""
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_don_web_367 import _Tra, _don, _moi_truong_tao_don

LOI_THE = {"message": "[tags]: Nhiều hơn 1 thẻ trong nhóm thẻ: Khách yêu cầu", "success": False}


def _chuoi(*tra):
	"""Pancake giả trả lần lượt từng phản hồi; ghi lại thân từng lần gửi."""
	ds = list(tra)
	gui = []

	def pancake(vet):
		gui.append(dict(vet.body))
		x = ds.pop(0)
		if isinstance(x, Exception):
			raise x
		return x
	return pancake, gui


@ca("v598 Pancake chặn thẻ: gửi lại một lần chỉ thẻ khung giờ, thẻ còn lại thành chữ trong ghi chú, khách có biên nhận")
def _():
	pancake, gui = _chuoi(_Tra(422, LOI_THE), _Tra(200, {"data": {"id": "91600"}}))
	vet, tao_don = _moi_truong_tao_don(pancake)
	r = tao_don(_don(tags=[92, 74, 68], note_print="Bếp: ít ngọt", note="Ghi chú khách"))
	la("khách nhận được biên nhận", r.get("ok"), 1)
	la("gửi đúng hai lần", vet.su.count("post"), 2)
	la("lần đầu đủ ba thẻ", gui[0]["tags"], [92, 74, 68])
	la("lần sau chỉ thẻ khung giờ", gui[1]["tags"], [92])
	for o in ("note_print", "note"):
		dung(o + " giữ chữ cũ", gui[1][o].startswith(gui[0][o]))
		dung(o + " ghi thẻ Sales cần gắn tay", "Xuất hoá đơn, Bánh tặng" in gui[1][o])
	dung("có Error Log chỉ ra cấu hình nhóm thẻ", any("chan the" in x for x in vet.log))
	la("đơn được nhận", [x for x in vet.su if str(x).startswith("cap_nhat:")], ["cap_nhat:da_nhan"])
	dung("CAPI GuiDon vẫn gửi", "capi" in vet.su)


@ca("v598 lỗi khác thẻ, lỗi mạng, hoặc chỉ một thẻ: KHÔNG gửi lại (giữ luật chống hai đơn #367)")
def _():
	for ten, tra, tags in (
		("422 không phải thẻ", [_Tra(422, {"message": "[items]: sai mã", "success": False})], [92, 74]),
		("500 có chữ tags", [_Tra(500, LOI_THE)], [92, 74]),
		("mất mạng", [OSError("timeout")], [92, 74]),
		("chỉ một thẻ", [_Tra(422, LOI_THE)], [92]),
	):
		pancake, gui = _chuoi(*tra)
		vet, tao_don = _moi_truong_tao_don(pancake)
		tao_don(_don(tags=tags))
		la(ten + ": gửi một lần", vet.su.count("post"), 1)


@ca("v598 gửi lại vẫn bị từ chối: dừng sau lần thứ hai, khách thấy chưa gửi được")
def _():
	pancake, gui = _chuoi(_Tra(422, LOI_THE), _Tra(422, LOI_THE))
	vet, tao_don = _moi_truong_tao_don(pancake)
	r = tao_don(_don(tags=[92, 74, 68]))
	la("đúng hai lần", vet.su.count("post"), 2)
	la("báo khách chưa gửi được", (r.get("ok"), r.get("ly_do")), (0, "pancake_tu_choi"))
	dung("không GuiDon", "capi" not in vet.su)


@ca("v598 hàm thuần: nhận đúng lỗi thẻ, tên thẻ có dấu, thẻ lạ ghi số")
def _():
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap
	g = {}
	from vagabond.khung.kiem_thu.thu_don_web_367 import _hang_so
	g["TEN_THE"] = _hang_so("don_hang.py", "TEN_THE")
	la_loi = nap("don_hang.py", "la_loi_the", g)
	bot = nap("don_hang.py", "bot_the", g)
	la("422 [tags]", la_loi(422, LOI_THE), True)
	la("400 [tags]", la_loi(400, {"message": " [Tags]: x"}), True)
	la("422 khác", la_loi(422, {"message": "[items]: x"}), False)
	la("không phải dict", la_loi(422, None), False)
	la("200", la_loi(200, LOI_THE), False)
	la("bỏ thẻ", bot([92, 74, 68]), ([92], "Thẻ Pancake chưa gắn được, Sales gắn tay: Xuất hoá đơn, Bánh tặng."))
	la("thẻ lạ", bot([92, 5]), ([92], "Thẻ Pancake chưa gắn được, Sales gắn tay: thẻ số 5."))
	la("một thẻ", bot([92]), ([92], ""))

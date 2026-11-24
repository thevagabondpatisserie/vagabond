# -*- coding: utf-8 -*-
"""v692 (giám đốc chốt 24/11/2026, Sales báo khách đặt size nhỏ xin quá nhiều dĩa,
nĩa): trần dĩa, nĩa tặng theo cỡ bánh. Bánh 12cm, 16cm được 10 bộ; 18cm, 20cm được
15 bộ, nhân số chiếc; món không có cỡ 1 bộ mỗi món; phụ kiện (BAPK) không tính; cả
đơn không quá MAX_SL. Trang khách khoá nút Thêm 1 và hiện "Đã chọn tối đa số lượng
cho phép" (ca DOM F06 trong cong_cu/kiem_web_vue_dom.cjs); máy chủ chốt lại số khi
tạo đơn. Hai phía chạy cùng bộ số ở đây."""

import json
import subprocess
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_dia_nia_678 import _hang_so
from vagabond.khung.kiem_thu.thu_su_co_290 import nap

GOC = Path(__file__).resolve().parents[3]

# (mô tả, [(mã, cỡ cm, số lượng)], trần mong đợi)
BO_SO = [
	("một bánh 12cm", [("BAWC00139", 12, 1)], 10),
	("một bánh 16cm", [("BAWC00140", 16, 1)], 10),
	("một bánh 18cm", [("BAWC00141", 18, 1)], 15),
	("một bánh 20cm", [("BAWC00138", 20, 1)], 15),
	("hai bánh 12cm", [("BAWC00139", 12, 2)], 20),
	("12cm và 18cm: cộng rồi kẹp trần chung", [("BAWC00139", 12, 1), ("BAWC00141", 18, 1)], 20),
	("bánh một cỡ, đồ uống: 1 bộ mỗi món", [("BAWC00900", 0, 2), ("NU00001", 0, 1)], 3),
	("phụ kiện, thiệp, nến không tính", [("BAWC00139", 12, 1), ("BAPK00002", 0, 3), ("BAPK00015", 0, 1)], 10),
	("chỉ phụ kiện", [("BAPK00002", 0, 1)], 0),
	("giỏ rỗng", [], 0),
	("số lượng lạ", [("BAWC00139", "x", 1), ("BAWC00141", 18, "2")], 20),
]


def _dh():
	g = dict(MAX_SL=_hang_so("MAX_SL"), DC_CO_NHO=_hang_so("DC_CO_NHO"), DC_BO_NHO=_hang_so("DC_BO_NHO"),
		DC_BO_LON=_hang_so("DC_BO_LON"))
	nap("don_hang.py", "tran_dung_cu", g)
	nap("don_hang.py", "_lam_sach_hang", g)
	nap("don_hang.py", "_chot_dung_cu", g)
	return g


@ca("v692 trần dĩa, nĩa theo cỡ bánh (máy chủ): đúng bộ số giám đốc chốt")
def _may_chu():
	g = _dh()
	la("hằng số", (g["DC_CO_NHO"], g["DC_BO_NHO"], g["DC_BO_LON"]), (16, 10, 15))
	for mo, dong, mong in BO_SO:
		la(mo, g["tran_dung_cu"](dong), mong)


@ca("v692 trần dĩa, nĩa: trang khách (thuan.js chạy thật bằng node) ra đúng cùng bộ số với máy chủ")
def _hai_phia():
	ma = """import * as T from './vagabond/public/web_vue/kho/thuan.js';
const bo = JSON.parse(process.argv[1]);
console.log(JSON.stringify(bo.map(([mo, dong]) => T.tranDcGio(dong.map(([id, cm, qty]) => ({id, cm, qty}))))));
console.log(JSON.stringify([T.DC_CO_NHO, T.DC_BO_NHO, T.DC_BO_LON, T.DC_TOI_DA]));
console.log(JSON.stringify([T.chuanDcDon({dia: 14, nia: 3}, 10), T.chuanDcDon({dia: 99, nia: -2}), T.chuanDcDon({dia: 5}, 0)]));
console.log(JSON.stringify(T.hangGui([{id: 'BAWC00139', cm: 12, qty: 1, adds: []}], {dia: 18, nia: 12})));
"""
	r = subprocess.run(["node", "--input-type=module", "-e", ma, json.dumps([[m, d] for m, d, _ in BO_SO])],
		cwd=GOC, capture_output=True, text=True, timeout=60)
	la("node chạy được: " + r.stderr[-800:], r.returncode, 0)
	dong = r.stdout.strip().splitlines()
	la("cùng trần từng giỏ", json.loads(dong[0]), [mong for _, _, mong in BO_SO])
	la("cùng hằng số", json.loads(dong[1]), [_hang_so("DC_CO_NHO"), _hang_so("DC_BO_NHO"), _hang_so("DC_BO_LON"), _hang_so("MAX_SL")])
	la("kẹp theo trần, trần mặc định là MAX_SL, trần 0 thì 0", json.loads(dong[2]),
		[{"dia": 10, "nia": 3}, {"dia": 20, "nia": 0}, {"dia": 0, "nia": 0}])
	la("gửi máy chủ đã kẹp theo trần bánh 12cm", json.loads(dong[3]),
		[{"variation_id": "BAWC00139", "quantity": 1}, {"variation_id": "BAPK00020", "quantity": 10},
			{"variation_id": "BAPK00018", "quantity": 10}])


@ca("v692 máy chủ chốt dĩa, nĩa khi tạo đơn: trang cũ hay gọi thẳng cửa gửi 20 cho bánh 12cm vẫn chỉ còn 10")
def _chot():
	g = _dh()
	ten = {"BAWC00139": "Bánh Candle, size 12cm", "BAWC00141": "Bánh Candle, size 18cm", "BAPK00002": "Thiệp ép kim"}
	hang = [{"variation_id": "BAWC00139", "quantity": 1}, {"variation_id": "BAPK00020", "quantity": 20},
		{"variation_id": "BAPK00018", "quantity": 4}, {"variation_id": "BAPK00002", "quantity": 1}]
	la("kẹp dĩa về 10, giữ nĩa, giữ thứ tự", g["_chot_dung_cu"](hang, ten),
		[{"variation_id": "BAWC00139", "quantity": 1}, {"variation_id": "BAPK00020", "quantity": 10},
			{"variation_id": "BAPK00018", "quantity": 4}, {"variation_id": "BAPK00002", "quantity": 1}])
	la("không đổi giỏ gốc", hang[1]["quantity"], 20)
	h18 = [{"variation_id": "BAWC00141", "quantity": 1}, {"variation_id": "BAPK00020", "quantity": 15}]
	la("bánh 18cm giữ 15", g["_chot_dung_cu"](h18, ten), h18)
	h0 = [{"variation_id": "BAPK00002", "quantity": 1}, {"variation_id": "BAPK00020", "quantity": 3}]
	la("không có bánh: bỏ dòng dĩa", g["_chot_dung_cu"](h0, ten), [{"variation_id": "BAPK00002", "quantity": 1}])
	khong_dc = [{"variation_id": "BAWC00139", "quantity": 1}]
	la("không có dĩa, nĩa: không đọc hồ sơ món", g["_chot_dung_cu"](khong_dc, None), khong_dc)
	src = (GOC / "vagabond/don_hang.py").read_text(encoding="utf-8")
	i = src.index("def tao_don(")
	j = [x for x in (src.find("\ndef ", i + 10), src.find("\n@", i + 10)) if x > 0]
	than = src[i:min(j)] if j else src[i:]
	dung("tạo đơn gọi chốt ngay sau chốt thiệp ép kim, trước tính tiền", than.index("_chot_dung_cu(hang)") > than.index("chot_thiep_ep_kim(hang, chiec)")
		and than.index("_chot_dung_cu(hang)") < than.index("_gia_va_ten("))

"""v697: Kèm theo mỗi bánh chọn ở trình biên tập, Túi Panettone tách hai ô ảnh,
ảnh web nhẹ (anh Việt chốt 27/11/2026, phương án Danh sách cố định).

Nguồn việc: nhân viên báo hai Bûche thiếu nến xoắn, dao gỗ, cờ cắm trong mục
"Kèm theo mỗi bánh"; Minh Vũ báo bánh lớn và Mini của Panettone dùng chung một
ô ảnh Túi Panettone; anh Việt báo ảnh bánh hiện chậm (ảnh máy ảnh 5 tới 10 MB,
ảnh nền 8,3 MB).

Chốt:
- danh mục đồ kèm MỘT nguồn: mã ở banh_web.MA_KEM trùng du-lieu.js DO_KEM;
- ô kem_theo: None là chưa chọn (bộ mặc định), mảng rỗng là không kèm gì;
- máy chủ chặn mã lạ và size không thuộc bánh ở cửa ghi;
- trang khách, giỏ hàng, trình biên tập đi qua MỘT phép kemCho / kemMacDinhTheoSize;
- Bûche mặc định có nến xoắn, dao gỗ, cờ cắm; Panettone lớn và Mini mỗi size một túi;
- ảnh tải lên lớn hơn 1600 điểm hoặc nặng hơn 500 KB được thu nhỏ, xoay đúng chiều.
Dữ liệu trong ca là GIẢ.
"""
import io
import json
import re
import subprocess
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[3]
DL = GOC / "vagabond/public/web_vue/banh/du-lieu.js"


def _bw():
	from vagabond import banh_web

	return banh_web


def _node(ma):
	r = subprocess.run(["node", "--input-type=module", "-e", ma], cwd=GOC, capture_output=True, text=True, timeout=60)
	la("node chạy được: " + r.stderr[-600:], r.returncode, 0)
	return json.loads(r.stdout)


@ca("v697 một danh mục đồ kèm: mã của máy chủ trùng DO_KEM của trang khách, cùng thứ tự")
def _():
	bw = _bw()
	js = _node("import {DO_KEM} from './vagabond/public/web_vue/banh/du-lieu.js'; console.log(JSON.stringify(DO_KEM.map(x => x.ma)))")
	la("cùng mã, cùng thứ tự", tuple(js), bw.MA_KEM)
	nguon = DL.read_text(encoding="utf-8")
	la("chỉ một chỗ khai danh mục (không còn ACC, KEM_MUA riêng)", (nguon.count("export const DO_KEM"), "export const ACC" in nguon, "KEM_MUA" in nguon), (1, False, False))
	kho = (GOC / "vagabond/public/web_vue/banh/kho-banh.js").read_text(encoding="utf-8")
	app = (GOC / "vagabond/public/web_vue/banh/app.js").read_text(encoding="utf-8")
	bt = (GOC / "vagabond/public/web_order/bien-tap-moi.js").read_text(encoding="utf-8")
	dung("giỏ, sheet bánh thường, sheet mùa vụ đều qua kemCho", "kemCho(" in kho and app.count("kemCho(") == 2)
	dung("trình biên tập dùng bộ mặc định của trang khách, không tự khai", "kemMacDinhTheoSize(" in bt and "hop_pan_lon" not in bt)


@ca("v697 đọc ô kem_theo: trống là bộ mặc định, mảng rỗng là không kèm gì (không bị thay mặc định), mã lạ bị bỏ, ô hỏng không làm ngã trang")
def _():
	bw = _bw()
	la("chưa có ô", bw.doc_kem(None), None)
	la("chuỗi rỗng", bw.doc_kem(""), None)
	la("ô hỏng", bw.doc_kem("{không phải json"), None)
	la("không phải mảng", bw.doc_kem('{"ma": "dao_go"}'), None)
	la("mảng rỗng là lựa chọn của người dùng", bw.doc_kem("[]"), [])
	la("bỏ mã lạ, size rỗng thành ''", bw.doc_kem(json.dumps([{"ma": "dao_go"}, {"ma": "la", "size": ""}, "x", {"ma": "tui_pan_mini", "size": "GIA-M"}])),
		[{"ma": "dao_go", "size": ""}, {"ma": "tui_pan_mini", "size": "GIA-M"}])


@ca("v697 lưu đồ kèm: chặn mã lạ và size không thuộc bánh ở cửa ghi; Mọi size gộp dòng theo size; dòng trùng bỏ")
def _():
	bw = _bw()
	sz = ["GIA-L", "GIA-M"]
	la("hợp lệ, giữ thứ tự", bw.chuan_kem([{"ma": "hop_pan_lon", "size": "GIA-L"}, {"ma": "tui_pan_mini", "size": "GIA-M"}, {"ma": "thiep_noel", "size": ""}], sz),
		[{"ma": "hop_pan_lon", "size": "GIA-L"}, {"ma": "tui_pan_mini", "size": "GIA-M"}, {"ma": "thiep_noel", "size": ""}])
	la("nhận chuỗi JSON như khi gửi form", bw.chuan_kem('[{"ma": "dao_go"}]', sz), [{"ma": "dao_go", "size": ""}])
	la("mảng rỗng hợp lệ", bw.chuan_kem([], sz), [])
	la("Mọi size gộp dòng theo size, dòng trùng bỏ",
		bw.chuan_kem([{"ma": "dao_go", "size": "GIA-L"}, {"ma": "dao_go", "size": ""}, {"ma": "nen_xoan", "size": "GIA-M"}, {"ma": "nen_xoan", "size": "GIA-M"}], sz),
		[{"ma": "dao_go", "size": ""}, {"ma": "nen_xoan", "size": "GIA-M"}])
	for sai in ([{"ma": "ruou_vang"}], [{"ma": "dao_go", "size": "MA-BANH-KHAC"}], ["dao_go"], {"ma": "dao_go"}, "{hỏng", [{"ma": "dao_go"}] * 101):
		try:
			bw.chuan_kem(sai, sz)
			ra = ""
		except ValueError as e:
			ra = str(e)
		la("chặn: %s" % str(sai)[:40], ra, bw.CAU_KEM_SAI)


@ca("v697 trang khách: bánh thường, Panettone lớn, Panettone Mini, Bûche đúng bộ mặc định; Bûche có nến xoắn, dao gỗ, cờ cắm; mỗi size Panettone một túi")
def _():
	r = _node("""import {kemCho, kemMacDinhTheoSize, ANH_O_MAC_DINH, THIEP_MUA} from './vagabond/public/web_vue/banh/du-lieu.js';
const m = ds => ds.map(x => x.ma);
console.log(JSON.stringify({
  thuong: m(kemCho(null, '', 'B16', '')), thuong_cu: m(kemCho(undefined, '', 'B16', '')),
  lon: m(kemCho(null, 'panettone', 'P1', 'Bánh Lớn 680gr')), mini: m(kemCho(null, 'panettone', 'P2', 'Bánh Mini 250gr')),
  buche: m(kemCho(null, 'buche', 'BU1', '')),
  rong: m(kemCho([], 'buche', 'BU1', '')),
  rieng_lon: m(kemCho([{ma: 'tui_pan_lon', size: 'P1'}, {ma: 'tui_pan_mini', size: 'P2'}, {ma: 'thiep_noel', size: ''}, {ma: 'la', size: ''}, {ma: 'thiep_noel', size: ''}], 'panettone', 'P1', 'Bánh Lớn')),
  rieng_mini: m(kemCho([{ma: 'tui_pan_lon', size: 'P1'}, {ma: 'tui_pan_mini', size: 'P2'}, {ma: 'thiep_noel', size: ''}], 'panettone', 'P2', 'Bánh Mini')),
  trai: kemMacDinhTheoSize('panettone', [{ma: 'P1', nhan: 'Bánh Lớn 680gr'}, {ma: 'P2', nhan: 'Bánh Mini 250gr'}]),
  o_tui: [ANH_O_MAC_DINH.anh_mv_tui_pan, ANH_O_MAC_DINH.anh_mv_tui_pan_mini],
  thiep: [THIEP_MUA.panettone.ka, THIEP_MUA.buche.ka]
}));""")
	la("bánh thường: đúng bộ có sẵn trước đây", r["thuong"], ["hop_banh", "tui_vai", "dao_go", "nen_xoan", "co_cam"])
	la("máy chủ cũ không gửi ô thì như chưa chọn", r["thuong_cu"], r["thuong"])
	la("Panettone lớn", r["lon"], ["hop_pan_lon", "tui_pan_lon", "thiep_noel"])
	la("Panettone Mini có túi riêng", r["mini"], ["hop_pan_mini", "tui_pan_mini", "thiep_noel"])
	la("Bûche thêm nến xoắn, dao gỗ, cờ cắm", r["buche"], ["hop_buche", "tui_buche", "thiep_buche", "dao_go", "nen_xoan", "co_cam"])
	la("Marketing bỏ hết thì không kèm gì", r["rong"], [])
	la("chọn riêng theo size: size lớn", r["rieng_lon"], ["tui_pan_lon", "thiep_noel"])
	la("chọn riêng theo size: size Mini", r["rieng_mini"], ["tui_pan_mini", "thiep_noel"])
	la("trình biên tập trải mặc định ra từng mã size", r["trai"],
		[{"ma": "hop_pan_lon", "size": "P1"}, {"ma": "hop_pan_mini", "size": "P2"}, {"ma": "tui_pan_lon", "size": "P1"}, {"ma": "tui_pan_mini", "size": "P2"}, {"ma": "thiep_noel", "size": ""}])
	la("hai ô ảnh túi riêng, ô cũ giữ cho bánh lớn", r["o_tui"], ["", ""])
	la("thiệp ở bước Thông tin đơn hàng dùng cùng ô ảnh", r["thiep"], ["anh_mv_thiep_noel", "anh_mv_thiep_buche"])
	chu = json.loads((GOC / "vagabond/public/web_order/chu-mac-dinh.json").read_text(encoding="utf-8"))
	dung("ô ảnh Túi Panettone Mini có trong trình biên tập", chu.get("anh_mv_tui_pan_mini", {}).get("anh") is True)
	dung("ô ảnh cũ ghi rõ là bánh lớn", "bánh lớn" in chu["anh_mv_tui_pan"]["ten"])
	nguon = DL.read_text(encoding="utf-8")
	for ma, k in re.findall(r"\{ma: '([a-z_]+)', k: '([a-z0-9_]+)'", nguon):
		dung("chữ của %s có trong sổ nhãn" % ma, k in chu)


@ca("v697 ảnh web nhẹ: ảnh lớn thu về cạnh 1600 và xoay đúng chiều, ảnh nền trong giữ PNG, ảnh nhỏ giữ nguyên (máy có Pillow)")
def _():
	try:
		from PIL import Image
	except ImportError:
		return
	from vagabond import anh_web

	def tao(co, kieu, mau="RGB", exif_xoay=None):
		a = Image.new(mau, co, (180, 90, 40) if mau == "RGB" else (180, 90, 40, 120))
		for x in range(0, co[0], 7):
			for y in range(0, co[1], 97):
				a.putpixel((x, y), (x % 255, y % 255, 30) if mau == "RGB" else (x % 255, y % 255, 30, 200))
		b = io.BytesIO()
		if exif_xoay:
			ex = Image.Exif()
			ex[0x0112] = exif_xoay
			a.save(b, kieu, quality=97, exif=ex)
		else:
			a.save(b, kieu, quality=97) if kieu == "JPEG" else a.save(b, kieu)
		return b.getvalue()

	lon = tao((4000, 3000), "JPEG", exif_xoay=6)
	moi, duoi = anh_web.thu_nho_anh(lon)
	with Image.open(io.BytesIO(moi)) as a:
		la("ảnh chụp dọc (EXIF xoay 90) ra đúng chiều, cạnh dài 1600", (a.size, duoi), ((1200, 1600), "jpg"))
	dung("nhẹ hơn bản gốc", len(moi) < len(lon))
	nho = tao((800, 600), "JPEG")
	la("ảnh đã nhỏ và nhẹ giữ nguyên từng byte", anh_web.thu_nho_anh(nho), (nho, "jpg"))
	trong = tao((2400, 1200), "PNG", mau="RGBA")
	moi2, duoi2 = anh_web.thu_nho_anh(trong)
	with Image.open(io.BytesIO(moi2)) as a:
		la("ảnh nền trong giữ PNG, giữ kênh trong", (a.size, duoi2, a.mode), ((1600, 800), "png", "RGBA"))
	nguon = (GOC / "vagabond/noi_dung_web.py").read_text(encoding="utf-8")
	tim = nguon[nguon.index("def luu_anh_cong_khai("):]
	dung("cửa tải ảnh duy nhất của web gọi thu_nho_anh trước khi lưu", tim.index("thu_nho_anh(noi_dung)") < tim.index("save_file("))


@ca("v697 ảnh nền nhẹ: mọi nơi dùng anh-bia.jpg, PNG cũ vẫn được nhận là ảnh nền")
def _():
	from vagabond import anh_web, google_merchant as gm

	la("đường dẫn", anh_web.ANH_NEN, "/assets/vagabond/web_order/anh-bia.jpg")
	dung("tệp JPG có và dưới 400 KB", (GOC / "vagabond/public/web_order/anh-bia.jpg").stat().st_size < 400 * 1024)
	la("Google không nhận cả hai bản ảnh nền", (gm.anh_tuyet_doi(anh_web.ANH_NEN), gm.anh_tuyet_doi(anh_web.ANH_NEN_CU + "?v=2")), ("", ""))
	for tep in ("vagabond/public/web_vue/banh/du-lieu.js", "vagabond/trang/banh.html", "vagabond/public/web_order/thanh-vien.js", "vagabond/public/web_order/thanh-vien.css"):
		s = (GOC / tep).read_text(encoding="utf-8")
		dung(tep + " không còn trỏ ảnh nền PNG nặng", "anh-bia.png" not in s and "anh-bia.jpg" in s)


@ca("v697 trình biên tập, thẻ Bánh: bấm thật bằng node (hanh_vi/bien_tap_kem_697.js)")
def _():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/bien_tap_kem_697.js")], capture_output=True, text=True, timeout=120)
	la("mã trả về", (r.returncode, (r.stdout + r.stderr)[-800:] if r.returncode else ""), (0, ""))


@ca("v697 ảnh anh Việt 27/11: Bûche của mùa đang bán nhận 23/12 không bị luật ba ngày của bánh đặt trước thường chặn; bánh thường vẫn bị xét")
def _():
	import datetime
	from unittest.mock import patch

	from vagabond import mua_vu_web as w
	from vagabond import ton_don_web as t

	mua = {"ma_mua": ["GIA-BU1", "GIA-PA1"], "loai_theo_ma": {"GIA-BU1": "buche"}}
	hang = [{"variation_id": "GIA-BU1", "quantity": 1}, {"variation_id": "GIA-THUONG", "quantity": 1}]
	la("bỏ mã của mùa", w.bo_hang_mua(hang, mua), [{"variation_id": "GIA-THUONG", "quantity": 1}])
	la("không có mùa thì giữ nguyên", w.bo_hang_mua(hang, None), hang)
	# Dựng đúng phép xa ngày của ton_don_web: cả hai mã đều có trên bảng BTP.
	btp = type("B", (), {"dong": [type("D", (), {"ma_hang": m, "ten_banh": m})() for m in ("GIA-BU1", "GIA-THUONG")]})()
	with patch.object(t, "hom_nay", lambda: datetime.date(2026, 11, 27)), patch.object(t, "_kiem_refill", lambda h, n, nay: (set(), [])), \
		patch.object(t, "_ton_phieu", lambda ng: {}), patch.object(t.frappe, "get_single", lambda dt: btp, create=True):
		cu = t.kiem(hang, "2026-12-23")
		moi = t.kiem(w.bo_hang_mua(hang, mua), "2026-12-23")
	dung("trước v697: Bûche bị chặn", any("GIA-BU1" in x for x in cu))
	la("từ v697: chỉ bánh thường còn bị nhắc", [x.split(" là ")[0] for x in moi], ["GIA-THUONG"])
	# Cửa nhận đơn THẬT (tao_don, môi trường giả của bộ #367) với luật ba ngày THẬT:
	# mã của mùa nhận 23/12 ghi được, bánh thường trên bảng BTP vẫn bị chặn.
	from vagabond.khung.kiem_thu import thu_tran_ngay_697 as t697
	btp2 = type("B", (), {"dong": [type("D", (), {"ma_hang": m, "ten_banh": m})() for m in ("GIA-P1", "GIA-THUONG")]})()
	ton = {"hom_nay": lambda: datetime.date(2026, 11, 27), "_kiem_refill": lambda h, n, nay: (set(), []), "_ton_phieu": lambda ng: {}}
	with patch.object(t.frappe, "get_single", lambda dt: btp2, create=True):
		r, vet = t697._tao_mua([{"variation_id": "GIA-P1", "quantity": 1}], t697._mua_gia([]), ton=ton)
		la("cửa nhận đơn: hàng của mùa nhận 23/12 ghi được", (r.get("ok"), "ghi" in vet.su), (1, True))
		r, vet = t697._tao_mua([{"variation_id": "GIA-P1", "quantity": 1}, {"variation_id": "GIA-THUONG", "quantity": 1}], t697._mua_gia([]), ton=ton)
		la("cửa nhận đơn: bánh thường cùng giỏ vẫn bị luật ba ngày", (r.get("ly_do"), "ghi" in vet.su), ("het_hang", False))

"""v651 đối soát GrabFood: PyMuPDF trên Frappe Cloud gộp mã đơn ngắt dòng vào giữa dòng.

Site thật 12/11/2026, bot Zalo báo: GrabFood Sales Online 11/11 (DSN-2611-06914)
3 dòng lỗi ở vị trí 15, 21, 24; GrabFood TCV 11/11 (DSN-2611-06912) 10 dòng lỗi.
Bản sửa v649 không ăn vì ca kiểm v649 dựng chữ bằng tay theo phỏng đoán ba mảnh
nằm ba dòng riêng. Chữ dưới đây là đầu ra THẬT của PyMuPDF 1.24.14 (đúng bản
máy chủ: số dòng lỗi trùng 15, 21, 24) trên tệp 06914: tiền tố "GF-" đứng TRƯỚC
giờ, phần sau "509F" dính ở CUỐI dòng. PyMuPDF 1.26 cho cùng dạng.
"""
from itertools import permutations

from vagabond import doi_soat_khop as K
from vagabond import doi_soat_mau as M
from vagabond.khung.kiem_thu.nen import ca, dung, la

# Đầu ra thật PyMuPDF 1.24.14, trang 1 tệp 5-C4E1NPWGMGBGNX-20261111.pdf, giữ nguyên
# khoảng trắng (chỉ bỏ khoảng trắng cuối dòng như doi_soat_doc.doc_pdf).
THAT_0614 = 'Báo cáo kinh doanh hàng ngày\n11 tháng 11 2026, thứ tư                                                                                                    https://grb.to/hotrodoitacnhahang\n                                                                                                                                https://grb.to/hotrodoitacnhahang\nThe Vagabond Delivery Kitchen                                                                                             +842871098466\nTóm tắt thông tin\n  Tổng thu nhập                                           Còn thiếu Grab                 Tổng số đơn hàng\n VND 1.028.974              VND 0          11 đơn hàng\nThu nhập\nTổng tiền thanh toán sẽ được chuyển cho bạn vào ngàythứ năm, tháng 11 12. Tài khoản của bạn có thể phải đợi vài ngày trước khi ghi nhận số tiền này.\n  Trịgiá đơn              Phí dịch vụ của    Khuyến mãi từ        Tổng chiết khấu cho    Tài trợ giảm giá phí giao    Phí quảng      Tổng thu     Còn thiếu              GTGT hàng                quán              người bán            Grab                hàng                    cáo              nhập         Grab\n 1.790.000    0      0               -522.500           -186.579           0                      -51.947     1.028.974          0\nĐơn hàng từ ứng dụng và web\n  Thời gian     Mã đơn    Phương thức       Trịgiá đơn               Phí dịch vụ     Khuyến mãi từ    Tổng chiết khấu    Tài trợ giảm giá phí                                                 GTGT                                                                     Thu nhập  giao hàng     hàng      thanh toán            hàng              của quán          người bán          cho Grab             giao hàng\n Đơn hàng Delivery\n               GF- 5:01 PM                       Trả thẻ / Ví       100.000      0                      -          -39.500            -8.905                 0    51.595             509F\n 4:55 PM      GF-554   Trả thẻ / Ví       350.000      0                      -          -71.500          -40.996                 0   237.504\n 4:44 PM      GF-294   Trả thẻ / Ví         90.000      0                      -          -42.000            -7.065                 0    40.935\n 4:38 PM      GF-117   Trả thẻ / Ví       250.000      0                      -          -68.000          -26.791                 0   155.209\n 3:28 PM      GF-838   Trả thẻ / Ví       200.000      0                      -          -50.500          -22.007                 0   127.493\n 1:57 PM      GF-595   Trả thẻ / Ví       280.000      0                      -          -72.000          -30.618                 0   177.382\n               GF- Đã hủy                                        -                                       -           -                     -                          -                          -                              -              -             059F\n 1:40 PM      GF-731   Trả thẻ / Ví       280.000      0                      -          -92.500          -27.601                 0   159.899\n 1:39 PM      GF-096   Trả thẻ / Ví       180.000      0                      -          -69.500          -16.266                 0    94.234\n               GF- Đã hủy                                        -                                       -           -                     -                          -                          -                              -              -             469F\n 9:13 AM      GF-869   Trả thẻ / Ví         60.000      0                      -          -17.000            -6.330                 0    36.670\n                                                                                                                     1.080.921\n Tổng cộng                                       VND 1.080.921\nMarketing\n  Thời gian giao hàng      Mã giao dịch     Mô tả                                                               Phí quảng cáo      Thuế         Tổng cộng\n 11 Th11, 1:39 PM           -            Từ khóa thủ công - 2026-11-11                              -45.500           -3.639        -49.139\n 11 Th11, 1:57 PM           -             Đồng tài trợ đa tầng - GrabUnlimited - 2026-11-11             -1.000            -80            -1.080\n 11 Th11, 5:02 PM           -             Đồng tài trợ đa tầng - Tiêu Chuẩn - 2026-11-11               -800              -64             -864\n 11 Th11, 5:02 PM           -             Đồng tài trợ đa tầng - Riêng cho bạ - 2026-11-11             -800              -64             -864\n                                                                                                             VND-51.947\nHướng dẫn đọc hiểu báo cáo\nTất cả các trịgiá tiền đều được tính bằng VND. Để tiện cho việc tính toán, tổng trịgiá trong báo cáo này có thể được làm tròn khi cần thiết.\n  Thuật ngữ   Ý nghĩa\n Trịgiá      Giá bán của các món ăn trong đơn hàng, đã bao gồm thuế GTGT, nhưng không bao gồm khuyến mãi từ đối tác và Phí hoa hồng của\n đơn hàng   Grab.'


def _tep(chu=THAT_0614):
	return dict(ten="5-C4E1NPWGMGBGNX-20261111.pdf", loai="pdf", sha256="x",
		trang=[dict(ten="Trang 1", dong=chu.split("\n"))])


@ca("v651 GrabFood: tệp thật Sales Online 11/11 đọc đủ, không dòng lỗi, cộng đúng Tổng thu nhập")
def _():
	kq = M.doc(_tep())
	la("không lỗi", (kq["dong_loi"], kq["loi"]), ([], []))
	ban = [d for d in kq["dong"] if d["loai"] == "ban"]
	la("chín đơn bán", len(ban), 9)
	la("đơn mã ngắt dòng", [(d["ma_don"], d["gio"], d["thuc_nhan"]) for d in ban if d["ma_don"] == "GF-509F"],
		[("GF-509F", "17:01:00", 51595)])
	la("hai đơn huỷ ghép đủ mã", sorted(kq["them"]["don_huy"]), ["GF-059F", "GF-469F"])
	la("cộng = Tổng thu nhập", sum(d["thuc_nhan"] for d in kq["dong"]), 1028974)


@ca("v651 GrabFood: chuan_dong_don_grab xếp lại dòng gộp, dòng chuẩn giữ nguyên")
def _():
	d = [x for x in THAT_0614.split("\n") if "509F" in x][0]
	la("đơn bán", M.chuan_dong_don_grab(d),
		"5:01 PM GF-509F Trả thẻ / Ví 100.000 0 - -39.500 -8.905 0 51.595")
	h = [x for x in THAT_0614.split("\n") if "059F" in x][0]
	la("đơn huỷ", M.chuan_dong_don_grab(h), "Đã hủy GF-059F - - - - - - - -")
	c = " 4:55 PM      GF-554    Trả thẻ / Ví       350.000      0      -   -71.500  -40.996   0   237.504"
	la("dòng chuẩn không đổi", M.chuan_dong_don_grab(c), c)
	la("dòng không phải đơn không đổi", M.chuan_dong_don_grab("   509F"), "   509F")


@ca("v651 GrabFood: mã GD- dài (TCV 11/11 GD-NUUE6UD2) ghép đúng dù tiền tố và đuôi nằm ở đâu trong dòng")
def _():
	manh = ["GD-", "Trả thẻ / Ví 305.000 0 - -60.000 -36.065 0 208.935", "NUUE6UD2"]
	for tt in permutations(manh):
		dong = "   ".join([tt[0], "4:12 PM", tt[1], tt[2]])
		la("ghép %s" % dong[:40], M.chuan_dong_don_grab(dong),
			"4:12 PM GD-NUUE6UD2 Trả thẻ / Ví 305.000 0 - -60.000 -36.065 0 208.935")


@ca("v651 GrabFood: đơn gộp hai mã (TCV 11/11 GF-736, GF-755) đọc được và khớp hoá đơn gõ mã nào cũng được")
def _():
	gop = "  GF-736, 12:42 PM   Trả thẻ / Ví  2.850.000 0 - -64.500 -410.036 0 2.375.464   GF-755"
	ra = M.chuan_dong_don_grab(gop)
	la("dạng chuẩn", ra, "12:42 PM GF-736,GF-755 Trả thẻ / Ví 2.850.000 0 - -64.500 -410.036 0 2.375.464")
	chuan = " 12:42 PM  GF-736, GF-755  Trả thẻ / Ví  2.850.000 0 - -64.500 -410.036 0 2.375.464"
	la("dòng đã đúng thứ tự giữ nguyên", M.chuan_dong_don_grab(chuan), chuan)
	for d in (ra, chuan):
		la("là dòng đủ", M.loai_manh_grab(d), "du")
	chu = THAT_0614.replace(" 9:13 AM      GF-869   Trả thẻ / Ví         60.000      0                      -          -17.000"
		"            -6.330                 0    36.670", gop).replace("1.080.921", "3.419.715").replace(
		"VND 1.028.974", "VND 3.367.768").replace("11 đơn hàng", "11 đơn hàng")
	kq = M.doc(_tep(chu))
	la("không lỗi", kq["dong_loi"], [])
	la("đơn gộp", [(d["ma_don"], d["thuc_nhan"]) for d in kq["dong"] if "," in d["ma_don"]],
		[("GF-736,GF-755", 2375464)])
	dung("khớp GF-755", K._ma_khop("grab", "GF-736,GF-755", "GF-755"))
	dung("khớp GF-736", K._ma_khop("grab", "GF-736,GF-755", "GF-736"))
	dung("không khớp mã khác", not K._ma_khop("grab", "GF-736,GF-755", "GF-737"))


@ca("v651 GrabFood: dòng mơ hồ thì KHÔNG đoán, vẫn báo lỗi kèm chữ gốc")
def _():
	for dong in ("GF- GF- 5:01 PM Trả thẻ / Ví 100.000 0 - -39.500 -8.905 0 51.595 509F",
			"GF- 5:01 PM Trả thẻ / Ví 100.000 0 - -39.500 -8.905 0 51.595 509F 77AB",
			"GF- 5:01 PM Trả thẻ / Ví 100.000 0 - -39.500 -8.905 51.595 509F",
			"GF- 5:01 PM 4:02 PM Trả thẻ / Ví 100.000 0 - -39.500 -8.905 0 51.595 509F"):
		la("giữ nguyên %s" % dong[-24:], M.chuan_dong_don_grab(dong), dong)
	chu = THAT_0614.replace("51.595             509F", "51.595             509F  77AB")
	kq = M.doc(_tep(chu))
	la("một dòng lỗi", len(kq["dong_loi"]), 1)
	dung("lỗi giữ chữ gốc", "509F" in " ".join(kq["dong_loi"][0]["tho"]))


@ca("v651 đối soát vendor: dòng lỗi gửi về màn và lưu vào nguồn kèm chữ máy đọc được")
def _():
	from vagabond import doi_soat_vendor as V
	la("cắt ba mảnh 200 ký tự", V._tho_ngan({"tho": ["a" * 300, "b", "c", "d"]}), ["a" * 200, "b", "c"])
	la("không có chữ", V._tho_ngan({}), [])
	xt = K.xem_truoc(M.doc(_tep(THAT_0614.replace("51.595             509F", "51.595  509F  77AB"))), "C")
	loi = [x for x in xt["dong"] if x["trang_thai"] == "loi"]
	dung("xem trước giữ chữ gốc", loi and "509F" in " ".join(loi[0]["tho"]))

"""Số tiền phân bổ không được bị ép ngầm thành toàn bộ dư nợ."""
from decimal import Decimal
from vagabond.phan_bo_app import gom, tien_hop_le
from vagabond.khung.kiem_thu.nen import ca, la, dung


@ca("APP từng đợt: cộng cùng hóa đơn chính xác, giữ riêng hóa đơn khác")
def _():
    la("gộp", gom([{"hoa_don": "A", "so_tien": "0.1"},
        {"hoa_don": "A", "so_tien": "0.2"}, {"hoa_don": "B", "so_tien": 3000000}]),
        {"A": Decimal("0.3"), "B": Decimal(3000000)})


@ca("APP từng đợt: số tiền lỗi không trở thành cả hóa đơn")
def _():
    for x in (None, "", "abc", 0, -1, True, "NaN", "Infinity", float("nan")):
        try:
            tien_hop_le(x)
        except ValueError:
            continue
        dung("phải chặn %r" % x, False)

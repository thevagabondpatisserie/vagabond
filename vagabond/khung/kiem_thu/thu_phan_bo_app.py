"""Số tiền phân bổ không được bị ép ngầm thành toàn bộ dư nợ."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
import frappe
from vagabond import phan_bo_app as pb
from vagabond.phan_bo_app import gom, tien_hop_le
from vagabond.khung.kiem_thu.nen import ca, la, dung


def _kiem_so_hoc(no, xin, giu=0, da_chi=0, docstatus=1, loi=""):
    """Chạy cả cửa kiem và phép trừ PE; chỉ giả dữ liệu, không thay helper."""
    class LoiKhoaThu(Exception):
        pass
    hd = SimpleNamespace(docstatus=docstatus, outstanding_amount=no,
        supplier="NCC", company="CT", currency="VND")
    def sql(cau, tham_so, as_dict=False):
        if "Vagabond Ho So TT Dong" in cau:
            return ([SimpleNamespace(name="APP-A", ma="APP-A", hoa_don="HD-1",
                so_tien=giu)] if giu else [])
        return ([SimpleNamespace(vgb_ho_so_tt="APP-A", reference_name="HD-1",
            allocated_amount=da_chi)] if da_chi else [])
    with patch.object(frappe.db, "get_value", return_value=hd), \
            patch.object(frappe.db, "sql", side_effect=sql), \
            patch.object(frappe, "QueryDeadlockError", LoiKhoaThu, create=True):
        if loi:
            try:
                pb.kiem([{"hoa_don": "HD-1", "so_tien": xin}], khoa=False)
            except frappe.ValidationError as exc:
                dung("đúng lý do chặn", loi in str(exc))
            else:
                dung("phải chặn", False)
        else:
            la("cho qua đúng hóa đơn", pb.kiem(
                [{"hoa_don": "HD-1", "so_tien": xin}], khoa=False), {"HD-1": hd})


@ca("APP số học: không ai giữ, xin hết 10 triệu được qua")
def _():
    _kiem_so_hoc(10000000, 10000000)


@ca("APP số học: giữ 7 triệu, xin 4 triệu bị chặn")
def _():
    _kiem_so_hoc(10000000, 4000000, 7000000, loi="tối đa 3.000.000 đ")


@ca("APP số học: giữ 7 triệu, xin đúng 3 triệu được qua")
def _():
    _kiem_so_hoc(10000000, 3000000, 7000000)


@ca("APP số học: đã ghi sổ đủ 7 triệu không giữ lại phần đã chi")
def _():
    _kiem_so_hoc(3000000, 3000000, 7000000, 7000000)


@ca("APP số học: mới ghi sổ 5 trên 7 triệu vẫn giữ 2 triệu")
def _():
    _kiem_so_hoc(5000000, 4000000, 7000000, 5000000, loi="tối đa 3.000.000 đ")


@ca("APP số học: hóa đơn đã hủy còn số dư vẫn bị chặn")
def _():
    _kiem_so_hoc(10000000, 1000000, docstatus=2, loi="chưa ghi sổ hoặc đã hủy")


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


@ca("APP giữ tiền: chỉ khóa hóa đơn đang kiểm và trừ phần đã ghi sổ")
def _():
    goi = []
    def sql(cau, tham_so, as_dict=False):
        goi.append((cau, tham_so))
        if "Vagabond Ho So TT Dong" in cau:
            return [SimpleNamespace(name="APP-A", ma="APP.26.09.001",
                hoa_don="HD-1", so_tien=7000000)]
        return [SimpleNamespace(vgb_ho_so_tt="APP-A", reference_name="HD-1",
            allocated_amount=2000000)]
    with patch.object(frappe.db, "sql", side_effect=sql):
        la("còn giữ 5 triệu", pb.dang_giu(khoa=True, hoa_don={"HD-1"}),
            {"HD-1": Decimal(5000000)})
    dung("lọc đúng hóa đơn trong SQL", "d.hoa_don in %s" in goi[0][0])
    la("tham số lọc chỉ có HD-1", goi[0][1][2], ("HD-1",))
    dung("cả hai lượt đọc đều khóa", all("for update" in x[0] for x in goi))


@ca("APP báo tiền: có phân cách hàng nghìn và không lộ Decimal thô")
def _():
    hd = SimpleNamespace(docstatus=1, outstanding_amount=10000000,
        supplier="NCC", company="CT", currency="VND")
    with patch.object(frappe.db, "get_value", return_value=hd), \
            patch.object(pb, "dang_giu", return_value={"HD-1": Decimal(7000000)}):
        try:
            pb._kiem([{"hoa_don": "HD-1", "so_tien": 4000000}])
        except frappe.ValidationError as exc:
            cau = str(exc)
        else:
            dung("phải chặn vượt phần còn đề nghị", False)
            return
    dung("đọc được ba con số", "10.000.000 đ" in cau and
        "7.000.000 đ" in cau and "3.000.000 đ" in cau)

"""Tính phần tiền còn có thể chọn trước khi nối Bank Transaction Payments.

Phép thuần phục vụ A1 sau v594. Chưa nối vào cửa ghi: caller phải khóa và
đọc lại phân bổ lõi, chỗ giữ của mọi luồng bằng current read trong cùng
giao dịch. Không dùng kết quả đọc thường này như quyền ghi sổ.
"""
import json
from decimal import Decimal, InvalidOperation


def so_tien(v, cho_khong=False):
    try:
        n = Decimal(str(v))
        if not n.is_finite() or n < 0 or (not cho_khong and n == 0):
            raise ValueError("Số phân bổ không hợp lệ.")
        return n
    except (InvalidOperation, TypeError):
        raise ValueError("Số phân bổ không hợp lệ.")


def _ma(v):
    if not isinstance(v, str) or not v.strip() or v != v.strip():
        raise ValueError("Mã phân bổ không hợp lệ.")
    return v


def doc_bo(chuoi):
    """Dữ liệu hỏng phải nổi lỗi, không biến thành bộ rỗng để nhả tiền."""
    if chuoi is None or chuoi == "":
        return {"dong": [], "chung_tu": []}
    b = json.loads(chuoi) if isinstance(chuoi, str) else chuoi
    if not isinstance(b, dict) or set(b) != {"dong", "chung_tu"}:
        raise ValueError("Bộ sao kê không đúng cấu trúc.")
    if not isinstance(b["dong"], list) or not isinstance(b["chung_tu"], list):
        raise ValueError("Dòng phân bổ phải là danh sách.")
    da = set()
    for d in b["dong"]:
        if not isinstance(d, dict) or set(d) != {"name", "phan_bo"}:
            raise ValueError("Dòng sao kê không đúng cấu trúc.")
        ma = _ma(d["name"])
        if ma in da:
            raise ValueError("Bộ sao kê có dòng trùng.")
        so_tien(d["phan_bo"])
        da.add(ma)
    da = set()
    for c in b["chung_tu"]:
        if not isinstance(c, dict) or set(c) != {"doctype", "name"}:
            raise ValueError("Chứng từ phân bổ không đúng cấu trúc.")
        if c["doctype"] not in ("Payment Entry", "Journal Entry"):
            raise ValueError("Bộ sao kê có loại chứng từ không hợp lệ.")
        ma = (c["doctype"], _ma(c["name"]))
        if ma in da:
            raise ValueError("Bộ sao kê có chứng từ trùng.")
        da.add(ma)
    return b


def phan_con(tien, phan_loi, cac_bo, ma, chu=None):
    """Trừ lõi và phần giữ chưa thành phân bổ, không trừ hai lần.

    phan_loi có doctype/name/tien. cac_bo có chu/dong/chung_tu. Phần của
    chính phiếu đang kiểm được cộng lại để retry không tự chặn mình.
    Chứng từ lõi khác không thuộc bộ vẫn trừ đủ, không tự bỏ qua SI/JE.
    Dữ liệu trùng chủ hoặc âm không được làm tăng số tiền còn dùng được.
    """
    tong = so_tien(tien)
    _ma(ma)
    loi = {}
    for p in phan_loi:
        k = (_ma(p["doctype"]), _ma(p["name"]))
        if k in loi:
            raise ValueError("Phân bổ lõi có chứng từ trùng.")
        loi[k] = so_tien(p["tien"], cho_khong=True)
    da = sum(loi.values(), Decimal(0))
    if da > tong:
        raise ValueError("Phân bổ lõi vượt số tiền giao dịch.")
    giu, cua_minh = Decimal(0), Decimal(0)
    chu_da, ct_da = set(), set()
    for b in cac_bo:
        ten_chu = _ma(b["chu"])
        if ten_chu in chu_da:
            raise ValueError("Một phiếu giữ tiền bị đọc trùng.")
        chu_da.add(ten_chu)
        doc_bo({"dong": b["dong"], "chung_tu": b["chung_tu"]})
        phan = sum((so_tien(d["phan_bo"]) for d in b["dong"] if d["name"] == ma), Decimal(0))
        ct = {(d["doctype"], d["name"]) for d in b["chung_tu"]}
        if ct & ct_da:
            raise ValueError("Một chứng từ lõi đang thuộc nhiều bộ sao kê.")
        ct_da.update(ct)
        da_noi = sum((loi.get(k, Decimal(0)) for k in ct), Decimal(0))
        if da_noi > phan or phan > tong:
            raise ValueError("Phần giữ và liên kết lõi chưa khớp; đọc lại trước khi phân bổ.")
        if ten_chu == chu:
            cua_minh += da_noi
        else:
            giu += phan - da_noi
    if da + giu > tong:
        raise ValueError("Các phiếu đã giữ vượt phần tiền còn lại.")
    return float(tong - da - giu + cua_minh)


def de_xuat_bo(dong, ma_phieu, can, tai_khoan, chieu):
    """Tự chọn cả bộ có cùng mã, không tìm tổ hợp ngẫu nhiên cho đủ tiền.

    Caller cung cấp các dòng đã đọc quyền/nguồn, còn phần tiền thật. Mã ở
    nội dung hoặc tham chiếu được chuẩn hoá theo cùng luật SePay hiện có.
    Dòng có mã nhưng sai tài khoản/chiều phải hiện lỗi, không bị bỏ qua để
    làm bộ có vẻ đủ. Đây là đề xuất, cửa ghi phải khoá và tính lại.
    """
    from vagabond.khop_sao_ke import co_ma, xet_bo
    _ma(ma_phieu)
    _ma(tai_khoan)
    if chieu not in ("ra", "vao"):
        raise ValueError("Chiều tiền không hợp lệ.")
    ds = []
    for d in dong:
        if co_ma(d.get("description"), ma_phieu) or co_ma(d.get("reference_number"), ma_phieu):
            r = dict(d)
            r["phan_bo"] = r.get("con_lai", r.get("tien"))
            ds.append(r)
    kq = xet_bo(ds, can, tai_khoan, chieu, dung_sai=0)
    kq["dong"] = [{"name": d["name"], "phan_bo": d["phan_bo"]} for d in ds]
    return kq


def nhan_ket_qua(k):
    """Thông báo tổng thực tế từ cùng phép xét, không tự tính lại ở adapter."""
    tien=lambda n: format(n,',.0f').replace(',','.')
    return 'Ngân hàng có %s / %s đ; còn thiếu %s đ, dư %s đ. Mở Khớp tay để chọn phần thực tế.' % tuple(
        tien(k[x]) for x in ('tong','can','thieu','thua'))

"""#257: rà đơn vị từ bản xuất JSON trước khi chuẩn hoá danh mục.

Không suy 1 thùng bằng bao nhiêu quả từ tên hàng. Chỉ dùng quy ước đã duyệt
truyền rõ theo item_code; không kết nối site, không sửa chứng từ hoặc danh mục.
"""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def ra(mon, quy_uoc):
    """mon: các Item với stock_uom và uoms; quy_uoc: item_code -> stock_uom."""
    loi = []
    da_gap = set()
    for hang in mon:
        ma = hang['item_code']
        def ghi(loai, chi_tiet):
            loi.append(dict(item_code=ma, loai=loai, chi_tiet=chi_tiet))
        if ma in da_gap:
            ghi('trung_mon', 'Bản xuất có nhiều dòng cùng item_code, kiểm lại nguồn xuất.')
        da_gap.add(ma)
        goc = hang.get('stock_uom')
        if not goc:
            ghi('thieu_don_vi_kho', 'Chưa khai đơn vị tồn kho.')
        if ma in quy_uoc and goc != quy_uoc[ma]:
            ghi('lech_quy_uoc', 'Đang dùng %s; quy ước đã duyệt là %s.' % (goc, quy_uoc[ma]))
        don_vi = {}
        for dong in hang.get('uoms') or []:
            ten = dong.get('uom')
            if not ten:
                ghi('thieu_don_vi_quy_doi', 'Dòng quy đổi chưa có tên đơn vị.')
            if ten in don_vi:
                ghi('trung_don_vi', 'Đơn vị %s lặp trong bảng quy đổi.' % ten)
            try:
                he = Decimal(str(dong.get('conversion_factor')))
                if not he.is_finite() or he <= 0:
                    raise ValueError()
            except (InvalidOperation, ValueError):
                ghi('he_so_khong_hop_le', 'Đơn vị %s cần hệ số hữu hạn lớn hơn 0.' % ten)
                he = None
            don_vi[ten] = he
            if ten == goc and he is not None and he != 1:
                ghi('he_so_goc_khac_mot', 'Đơn vị tồn kho %s phải có hệ số 1.' % ten)
        for truong in ('purchase_uom', 'sales_uom'):
            ten = hang.get(truong)
            if ten and ten != goc and ten not in don_vi:
                ghi('thieu_quy_doi', '%s=%s chưa có trong bảng quy đổi.' % (truong, ten))
    for ma in sorted(set(quy_uoc) - da_gap):
        loi.append(dict(item_code=ma, loai='thieu_mon_trong_ban_xuat', chi_tiet='Chưa đủ dữ liệu kiểm quy ước đã duyệt.'))
    return dict(so_mon=len(mon), so_phat_hien=len(loi), phat_hien=loi, chi_doc=True)


if __name__ == '__main__':
    bo = argparse.ArgumentParser(description=__doc__)
    bo.add_argument('nguon', type=Path)
    bo.add_argument('dich', type=Path)
    args = bo.parse_args()
    du_lieu = json.loads(args.nguon.read_text(encoding='utf-8'))
    ket = ra(du_lieu['items'], du_lieu.get('quy_uoc_da_duyet', {}))
    args.dich.write_text(json.dumps(ket, ensure_ascii=False, indent=2), encoding='utf-8')
    print('%s món, %s phát hiện; không sửa dữ liệu.' % (ket['so_mon'], ket['so_phat_hien']))

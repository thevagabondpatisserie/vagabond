"""#339: chạy cửa Từ chối/Hủy, không chỉ tìm chữ trong mã."""
from unittest.mock import patch
from types import SimpleNamespace
from vagabond.khung.kiem_thu.nen import ca, la, dung, Doi


@ca("339 APP: NCC/hoàn ứng có hóa đơn sẵn được trả lại; hóa đơn sinh vẫn chặn")
def _():
    from vagabond import ho_so_tt as hs
    for loai, remarks, chan in [("NCC", "", False), ("Hoan ung HD", "", False),
            ("Hoan ung", "", True), ("NCC", "Hoàn ứng APP-THU - NCC", True),
            ("NCC", "Hoàn ứng APP-KHAC - NCC", False)]:
        for buoc in ("tu_choi", "huy"):
            log = []
            doc = SimpleNamespace(name="APP-THU", loai=loai, trang_thai="Cho ke toan",
                dong=[Doi(hoa_don="PI-THU", de_nghi_chi="")], flags=SimpleNamespace(),
                save=lambda **k: log.append("save"))
            with patch.object(hs.frappe, 'get_doc', return_value=doc), \
                    patch.object(hs.frappe.db, 'get_value', side_effect=lambda dt, name, field, **k: (1 if field == 'docstatus' else Doi(docstatus=1, remarks=remarks))), \
                    patch.object(hs.frappe.db, 'commit', side_effect=lambda: log.append("commit")), \
                    patch.object(hs, '_kiem'), patch.object(hs, '_ghi_vet'):
                loi = None
                try:
                    hs.duyet(doc.name, buoc, "Sửa liên kết hóa đơn")
                except Exception as e:
                    loi = str(e)
                la(str((loai, remarks, buoc)), bool(loi), chan)
                if chan:
                    dung("đúng lỗi hóa đơn đã ghi sổ", "ĐÃ GHI SỔ" in (loi or ""))
                    la("không lưu/commit", log, [])
                else:
                    la("lưu rồi commit", log, ["save", "commit"])


@ca("339 APP: đọc DB lỗi không bỏ qua; hóa đơn hủy không bị coi là đã sinh còn hiệu lực")
def _():
    from vagabond import ho_so_tt as hs
    doc = SimpleNamespace(name="APP-THU", loai="Hoan ung", dong=[Doi(hoa_don="PI-THU")])
    with patch.object(hs.frappe.db, 'get_value', side_effect=lambda dt, name, field, **k: (2 if field == 'docstatus' else Doi(docstatus=2, remarks=""))):
        la("PI đã hủy", hs._hoa_don_da_sinh(doc), [])
    with patch.object(hs.frappe.db, 'get_value', side_effect=RuntimeError("DB unavailable")):
        try:
            hs._hoa_don_da_sinh(doc)
        except RuntimeError:
            return
        dung("không nuốt lỗi DB", False)

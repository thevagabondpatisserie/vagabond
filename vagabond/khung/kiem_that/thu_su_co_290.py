"""#290: lưu/ghi sổ thật, giữ VAT khi tắt kho và giữ dữ liệu người nhập khi đồng bộ."""
from unittest.mock import patch
from contextlib import ExitStack
import frappe
from vagabond import ban_hang, hang_tang
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca,la,dung
from vagabond.khung.kiem_that.thu_hang_tang_kho_243 import _nen, _sle
from vagabond.khung.kiem_that.thu_hang_tang_227 import _gl, _hoa_don

@ca('#290 kho tặng tắt: thiếu tồn vẫn ghi VAT, không SLE; hủy giữ đúng lịch sử')
def kho_tat():
    hd,kho,lo=_nen()
    frappe.db.set_single_value('Vagabond Settings','hang_tang_xuat_kho_that',0)
    hd.items[0].qty=8  # Kho chỉ có 5 từ fixture sản xuất, không nới tồn.
    hd.save(ignore_permissions=True)
    hang_tang.duyet(hd.name,'Duyệt fixture 8 bánh khi chưa triển khai kho')
    hd.reload();hd.flags.ignore_permissions=True;hd.submit();hd.reload()
    la('đã ghi sổ',hd.docstatus,1);la('không xuất kho',hd.update_stock,0)
    la('không có SLE',_sle(hd),[]);la('chờ giá vốn',hd.vgb_tang_cho_gia_von,1)
    la('chỉ VAT, không doanh thu/công nợ',{r.account for r in _gl(hd)},{hd.vgb_tang_tk_vat,hd.vgb_tang_tk_thue})
    frappe.db.set_single_value('Vagabond Settings','hang_tang_xuat_kho_that',1)
    hd.cancel();hd.reload();la('hủy được',hd.docstatus,2)
    la('hủy không sinh kho',frappe.db.count('Stock Ledger Entry',{'voucher_no':hd.name}),0)

@ca('#290 B1 đồng bộ lại SI tặng thật giữ chữ người nhập và dấu duyệt')
def dong_bo_tang():
    from vagabond import thanh_toan_nhieu as ttn
    hd=_hoa_don(False)
    hd.custom_pancake_id='THU290-'+frappe.generate_hash(length=10)
    hd.custom_pancake_display_id='THU290'
    hd.vgb_quay='TCV';hd.custom_nguon='Tại chỗ'
    hd.vgb_pt_thanh_toan='Tiền mặt';hd.vgb_pt_do_may=1
    hd.append(ttn.BANG,dict(pt='Tiền mặt',so_tien=hd.grand_total,do_may=1))
    hd.save(ignore_permissions=True);hd.reload()
    ban_hang.pos_chot(hd.name,pt='Hàng tặng')
    hang_tang.luu_thong_tin(hd.name,loai='marketing',ly_do='Tặng sự kiện tiệm sau khi Sales chọn tay')
    hang_tang.duyet(hd.name,'Duyệt quà fixture đồng bộ')
    hd.reload()
    la('lựa chọn tay hạ cờ máy',hd.vgb_pt_do_may,0)
    la('bảng máy cũ đã gỡ',list(hd.get(ttn.BANG) or []),[])
    truong=['vgb_tang_loai','vgb_tang_ly_do','vgb_tang_duyet','vgb_tang_nguoi_duyet','vgb_pt_thanh_toan']
    truoc=[hd.get(k) for k in truong]
    dong=[dict(item_code=d.item_code,qty=d.qty,rate=d.rate,warehouse=d.warehouse) for d in hd.items]
    with ExitStack() as st:
        st.enter_context(patch.object(ban_hang,'_dong_hang',return_value=(dong,[])))
        st.enter_context(patch.object(ban_hang,'_lech_pancake',return_value=0))
        st.enter_context(patch.object(ban_hang,'_doan_thanh_toan',return_value=('Tiền mặt','COD thật từ nguồn mô phỏng')))
        # Giữ nguyên _dien_dong_thanh_toan và hook validate; nguồn ngoài trả hai kênh đủ tổng.
        st.enter_context(patch.object(ban_hang,'dong_thanh_toan_pancake',return_value=[
            dict(pt='Tiền mặt',so_tien=hd.grand_total/2),dict(pt='Chuyển khoản',so_tien=hd.grand_total/2)]))
        ban_hang._upsert_hoa_don({'id':hd.custom_pancake_id,'display_id':'THU290'},hd.posting_date,hd.company,hd.customer)
    hd.reload();la('giữ dữ liệu sau DB reload',[hd.get(k) for k in truong],truoc)
    la('không nạp bảng máy cho quà tặng',list(hd.get(ttn.BANG) or []),[])

@ca('#290 A3 bill nháp cũ còn KMCB đi đúng cửa ghi sổ, rã rồi có GL thật')
def combo_cu():
    hd=_hoa_don(False)
    ma_goc=hd.items[0].item_code
    cha=frappe.copy_doc(frappe.get_doc('Item',ma_goc))
    cha.item_code='KMCB-290-'+frappe.generate_hash(length=8)
    cha.insert(ignore_permissions=True);nen._DA_TAO.append((cha.doctype,cha.name))
    cb=frappe.get_doc(dict(doctype='Vagabond Combo',ten='Combo hồi quy 290',ma_hang=cha.name,bat=1,
        kieu='Gia tron goi',gia_combo=1900000,dong=[dict(item_code=ma_goc,so_luong=1,gia_goc=1900000)]))
    cb.insert(ignore_permissions=True);nen._DA_TAO.append((cb.doctype,cb.name))
    # Mô phỏng bản ghi nháp tồn từ trước khi triển khai rã combo, chỉ fixture vừa tạo.
    hd.items[0].db_set('item_code',cha.name)
    hd.reload();hd.vgb_pt_thanh_toan='Tiền mặt'
    with patch.object(ban_hang,'_tu_xuat_hddt',side_effect=AssertionError('Ca ghi sổ không phát hành')):
        ket=ban_hang._ghi_so_mot_don(hd,cho_xuat=False)
    la('cửa ghi sổ thành công',ket,(1,0,''));hd.reload()
    la('đã rã mã gốc',[d.item_code for d in hd.items],[ma_goc])
    la('đã ghi sổ',hd.docstatus,1);dung('GL thật',bool(_gl(hd)))

@ca('#290 B1-3 lưu Sales chặn quà có tiền tay trước DB, bảng máy gỡ qua Document')
def sales_doi_qua():
    from vagabond import thanh_toan_nhieu as ttn
    for may in (0,1):
        hd=_hoa_don(False)
        hd.custom_nguon='Tại chỗ';hd.vgb_quay='TCV'
        hd.vgb_pt_thanh_toan='Tiền mặt';hd.vgb_pt_do_may=1
        hd.append(ttn.BANG,dict(pt='Tiền mặt',so_tien=hd.grand_total,do_may=may))
        hd.save(ignore_permissions=True);hd.reload()
        try: ban_hang.luu_thanh_toan(hd.name,pt='Hàng tặng')
        except frappe.ValidationError as e:
            dung('chỉ chặn dòng tay',not may)
            dung('hướng dẫn tiền tay','dòng thanh toán' in str(e))
        else: dung('dòng tay không được qua',bool(may))
        hd.reload()
        la('phương thức DB',hd.vgb_pt_thanh_toan,'Hàng tặng' if may else 'Tiền mặt')
        la('bảng tay giữ nguyên, máy gỡ',len(hd.get(ttn.BANG) or []),0 if may else 1)
        hd.save(ignore_permissions=True);hd.reload()  # Không để tờ kẹt ở lần lưu kế.

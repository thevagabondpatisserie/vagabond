"""Thư NCC không được bỏ email phụ hay biến chuỗi sai thành người nhận khác."""
from vagabond.khung.kiem_thu.nen import ca,la,dung
from vagabond import thu_ncc

@ca('NCC nhiều email: dấu chấm phẩy, xuống dòng, tên hiển thị và bỏ trùng')
def nhieu_email():
    la('đủ địa chỉ',thu_ncc.tach_email('Chính <A@example.com>;b@example.com\nc@example.com','a@example.com'),['a@example.com','b@example.com','c@example.com'])
    for sai in ['hong','a@','a@b']:
        try:thu_ncc.tach_email(sai)
        except ValueError:dung('chặn',True)
        else:dung('không bỏ qua địa chỉ sai',False)

@ca('UNC có mã hồ sơ, thứ tự; mã thư bền nhưng tách NCC với kế toán')
def nhan_tep():
    la('tên',thu_ncc.ten_unc('APP-2609-001',2,'old.PDF'),'UNC-APP-2609-001-2.PDF')
    la('bền',thu_ncc.ma_thu('APP1','ncc'),thu_ncc.ma_thu('APP1','ncc'))
    dung('hai thư',thu_ncc.ma_thu('APP1','ncc')!=thu_ncc.ma_thu('APP1','ke-toan'))

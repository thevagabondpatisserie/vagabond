# -*- coding: utf-8 -*-
"""Cac o Cai dat cu, nay do MA NGUON dung lai sau moi lan deploy.

Bay o dau sinh ra tu truoc 15/08/2026, hoi con bam tay tren Desk, va dang
chay that tren site. Muoi o sau thi TE HON: chung chua bao gio ton tai. Ma
nguon van ghi vao chung bang `set_single_value` - duong ghi nay khong soi
danh sach truong nen ghi luon vao bang Singles - roi doc lai bang `cfg()`,
duong doc thi CO soi, nen doc ra rong. Man Cai dat bao da luu, quay lai thay
trang, va khong mot dong loi nao. Ra soat ngay 03/09/2026 tim ra tam o dang
hong nhu vay: tai khoan nhan tien, mau in quay, danh sach may in, can tem,
nhip Pancake, hoa don dien tu quay, cau hinh KPI, tien do nhap khach.

Khai o day KHONG phai de tao moi ma de:

  - site thu, site moi, hay site vua khoi phuc tu ban sao deu co du o giong
    site that, khong con canh mot ben co mot ben khong ma khong ai hay;
  - doc ma nguon la biet vi sao co o do.

`create_custom_fields(update=True)` la thao tac lap lai duoc va chi dung vao
mo ta cua o, khong dung vao du lieu dang nam trong do. Kieu du lieu duoi day
chep dung theo o that tren site ngay 03/09/2026 - doi kieu la doi cach doc
so, nen ai sua phai doi chieu lai voi site truoc.
"""

# v568: MỌI ô dưới đây đều có insert_after. Ô không có neo thì Frappe đặt lên
# ĐẦU trang Cài đặt, đúng cái làm mười một ô mã nằm chình ình trên cùng. Năm ô
# tu_ghi_so_* trước nay chỉ có neo trên site (gán tay), nay ghi vào mã nguồn để
# site mới cũng ra đúng chỗ. Ca kiểm thu_cai_dat_568.py chạy lại phép xếp của Frappe.
TRUONG_MOI = {
	"Vagabond Settings": [
		{
			"fieldname": "vgb_hddt_xac_nhan_qua_han",
			"insert_after": "sec_du_lieu_goc",
			"label": "Xác nhận xử lý HĐĐT quá hạn",
			"fieldtype": "Long Text",
			"read_only": 1,
			"hidden": 1,
		},
		{
			"fieldname": "khoa_so_ngay",
			"insert_after": "sec_khoa_so",
			"label": "Khoá sổ trước bao nhiêu ngày",
			"fieldtype": "Int",
		},
		{
			"fieldname": "khoa_so_den",
			"insert_after": "khoa_so_ngay",
			"label": "Khoá sổ đến ngày",
			"fieldtype": "Date",
		},
		{
			"fieldname": "tu_ghi_so_bat",
			"insert_after": "tu_xuat_hddt",
			"label": "Tự ghi sổ cuối ngày",
			"fieldtype": "Check",
		},
		{
			"fieldname": "tu_ghi_so_gio",
			"insert_after": "tu_ghi_so_bat",
			"label": "Giờ chạy lượt ghi sổ cuối ngày",
			"fieldtype": "Data",
		},
		{
			"fieldname": "tu_ghi_so_quay",
			"insert_after": "tu_ghi_so_gio",
			"label": "Điểm bán được tự ghi sổ",
			"fieldtype": "Small Text",
		},
		{
			"fieldname": "tu_ghi_so_lan_cuoi",
			"insert_after": "tu_ghi_so_quay",
			"label": "Lượt ghi sổ cuối ngày chạy lần cuối",
			"fieldtype": "Data",
			"read_only": 1,
		},
		{
			"fieldname": "tu_ghi_so_nhat_ky",
			"insert_after": "tu_ghi_so_lan_cuoi",
			"label": "Nhật ký lượt ghi sổ cuối ngày",
			"fieldtype": "Small Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_diem_ban",
			"insert_after": "sec_du_lieu_goc",
			"label": "Danh sách điểm bán",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_pt_thanh_toan_ds",
			"insert_after": "sec_du_lieu_goc",
			"label": "Danh sách phương thức thanh toán",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_quyen_bo_mon",
			"insert_after": "sec_du_lieu_goc",
			"label": "Quyền bỏ món khỏi bill",
			"fieldtype": "Data",
		},
		{
			"fieldname": "vgb_mau_in_quay",
			"insert_after": "sec_du_lieu_goc",
			"label": "Mẫu in của quầy",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_may_in",
			"insert_after": "sec_du_lieu_goc",
			"label": "Danh sách máy in",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_can_tem",
			"insert_after": "sec_du_lieu_goc",
			"label": "Cân in tem",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_pancake_nhip",
			"insert_after": "sec_du_lieu_goc",
			"label": "Nhịp kéo đơn Pancake",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_hddt_quay",
			"insert_after": "sec_du_lieu_goc",
			"label": "Điểm bán tự xuất hoá đơn điện tử",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_kpi_cau_hinh",
			"insert_after": "sec_du_lieu_goc",
			"label": "Cấu hình KPI",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_kho_sap",
			"insert_after": "sec_du_lieu_goc",
			"label": "Ngưỡng kho: dung sai giao nhận, hạn dùng tối thiểu",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_nhap_khach_tien_do",
			"insert_after": "sec_du_lieu_goc",
			"label": "Tiến độ nhập danh sách khách",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
	],
}

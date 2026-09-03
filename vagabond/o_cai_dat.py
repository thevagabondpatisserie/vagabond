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

TRUONG_MOI = {
	"Vagabond Settings": [
		{
			"fieldname": "khoa_so_ngay",
			"label": "Khoá sổ trước bao nhiêu ngày",
			"fieldtype": "Int",
		},
		{
			"fieldname": "khoa_so_den",
			"label": "Khoá sổ đến ngày",
			"fieldtype": "Date",
		},
		{
			"fieldname": "tu_ghi_so_bat",
			"label": "Tự ghi sổ cuối ngày",
			"fieldtype": "Check",
		},
		{
			"fieldname": "tu_ghi_so_gio",
			"label": "Giờ chạy lượt ghi sổ cuối ngày",
			"fieldtype": "Data",
		},
		{
			"fieldname": "tu_ghi_so_quay",
			"label": "Điểm bán được tự ghi sổ",
			"fieldtype": "Small Text",
		},
		{
			"fieldname": "tu_ghi_so_lan_cuoi",
			"label": "Lượt ghi sổ cuối ngày chạy lần cuối",
			"fieldtype": "Data",
			"read_only": 1,
		},
		{
			"fieldname": "tu_ghi_so_nhat_ky",
			"label": "Nhật ký lượt ghi sổ cuối ngày",
			"fieldtype": "Small Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_diem_ban",
			"label": "Danh sách điểm bán",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_pt_thanh_toan_ds",
			"label": "Danh sách phương thức thanh toán",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_quyen_bo_mon",
			"label": "Quyền bỏ món khỏi bill",
			"fieldtype": "Data",
		},
		{
			"fieldname": "vgb_mau_in_quay",
			"label": "Mẫu in của quầy",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_may_in",
			"label": "Danh sách máy in",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_can_tem",
			"label": "Cân in tem",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_pancake_nhip",
			"label": "Nhịp kéo đơn Pancake",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_hddt_quay",
			"label": "Điểm bán tự xuất hoá đơn điện tử",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_kpi_cau_hinh",
			"label": "Cấu hình KPI",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_kho_sap",
			"label": "Ngưỡng kho: dung sai giao nhận, hạn dùng tối thiểu",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
		{
			"fieldname": "vgb_nhap_khach_tien_do",
			"label": "Tiến độ nhập danh sách khách",
			"fieldtype": "Long Text",
			"read_only": 1,
		},
	],
}

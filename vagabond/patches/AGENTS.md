# Luật riêng của bản vá

- Mỗi lần phát hành thêm đúng một dòng `vagabond.patches.dong_bo_cau_truc #vNNN` vào `vagabond/patches.txt`, khớp APPVER. Không có dòng mới thì Frappe Cloud chỉ "Pull", after_migrate không chạy.
- GIỮ mọi dòng đang có trên main, kể cả dòng của phiên khác. CI kiểm việc này (`cong_cu/chot_chan.py`).
- Bản vá riêng (tệp trong thư mục này) phải có ca bench gọi thật `execute()`. Bench cài mới không tự chạy thân bản vá: ngày 18/11 bản vá v674 làm ngã lượt cập nhật site mà bench vẫn xanh.
- Bản vá chạy giữa lượt cập nhật site: không `frappe.db.commit()` giữa chừng, không đọc Singles bằng `frappe.db.get_value("Singles", ...)` (lỗi ORDER BY creation); đọc `tabSingles` bằng SQL.
- Bản vá chỉ nâng dữ liệu còn giá trị cũ. Không sửa dữ liệu quá khứ đã ghi sổ.

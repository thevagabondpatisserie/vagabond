# Issue303: Gelatine Mass phantom

Anh Việt chốt Mass không quản tồn, backflush ra NVL thô. Issue304 phân cấp mã, issue305 thay thế tách riêng; không đưa vào PR302/v489.

Nền372b8d87, nhánh codex/303-gelatine-phantom, Codex local owner. Preflight PASS. Công cụ cong_cu/ra_phantom_303.py chỉ đọc mã cụ thể, Item/BOM/BOM Item/BOM Explosion Item/Bin, không cài API/hook/patch. Ba ca riêng đạt, chưa kiểm trên site.

Repo đã có patches/no_phantom_chuan.py dùng is_phantom_bom/is_phantom_item và dựng bảng nổ từ con lên cha. Không chạy lại patch toàn cục để sửa một mã. Không có stock không đủ chứng minh phantom đã trừ NVL đúng.

Mac khóa nên chưa đọc được mã/BOM/tỷ lệ hiện tại. Sau mở khóa: tìm cả Mass và Powder, xác nhận mã, chạy báo cáo chỉ đọc; giữ công thức nội bộ ngoài GitHub. Chốt danh sách cấu hình thực sự lệch, code sửa hẹp và ca Work Order insert/submit/reload/SLE/GL/huỷ/retry trên bench. Không sửa chứng từ đã ghi sổ hoặc tự tạo tỷ lệ.

Đây mới là công cụ chuẩn bị chẩn đoán; chưa sửa hoặc nghiệm thu Gelatine trên production. Không tăng phiên bản vì không thay app/runtime; không ghép vào v489.

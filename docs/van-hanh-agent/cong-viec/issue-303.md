# Issue303: Gelatine Mass phantom

Anh Việt chốt Mass không quản tồn, backflush ra NVL thô. Issue304 phân cấp mã, issue305 thay thế tách riêng; không đưa vào PR302/v489.

Nền372b8d87, nhánh codex/303-gelatine-phantom, Codex local owner. Preflight PASS. Công cụ cong_cu/ra_phantom_303.py chỉ đọc mã cụ thể, Item/BOM/BOM Item/BOM Explosion Item/Bin, không cài API/hook/patch. Ba ca riêng đạt, chưa kiểm trên site.

Repo đã có patches/no_phantom_chuan.py dùng is_phantom_bom/is_phantom_item và dựng bảng nổ từ con lên cha. Không chạy lại patch toàn cục để sửa một mã. Không có stock không đủ chứng minh phantom đã trừ NVL đúng.

Mac khóa nên chưa đọc được mã/BOM/tỷ lệ hiện tại. Sau mở khóa: tìm cả Mass và Powder, xác nhận mã, chạy báo cáo chỉ đọc; giữ công thức nội bộ ngoài GitHub. Chốt danh sách cấu hình thực sự lệch, code sửa hẹp và ca Work Order insert/submit/reload/SLE/GL/huỷ/retry trên bench. Không sửa chứng từ đã ghi sổ hoặc tự tạo tỷ lệ.

Đây mới là công cụ chuẩn bị chẩn đoán; chưa sửa hoặc nghiệm thu Gelatine trên production. Không tăng phiên bản vì không thay app/runtime; không ghép vào v489.

## Đối chiếu site và sửa review 13/09

Mac đã mở. Đọc System Console (không commit): Mass BTPB00059 is_stock_item=0; BOM hoạt động/mặc định is_phantom_bom=1, chặng BTP thành phần. Powder là mã NVL riêng. 34/34 dòng BOM cha đang hoạt động trỏ đúng công thức Mass và bật is_phantom_item, không chặn nổ. Bảng nổ của BOM đang hoạt động không còn lá Mass; Bin Mass khác0 rỗng. Tỷ lệ công thức đã đọc nhưng giữ nội bộ. Chưa có bằng chứng lỗi cấu hình hiện tại để đổi mã hoặc chạy patch toàn cục.

Sửa306-1/2/3: chuyển ba ca riêng vào cổng khung; thêm ca thứ4 chốt trạng thái BOM huỷ và BOM chỉ có trong bảng nổ. Đọc default_bom/custom_chang_btp; gắn trạng thái và dang_chay cho BOM/dòng cha/bảng nổ. Ghi rõ mã phải đúng hoa/thường.

Thêm hai ca bench fixture riêng, tỷ lệ minh hoạ không phải công thức tiệm: Work Order nổ một/nhiều cấp, hoàn tất hai phần, trừ đúng NVL và giá trị, Mass không có Bin/SLE, GL cân, huỷ trả tồn/sản lượng. Chưa chạy bench SHA mới; không nhận hai ca viết ra là đã đạt. Retry qua API hoàn tất và nghiệm thu thao tác Khải vẫn chưa phủ. Không sửa runtime, cấu hình hoặc chứng từ live.

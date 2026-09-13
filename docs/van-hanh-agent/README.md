# Tra cứu công việc cho Codex và Claude

Áp dụng cloud và local, theo Issue #294. Đây là quy trình lưu bàn giao, không
phải worker hay bằng chứng automation đã bật. Codex làm chính, Claude review.

## Đọc trước khi làm

1. Đọc AGENTS.md, instruction hiện hành và mục lục này. Claude đọc thêm
   CLAUDE.md. Không dựa vào ký ức của phiên trước để xác nhận trạng thái.
2. Đọc issue/PR và comment mới trực tiếp trên GitHub, xác minh branch/SHA,
   owner/phạm vi đang claim. Issue là nguồn trạng thái hiện hành; ghi chú
   trong git có thể cũ. Không sửa chồng người đang làm cùng phạm vi.
3. Tìm `cong-viec/issue-N.md`, rồi dùng rg tìm từ khóa trong docs và
   docs/bai-hoc-su-co.md. Chỉ mở nguồn liên quan, không nạp mọi nhật ký.
4. Fetch main và đúng nhánh PR. Thiếu remote/quyền/mạng phải ghi blocked;
   không nhận commit chỉ có ở runner là đã đẩy lên PR.

## Ghi trước khi kết thúc lượt có thay đổi thực chất

- Bản `cong-viec/issue-N.md` thay mẫu `vgb-control-tower/templates/handoff.md`
  cho bàn giao agent; control tower vẫn dùng cho claim/preflight/lock.
- Chỉ owner đang claim issue sửa bản bàn giao, trên nhánh PR đã claim.
  Bên khác gửi bổ sung bằng comment trên PR kèm SHA; owner gộp ở lượt sau.
- Một tệp ngắn cho mỗi issue theo mau-ban-giao.md, nằm trong PR của việc đó.
  Cập nhật tệp hiện có; không tạo tệp theo từng tin nhắn hay từng lần poll.
- Ghi nguyên nhân đã chứng minh, quyết định/phạm vi anh Việt duyệt, code đã
  làm, kiểm trên SHA nào, finding còn mở, owner và bước tiếp. Chưa kiểm phải
  ghi rõ. Bài học tái sử dụng đưa vào docs/bai-hoc-su-co.md, tránh chép trùng.
- Ghi SHA code đã kiểm. Nếu ghi chú được commit sau code, ghi rõ commit chỉ
  thay tài liệu; link CI cuối trên PR là bằng chứng cho SHA cuối, không đoán.
- Trên PR đăng link bàn giao và bằng chứng mới. Chỉ gọi Claude khi có phần
  cần review; không tag chỉ để báo đã cập nhật ghi chú. Không tạo commit rỗng
  hoặc commit tài liệu sau mỗi lượt không có thay đổi.
- Cloud không truy cập nhật ký trên Mac: bản repo là bàn giao dùng chung,
  không được nhận đã ghi nhật ký local. Phiên local ghi nhật ký máy theo
  instruction; không đồng bộ nguyên transcript vào repo.

## Mục lục

- [Issue 294: cloud và lưu bàn giao](cong-viec/issue-294.md)
- [Mẫu bàn giao](mau-ban-giao.md)
- [Luồng cloud cần nghiệm thu](luong-cloud.md)

Thêm một dòng mục lục khi có issue mới. Mỗi tệp công việc mục tiêu dưới 8 KB;
đây là quy ước, chưa có cổng máy giới hạn. Giữ kết luận cuối và các mốc còn
cần dùng; lịch sử git/Issue/PR giữ diễn biến, không nhân bản mọi comment.

## Dung lượng và dữ liệu

Không đưa transcript, dump DB, cache, log dài, ảnh/base64 hay secret vào git.
Log thử dùng Actions artifact có hạn giữ; ghi run ID, SHA và kết luận tối
thiểu vào PR để vẫn hiểu khi artifact hết hạn. Tệp nghiệp vụ cần giữ dài
hạn đặt ở Drive được phân quyền theo yêu cầu, không tự chia sẻ công khai.

Mốc main 948952b: 47 tệp Markdown, 356000 byte tổng nội dung hiện tại, không
phải kích thước toàn lịch sử git hoặc hạn mức GitHub. Ví dụ 1000 bản ghi 8 KB
là khoảng 8 MB nội dung, chưa tính lịch sử. Chưa cần VPS riêng cho ghi chú.
Xóa tệp ở commit mới không xóa dung lượng khỏi lịch sử git; tránh đưa tệp
lớn vào từ đầu. Không tự rewrite lịch sử hoặc xóa bằng chứng để giảm dung lượng.

Đọc chọn lọc giảm token; ghi Markdown không tự huấn luyện lại model. Hiệu
quả phụ thuộc lượt sau thực sự đọc, xác minh và dùng bài học đúng phạm vi.

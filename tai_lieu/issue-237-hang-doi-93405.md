# Bàn giao #237: đơn 93405 bị hàng quá hạn giữ lại

## Trạng thái

- Code: Codex, nhánh `codex/237-doi-ngay-93405` trên main `4e95e2a`/v457.
- Đề xuất v459. PR243 đang đề xuất v458 riêng cho thuế; không chứa code
  thuế trong nhánh này. Claude chốt lại phiên bản/thứ tự khi tích hợp.
- Claude review, bench, merge và deploy theo phân công anh Việt.
- Không sửa trạng thái đơn quá hạn hoặc đơn 93405 trên site từ Codex.

## Bằng chứng và nguyên nhân

Issue #237 comment 5587152431: nguồn 93405 đã ra khỏi ngày 08/09, ngày
nguồn không khai múi `2026-09-09T17:00:00` được đọc đúng ra 10/09 tại VN.
Có 1.325 vận đơn quá hạn và 11 vận đơn đúng ngày, nhưng bản cũ gộp cả
hai nhóm, xếp theo ID và chỉ thử 20 đơn mỗi lượt. Cursor mang ngày nên
qua nửa đêm lại về đầu. Không cần sửa ID hay phép đọc ngày.

Lưu ý về bằng chứng `modified`: code có `db.set_value(...,
update_modified=False)`. Vì vậy `modified == creation` không tự chứng
minh chưa đọc/chưa cập nhật; vị trí cursor suy từ modified cũng chỉ là
ước lượng. Bản sửa ghi số/cursor thực của mỗi lượt vào Nhật ký đồng bộ.

## Bản sửa

- Đúng ngày đang xem được truy vấn và đọc trước. Quá hạn là truy vấn
  `< hôm nay` riêng, chỉ chạy kèm lượt hôm nay.
- Khi cả hai còn việc, dành sức chứa 16 request/12 giây cho ngày xem,
  4 request và phần thời gian riêng cho quá hạn. Phần ngày không dùng
  hết nhường cho quá hạn, tối đa 20 request bổ sung/lượt.
- Timeout từng request giảm theo thời gian còn lại. Nếu HTTP vượt ngân
  sách mềm, quá hạn vẫn được dành 3 giây để thử tiếp. Không hứa thời gian
  cứng 15 giây cho toàn giao dịch hoặc bảo đảm 4 request khi mạng chậm.
- Cursor quá hạn theo shop, không mang ngày, không TTL. Cursor ngày xem
  riêng, TTL 30 ngày. Redis bị xoá/evict vẫn có thể làm mất cursor; sự cố
  đó không đưa đơn hôm nay xuống sau backlog nữa.
- Lỗi ID vẫn tiến lượt, báo lỗi rõ, giữ dữ liệu. Đơn sẽ được thử lại khi
  quay vòng. Không tự huỷ/đánh dấu đã giao đơn quá hạn.
- UI tách số chưa tới lượt của ngày xem/quá hạn với lỗi thật. Số liệu là
  của từng lượt, không phải tiến độ hoàn tất cả vòng. Nhật ký đồng bộ
  ghi số đã thử/đọc được/lỗi/chưa kiểm và cursor trước/sau cho cả cron
  lẫn nút tay. Error Log tiếp tục nhận lỗi thật của cron.
- Giữ khoá file dùng chung nút tay/cron, savepoint từng đơn và rollback
  toàn lượt khi có lỗi ngoài. Không thêm API hay thay quyền.

## Kiểm local

- Cổng `sh kiem_truoc_deploy.sh` và bundle `--kiem` phải RC0.
- Tái hiện chạy chính hàm main v457: 1.325 ID cũ + 11 ID ngày xem,
  lượt đầu đọc 20 ID cũ, không có 93405. Cùng dữ liệu trên bản sửa:
  93405 đầu tiên, đọc đủ 11 ID ngày xem, 9 ID quá hạn, vẫn 20 request.
- Ca thuần: 1.336 đơn; chuyển nửa đêm với lỗi 404 vẫn đi tiếp; hai hàng
  đông đều tiến; ID nhỏ mới thêm được đọc khi quay vòng; mạng chậm vẫn
  dành lượt cho hai nhóm; xem ngày khác không đổi cursor quá hạn.
- Ca JS chạy helper thật để kiểm thông báo chưa tới lượt/lỗi riêng.

## Bench và nghiệm thu còn phải chạy

Ca mới `_hang_doi_ngay_that` trong `thu_dong_bo_237.py` dựng 25 vận đơn
quá hạn và 1 vận đơn ngày xem thật trong savepoint, chặn mọi HTTP bằng
stub, giới hạn truy vấn trong danh sách fixture. Đọc nguồn ngày mới,
lưu/reload thật rồi gọi chính API `danh_sach`: mất ở ngày cũ, hiện ở ngày
mới; chỉ một vận đơn theo ID; 25 đơn cũ không bị tự đóng. Các ca #237 cũ
vẫn phải chạy, đặc biệt rollback món/ngày, nối SI và huỷ nguồn.

Codex chưa chạy bench. Claude cần:

1. Chạy cổng và toàn bộ ca tích hợp #237 trên bench, giữ rollback/cấm
   commit/cấm gửi ngoài. Hai khoá chứng từ còn sót và số lượng lệch rỗng.
2. Kiểm nút tay cùng cron bằng hai phiên: khoá vẫn chặn chạy chồng;
   quay ngày không đặt lại cursor quá hạn. Đối chiếu nhật ký với request.
3. Sau review/bench đạt, merge và deploy theo phân công. Fetch main,
   kiểm APPVER/patch để không đè PR243. Đây là Python/JS, không có Server
   Script mới cần đồng bộ. Migrate phải có mốc v459 (hoặc số mới đã chốt).
4. Nghiệm thu riêng 93405 sau phát hành: nguồn vẫn 10/09 thì vận đơn
   phải mất khỏi 08/09 và có đúng một ở 10/09 sau lượt đồng bộ hữu hạn.
   Không sửa ngày tay để làm ca xanh. Kiểm các đường #237 khác trên màn.

1.325 đơn cũ cần một đợt đối chiếu trạng thái riêng nếu muốn dọn nghiệp
vụ. Tuổi đơn không đủ căn cứ tự huỷ/đã giao; đó không phải điều kiện để
bản sửa hàng đợi ưu tiên được đơn của Sales.

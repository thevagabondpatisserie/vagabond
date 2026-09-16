# Issue339 - trả lại APP có hóa đơn mua sẵn

Owner Codex Desktop, branch codex/fix-app059. Production incident ưu tiên.

Lỗi: APP NCC chọn PI đã ghi sổ; khi PI hủy/sửa sau đó, duyệt bị chặn đúng nhưng Từ chối cũng bị chặn bởi helper coi mọi PI có sẵn là PI do APP sinh. Không sửa bằng bỏ kiểm docstatus hay hủy các PI khác.

Sửa: chỉ giữ chặn PI của luồng Hoan ung (bảo thủ cho dữ liệu cũ) hoặc có dấu nguồn remarks đúng APP do máy sinh. Hoan ung HD/NCC có PI độc lập trả lại được. Đọc DB lỗi không được bỏ qua. Document validate dùng cùng guard cho Desk/API. Chưa thay toàn bộ thiết kế provenance; remarks có thể được quản trị sửa nên không coi là chứng cứ bất biến chống mọi chỉnh sửa đặc quyền.

Kiểm: local3072/0, Node gate đạt. Hai ca mới gọi API thật trên mock, baseline main fail cả2, bản mới pass. Bench mới: API trả/hủy giữ GL, PI hủy sau lập rồi amend/chọn lại/duyệt, nguồn sinh chặn API và Document. Chờ CI đúng SHA trước phát hành. Chưa claim Claude review, chưa merge/deploy.

Dữ liệu sự cố cụ thể được anh duyệt sửa riêng, dùng Document.save và Comment, đã đọc lại; không đưa chứng từ thật vào repo. Các PI/sổ cái không thay đổi trong xử lý APP.

## Vòng 2 và nền tích hợp
Native Codex P1: xóa link PI cùng lúc đổi terminal state lách guard incoming. Đã sửa kiểm cả get_doc_before_save, thêm mock + bench xóa link và đổi loại. Testmock3cađạt; combined predeploy gateđạt. Gộp PR338 head0d8a4098 (đã chứa337513d), dànhv504, giữ đủ502/503/504. Conflict chỉdocsappend/APPVER/patch vàbundle, không conflictlogic. Chưa coi PR337/338 đãmerge hayrelease.
Claude run35087522672 thất bại error_max_turns20,7permissiondenials, không có kết luận; không nhận reviewClaudeđạt. Bench SHA mới còn chờ; phải kiểm final integration trướcmerge/deploy.

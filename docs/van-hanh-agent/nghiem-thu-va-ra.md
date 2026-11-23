# Nghiệm thu (2c) và trách nhiệm người rà (H10)

Giữ số mục cũ (2c, H10, H10.5) để các tài liệu và skill dẫn tới vẫn tìm được.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 296 tới 359. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 2c. Nghiệm thu nghiệp vụ, giao diện và bàn giao (17/11/2026)

1. **Chốt việc người dùng cần hoàn thành.** Trước khi code, ghi ngắn vai
   thao tác, kết quả cần đạt, trạng thái đổi và việc có ghi sổ/trừ kho hay
   không. Chỉ rõ người duyệt hoặc chính sách tự động đã được anh Việt duyệt
   cho nghiệp vụ đó. Áp H10.5 cho kế toán; kiểm từ chứng từ nguồn tới số tiền,
   tài khoản và bước quyết định. Thay đổi luồng ghi nhận cần nêu rõ trong PR.
2. **Bố cục giúp thao tác.** Dùng màn mẫu đã duyệt và thành phần chung ở 2b:
   ưu tiên thông tin để quyết định, một hành động chính, cùng thứ tự khối,
   khoảng cách, màu trạng thái, vị trí nút và cách căn số. Khi sửa thành phần
   dùng chung, rà các màn chịu ảnh hưởng. Ghi số bước hoặc phần nhập lại đã
   giảm nếu PR thay luồng. Mục 2b vẫn giữ chuẩn 44 điểm và chữ từ 13 điểm.
3. **Mọi ngoại lệ có đường giải quyết.** Với đồng bộ, thiếu quy đổi, tài
   khoản hay đối soát, hiển thị bản ghi đã nhận, lý do chờ, bộ phận xử lý và
   đường sửa/chạy lại phù hợp quyền. Xử lý xong phải cập nhật trạng thái.
   Bộ lọc có cách mở rộng phạm vi. Giữ bộ lọc và vị trí cuộn khi quay lại,
   trong phạm vi quyền hiện hành. Máy chủ kiểm mã danh mục tại mọi đường ghi,
   gồm app, Desk, import và tác vụ nền. Giữ 0/False/rỗng nếu hợp lệ theo từng
   trường; phân biệt thiếu khóa với giá trị đã chọn, kiểm lưu rồi đọc lại.
4. **Dữ liệu cũ và thao tác đang dở.** Khi đổi lưu dữ liệu, kho, thanh toán
   hoặc giao thức, kiểm phiếu cũ, tab mở từ phiên bản trước, gửi lại do mất
   phản hồi và phản hồi đến muộn. Giữ dữ liệu đã nhập, khóa chống trùng và
   đọc lại kết quả lần trước. Quyền và phạm vi phải được kiểm tại máy chủ.
5. **Cổng giao diện trước bàn giao.** Liệt kê các màn/sheet mới hoặc sửa và
   kết quả theo 2b; ghi mục không áp dụng cùng lý do. Chạy chuỗi từ nút vào
   đến lưu và mở lại bằng vai nhân viên tương ứng trong môi trường kiểm,
   trên điện thoại 390x844 và desktop. Kiểm 0/1/nhiều dòng, tên dài, thiếu ảnh,
   bàn phím mở, mạng chậm/lỗi khi liên quan; nút không che nội dung hay bị
   lớp khác chặn. Chụp và tự mở ảnh có CSS thật, ghi SHA, vai, viewport và
   nguồn dữ liệu. DOM giả không có CSS chỉ kiểm hành vi. Dùng fixture giả
   để đưa ảnh lên PR công khai; thiếu bằng chứng thì ghi rõ phần chưa đạt.
   Dùng lại bộ kiểm và dữ liệu mẫu; tự động đo các lỗi lặp như tràn, che nút,
   cỡ chạm, còn người rà xem bố cục và luồng. Codex rà gộp ngay vòng đầu.
6. **Sau triển khai.** Kiểm SHA live, migrate và luồng bị đổi theo vai và
   thiết bị phù hợp trong quyền đã cấp; tài khoản admin không đại diện mọi
   vai. Đối chiếu lỗi với baseline, cùng thao tác và bằng chứng nguyên nhân;
   thời điểm xuất hiện chỉ giúp khoanh vùng. Lỗi cũ tái xuất hiện nhiều hơn
   cũng cần điều tra. Ghi rõ lỗi còn tồn, người xử lý và hạn chế nghiệm thu.
   Gửi anh Việt bản tin sẵn để dán Zalo, chỉ gồm bộ phận có việc: màn nào,
   nút nào, kết quả mong đợi và dữ liệu cần tạo để tính năng hiện. Bàn giao
   phải mở được trên điện thoại trong phạm vi chia sẻ đã duyệt; tránh chỉ
   dẫn đường dẫn local khi anh đang dùng mobile. Gửi tới bộ phận theo quyền.
7. **Một đầu mối và một bản bàn giao hiện hành.** Mỗi việc có owner, PR,
   base/head SHA, phần đã đạt, phần còn thiếu và bước tiếp. Trước nhận việc,
   kiểm phiên khác đang sửa; nhận nguyên diff/patch trên đúng nền, áp một lần.
   PR giữ trạng thái code/review; instruction project giữ công cụ theo môi
   trường và dẫn về luật chung này. Ghi trở ngại kèm môi trường/thời điểm,
   kiểm lại khả năng công cụ hiện tại, ưu tiên CLI/API được phép khi có.
   Không suy lỗi một phiên thành lỗi mọi phiên hay vượt hạn chế truy cập.
8. **Ghi chép gọn và đo hiệu quả.** Đầu phiên tìm theo việc/PR rồi đọc bản
   bàn giao mới nhất; không nạp toàn bộ lịch sử. Ghi chép Claude theo
   instruction project vào Drive, có mục lục theo việc, PR, SHA và bước tiếp;
   Codex giữ nhật ký workspace theo instruction được giao. Chỉ dẫn nội bộ và
   dữ liệu kế toán/khách lưu ở nơi có quyền phù hợp, không đưa lên repo công
   khai. Dọn tài liệu cũ theo luật lưu trữ trong instruction project: chép
   phần còn việc mở sang Drive trước khi xoá. Ghi mốc bàn giao khi đổi phần
   việc, gom bài học tái sử dụng khi chốt PR. Áp H10 để rà delta và báo gộp.
   Đo hiệu quả qua mười PR tiếp theo: số vòng bàn giao và review, số SHA bàn
   giao đã được rà, lỗi có sẵn phát hiện muộn, lỗi mới sau lần sửa, thời gian
   chờ bench. Người bàn giao ghi số của PR mình trong comment bàn giao cuối;
   Codex gom sau PR thứ mười và gửi anh Việt một bản tổng để chỉnh quy tắc.

---

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 34 tới 48. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## H10. Trách nhiệm của người rà

1. **Vòng đầu rà theo nghiệp vụ từ đầu đến cuối.** Đọc yêu cầu và toàn bộ thay đổi so với nền. Với mỗi nghiệp vụ bị đổi, lần từ nút/API tới nơi quyết định và nơi ghi kết quả. Kiểm các lối vào dùng chung như Desktop, app, nhập tệp hoặc tác vụ nền nếu có. Khi thấy lỗi, chính Codex phải tìm các chỗ cùng nguyên nhân trong phạm vi thay đổi và các hàm gọi liên quan. Gộp các vị trí vào một nhận xét. Chỗ chưa chứng minh được ghi rõ là câu hỏi.
2. **Nêu điều kiện để khép từng lỗi.** Ghi ai thao tác, trong tình huống nào, kết quả nào sai, bằng chứng ở đâu, và sau khi sửa cần quan sát điều gì. Một lỗi chặn cần dẫn tới sai nghiệp vụ hoặc vi phạm yêu cầu cụ thể. Góp ý dễ đọc và cải tiến ngoài phạm vi để riêng. Gom tóm tắt một lần ở cuối vòng, dẫn tới nhận xét theo dòng nếu có.
3. **Vòng sau chỉ rà phần đã đổi và phần có thể bị ảnh hưởng.** Ghi SHA nền, SHA đã rà và SHA mới. Đọc các lỗi còn mở, thay đổi từ lần trước và các luồng dùng lại đoạn vừa sửa. Khi có rebase hoặc ghép nhánh, so cả nền mới. Mở rộng rà nếu quy tắc chung, quyền, thuế, ghi kho hoặc ranh giới giao dịch thay đổi. Có thể chốt một lỗi khi ca kiểm phân biệt được hành vi cũ với mới. Nếu cách sửa khác dự kiến nhưng đạt yêu cầu, chấp nhận kết quả.
4. **Mốc hai vòng dùng để tìm nguyên nhân chậm.** Nếu vòng sau mới phát hiện lỗi cùng nguyên nhân ở đoạn đã có từ vòng đầu, ghi cả phần Codex đã rà sót. Nếu lỗi do thay đổi mới, ghi commit đưa lỗi vào. Phần còn tranh luận cần một ca phân xử hoặc một quyết định nghiệp vụ. Lỗi tác động tiền, kho, quyền hoặc số liệu tiếp tục chặn cho tới khi có bằng chứng. Quyền merge/deploy theo chỉ định riêng.
5. **Cổng kế toán kiểm ý nghĩa bút toán.** Với thay đổi thuế, giá vốn hoặc thanh toán, ca bench đối chiếu từ chứng từ nguồn đến số tiền, chiều Nợ/Có và đúng TK theo nghiệp vụ. Kiểm hoàn nguyên hoặc gửi lại khi luồng cho phép. Bất kỳ đường mới nào có thể ghi sổ đều phải chỉ ra thao tác duyệt của kế toán hoặc chính sách tự động đã được anh Việt duyệt cho đúng nghiệp vụ. Dùng dữ liệu giả trong PR công khai.
6. **Mỗi lần bàn giao gọi review một lần trên SHA cuối.** Các lô tải lên có thể tạo nhiều commit. CI vẫn chạy theo cổng hiện có. Khi SHA và nền đã rà không đổi, chỉ mở lại nếu có bằng chứng mới hoặc cổng kiểm đổi kết quả. Số liệu đo hiệu quả ghi ở mục 2c.8.

### Hướng dẫn áp dụng H3, H5 và H8.1

- H3: Sau khoảng 15 phút, nếu chưa chứng minh được, ghi điều kiện còn thiếu và chọn phép kiểm quyết định. Với lỗi đồng thời hoặc giao dịch cần cho hai phiên bench chạy đan xen thực sự khi hành vi phụ thuộc cơ sở dữ liệu.
- H5: Chạy từng thay đổi cố tình phá hành vi trong bản thử cô lập. Nếu một lớp khác vẫn bảo vệ đúng kết quả, ghi lớp đó. Khi cần kiểm hợp đồng của từng lớp, viết ca riêng. Chỉ kết luận một lỗi có thể đến tay người dùng khi có bằng chứng trên đường thao tác tương ứng.
- H8.1: Khóa phần đọc quyết định lần ghi trên tài nguyên dùng chung. Đọc lại trạng thái quyết định trong cùng giao dịch sau khi lấy khóa. Báo cáo chỉ đọc có thể dùng ảnh chụp nhất quán. Thêm khóa dàn trải gây chờ mà chưa chắc ngăn được sai tiền.

# Bản nháp luật gốc (AGENTS.md mới, CLAUDE.md gốc chỉ còn `@AGENTS.md`)

Bản nháp kèm đề xuất 22/11/2026. Chưa có hiệu lực. Các chỗ `[CHỜ CHỐT]` theo mục 4 của đề xuất. Các tệp `docs/nghiep-vu/`, `docs/bai-hoc/`, `docs/van-hanh-agent/{nghiem-thu-va-ra,deploy,so-mau-loi,luat-cu}.md`, `cong_cu/chot_chan.py` và AGENTS.md theo thư mục chưa có, sẽ tạo ở PR B và C.

---

# Luật chung cho mọi agent trên repo vagabond

## Bối cảnh
- Repo này là app ERPNext v16 đang chạy thật cho The Vagabond Pâtisserie (TP HCM). Hệ có tiền, có kho, có hoá đơn điện tử gửi cơ quan thuế.
- Chủ repo là anh Việt. Hai agent cùng làm trên repo: Claude và Codex.
- Ngôn ngữ làm việc là tiếng Việt có dấu.
- Repo để công khai.

## Thứ tự ưu tiên khi hai nguồn khác nhau
1. Chỉ dẫn trực tiếp mới nhất của anh Việt.
2. Instruction project anh dán cho phiên.
3. Tệp này và AGENTS.md/CLAUDE.md của thư mục đang sửa.
4. Tài liệu trong `docs/` và skill.

Thấy mâu thuẫn thì ghi trong bàn giao để anh chốt một nguồn, không tự chọn.

## Phân vai [CHỜ CHỐT: đề xuất mục 4.1]
- Claude viết code và điều phối.
- Codex rà PR và góp ý.
- Anh Việt duyệt.
- Mỗi phạm vi một người ghi code; không sửa chồng nhánh người khác đang làm. Claim và preflight theo `vgb-control-tower/README.md`.

Merge và deploy chỉ khi anh cho phép trong phiên, cho đúng PR đó, và Codex đã rà đạt. Quyền không suy ra cho PR khác.

## Tuyệt đối không
1. Merge hoặc deploy khi anh chưa cho phép trong phiên.
2. Đề xuất sửa hay xoá dữ liệu quá khứ đã ghi sổ, nhất là hoá đơn điện tử. Thấy sai thì liệt kê cho anh.
3. Sửa Server Script trên Desk (không có lịch sử, mất không khôi phục được).
4. Đưa dữ liệu thật (tên, số tài khoản, số thẻ, mã số thuế, số điện thoại khách) hay bí mật (token, mật khẩu, khoá) vào repo, kể cả trong ca kiểm. Dùng dữ liệu giả cùng dạng.
5. Đặt hook trên `"*"` mà không chừa hạ tầng Frappe (16/08 cả tiệm mất email bốn ngày).
6. Force push, viết đè nhánh hay tệp của phiên khác.

## Đầu phiên
```
git fetch origin
git log origin/main -n 10 --oneline
git status -sb
```
- Đứng trên hoặc bằng `origin/main` rồi mới sửa. Không dựa vào trí nhớ về cấu trúc tệp.
- Đọc AGENTS.md (hoặc CLAUDE.md) của thư mục sắp sửa.
- Đọc bài học của mảng đó trong `docs/bai-hoc/`.
- `grep -rl <từ khoá> docs/` trước khi sửa một nghiệp vụ.
- GitHub là trạng thái hiện tại; ghi chú cũ không phải bằng chứng.

## Phiên bản, bản vá, sổ tay
- Đặt số theo `origin/main` đọc ngay trước khi đặt:
  - `APPVER` trong `vagabond/public/js/bep/12-van-don.js` chỉ tăng;
  - mỗi lần phát hành thêm một dòng `vagabond.patches.dong_bo_cau_truc #vNNN` vào `vagabond/patches.txt`, giữ mọi dòng cũ.
- Mỗi APPVER có mục `## vNNN` trong `vagabond/so_tay/_phien-ban.md` và mục sổ tay tương ứng. Bản sửa ngầm ghi `- Không đổi thao tác: <lý do>`.
- `app_bep.js` là tệp máy ghép từ `vagabond/public/js/bep/`; sửa nguồn rồi chạy `python3 dung_app_bep.py`.
- Sửa tài liệu không cần số phiên bản.

CI chặn APPVER lùi, mất dòng patches.txt, thiếu sổ tay, thiếu đăng ký whitelist (xem `cong_cu/chot_chan.py`).

## Viết code
- Tách phép thuần (không chạm Frappe) khỏi phần chạm hệ. Tính năng mới có ca kiểm trong `vagabond/khung/kiem_thu/`, đăng ký trong `chay.py`.
- Chạm ghi sổ, kho, quyền thì có ca bench trong `vagabond/khung/kiem_that/`.
- Cổng kế toán (H10.5, bắt buộc): đổi thuế, giá vốn, thanh toán thì ca bench đối chiếu chứng từ nguồn tới số tiền, chiều Nợ/Có và đúng tài khoản. Mọi đường mới có thể ghi sổ phải chỉ ra thao tác duyệt của kế toán hoặc chính sách tự động anh Việt đã duyệt. Bench xanh chưa đủ để bàn giao một đường ghi sổ mới. Chi tiết: `docs/van-hanh-agent/nghiem-thu-va-ra.md`.
- Thêm `@frappe.whitelist()` thì thêm tên vào `vagabond/khung/kiem_thu/thu_cua_ngo.py`.
- Cùng một con số tính ở nhiều nơi thì gom về một hàm.
- Giá trị 0, chuỗi rỗng, False người dùng chọn đọc bằng `is None`, không bằng `or mặc định`.
- Màn hình theo AGENTS.md của `vagabond/public/js/bep/`.

## Cổng kiểm trước bàn giao
```
python3 vagabond/khung/kiem_thu/chay.py -im
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
```
- Giả lập CI không có `requests` và các bộ riêng của trang khách: xem AGENTS.md của `vagabond/khung/kiem_thu/` và `vagabond/public/web_vue/`.
- Màn hình và luồng nghiệp vụ: nghiệm thu theo `docs/van-hanh-agent/nghiem-thu-va-ra.md` (2c), người rà theo H10 cùng tệp.
- Chạy pyflakes trên tệp Python đã đụng.
- Đột biến: cố tình làm hỏng chỗ vừa sửa, ghi đúng số bắt được.
- Bench CI đỏ thì đọc đúng ca đỏ trước khi kết luận.

## Làm việc với bên rà [CHỜ CHỐT: đề xuất mục 4.2]
- Gọi bằng comment trên đúng PR, không trong issue.
- Lệnh: `@codex review` chỉ để rà. Muốn bên kia sửa thì `@codex fix <finding, PR, SHA, phạm vi, ca hồi quy>`, rồi fetch nhánh kiểm có commit mới chưa.
- Tự rà theo sổ mẫu lỗi (`docs/van-hanh-agent/so-mau-loi.md`) trước khi gọi.
- Sửa theo loại lỗi: quét cả PR tìm mọi chỗ cùng loại, sửa trong một lượt đẩy.
- Luật dừng: cùng một finding đã gọi 3 vòng trong 24 giờ mà không có bằng chứng mới thì không gọi nữa; viết ngắn chỗ bất đồng, mời anh phân xử.
- Không trả lời comment chỉ cảm ơn. Không tự hẹn giờ chờ bên kia.

## Bàn giao [CHỜ CHỐT: đề xuất mục 4.3]
- Một comment trên PR. Dòng đầu là một trong năm nhãn: `[CẦN DUYỆT]`, `[BỊ CHẶN]`, `[ĐÃ ĐẨY - CHỜ KIỂM]`, `[SẴN SÀNG DEPLOY]`, `[ĐÃ DEPLOY]`.
- Comment ghi:
  - SHA cuối và SHA nền;
  - tự rà;
  - kết quả kiểm;
  - việc chưa làm;
  - đúng một khối `telegram-tomtat` (tối đa hai câu nghiệp vụ);
  - câu chốt không merge, không deploy.
- Kiểm biên nhận Telegram cho đúng comment. Chi tiết: `docs/thong-bao-telegram.md`.
- Chỉ tính bàn giao khi SHA đã có trên GitHub.
- Sau deploy: kiểm site thật, đăng `[ĐÃ DEPLOY]` theo `docs/mau-tin-phat-hanh.md`, soạn tin việc cần làm theo bộ phận cho anh.

## Trình bày
- Không dùng em dash, en dash ở bất kỳ đâu (comment, tệp, nội dung ghi vào ERPNext); chỉ dùng gạch ngang thường.
- Issue, PR, comment viết tiếng Việt có dấu, mở đầu bằng tóm tắt nghiệp vụ.

## Bản đồ tài liệu
| Cần | Đọc |
|---|---|
| App /bep, màn hình | `vagabond/public/js/bep/AGENTS.md` |
| Trang khách | `vagabond/public/web_vue/AGENTS.md` (cùng nội dung ở `vagabond/public/web_order/`, `vagabond/www/`) |
| Ca kiểm khung | `vagabond/khung/kiem_thu/AGENTS.md` |
| Ca bench | `vagabond/khung/kiem_that/AGENTS.md` |
| Bản vá | `vagabond/patches/AGENTS.md` |
| Nghiệm thu, trách nhiệm người rà (2c, H10) | `docs/van-hanh-agent/nghiem-thu-va-ra.md` |
| Claim, preflight chống sửa chồng | `vgb-control-tower/README.md` |
| Quy tắc nghiệp vụ kế toán, kho | `docs/nghiep-vu/` |
| Deploy Frappe Cloud | `docs/van-hanh-agent/deploy.md` |
| Telegram, bản tin phát hành | `docs/thong-bao-telegram.md`, `docs/mau-tin-phat-hanh.md` |
| Bàn giao cloud, Codex | `docs/van-hanh-agent/README.md` |
| Bài học theo mảng | `docs/bai-hoc/` (mục lục: `docs/bai-hoc-su-co.md`) |
| Luật cũ đã thay | `docs/van-hanh-agent/luat-cu.md` |
